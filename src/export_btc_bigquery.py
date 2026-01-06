#!/usr/bin/env python3
"""
Bitcoin Blockchain Export von Google BigQuery (Sandbox-kompatibel!)

Nutzt die SEPARATEN Tabellen (blocks, transactions, inputs, outputs) statt
der nested arrays - das spart Bytes und funktioniert im kostenlosen Sandbox!

Exportiert im bitcoin-etl Format:

blockchain_exports/
└── YYYY-MM-DD_YYYY-MM-DD/
    ├── blocks/
    │   └── date=YYYY-MM-DD/
    │       └── blocks_00000.json
    ├── transactions/
    │   └── date=YYYY-MM-DD/
    │       └── transactions_00000.json
    ├── inputs/
    │   └── date=YYYY-MM-DD/
    │       └── inputs_00000.json
    └── outputs/
        └── date=YYYY-MM-DD/
            └── outputs_00000.json

Verwendung:
    python src/export_btc_bigquery.py --start-date 2024-01-15 --end-date 2024-01-15
    python src/export_btc_bigquery.py --start-date 2024-01-01 --end-date 2024-01-07
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from google.cloud import bigquery
from tqdm import tqdm


def format_bytes(size: int) -> str:
    """Formatiert Bytes in lesbares Format (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(seconds: float) -> str:
    """Formatiert Sekunden in lesbares Format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


class BigQueryEncoder(json.JSONEncoder):
    """Custom JSON Encoder für BigQuery-Datentypen."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        if isinstance(obj, bytes):
            return obj.hex()
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, 'items'):
            return dict(obj)
        return super().default(obj)


def get_date_range(start_date: str, end_date: str) -> list[str]:
    """Generiert Liste von Datumsstrings zwischen start und end (inklusiv)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def row_to_dict(row, table_name: str = "transactions") -> dict:
    """Konvertiert BigQuery Row zu dict im bitcoin-etl Format.

    Wichtig: block_timestamp wird zu Unix Timestamp (Long) konvertiert,
    damit es mit dem ETL-Schema kompatibel ist (erwartet LongType).
    """
    from decimal import Decimal

    # Felder die zu Unix Timestamp konvertiert werden sollen
    timestamp_fields = {"block_timestamp", "timestamp"}
    # Felder die wir nicht brauchen (BigQuery Partition-Spalten)
    skip_fields = {"block_timestamp_month", "timestamp_month"}

    result = {}
    for key, value in row.items():
        # Partition-Spalten überspringen
        if key in skip_fields:
            continue

        if value is None:
            result[key] = None
        elif key in timestamp_fields and hasattr(value, 'timestamp'):
            # Datetime zu Unix Timestamp (Sekunden seit 1970)
            result[key] = int(value.timestamp())
        elif hasattr(value, 'isoformat'):
            # Andere Datetime-Felder als ISO String
            result[key] = value.isoformat()
        elif isinstance(value, bytes):
            result[key] = value.hex()
        elif isinstance(value, Decimal):
            result[key] = int(value)  # Satoshi sind immer ganze Zahlen
        elif isinstance(value, list):
            # Nested arrays (inputs, outputs) rekursiv verarbeiten
            result[key] = [
                row_to_dict(item, table_name) if hasattr(item, 'items') else item
                for item in value
            ]
        elif hasattr(value, 'items'):
            # Nested structs rekursiv verarbeiten
            result[key] = row_to_dict(value, table_name)
        else:
            result[key] = value
    return result


def export_table_for_date(
    client: bigquery.Client,
    table_name: str,
    target_date: str,
    output_dir: Path,
    date_column: str,
    verbose: bool = True
) -> tuple[int, int]:
    """Exportiert eine Tabelle für ein spezifisches Datum.

    Returns:
        Tuple von (row_count, file_size_bytes)
    """

    table_dir = output_dir / f"{table_name}/date={target_date}"
    table_dir.mkdir(parents=True, exist_ok=True)

    # Berechne den Monatsanfang für die Partition
    date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    month_start = date_obj.replace(day=1).strftime("%Y-%m-%d")

    # Partition-Filter für block_timestamp_month (spart 99% der gescannten Bytes!)
    if table_name == "blocks":
        query = f"""
        SELECT *
        FROM `bigquery-public-data.crypto_bitcoin.{table_name}`
        WHERE timestamp_month = '{month_start}'
          AND DATE({date_column}) = '{target_date}'
        """
    else:
        query = f"""
        SELECT *
        FROM `bigquery-public-data.crypto_bitcoin.{table_name}`
        WHERE block_timestamp_month = '{month_start}'
          AND DATE({date_column}) = '{target_date}'
        """

    # Phase 1: Query ausführen
    if verbose:
        print(f"  📡 BigQuery läuft...", end="", flush=True)

    query_start = time.time()
    query_job = client.query(query)

    # Warte auf Query mit Status-Updates
    while not query_job.done():
        time.sleep(0.5)
        elapsed = time.time() - query_start
        if verbose:
            print(f"\r  📡 BigQuery läuft... ({elapsed:.0f}s)", end="", flush=True)

    query_time = time.time() - query_start

    # Phase 2: Ergebnisse laden
    if verbose:
        print(f"\r  📥 Lade Ergebnisse...                    ", end="", flush=True)

    load_start = time.time()
    rows = list(query_job.result())
    load_time = time.time() - load_start
    row_count = len(rows)

    if verbose:
        print(f"\r  ✓ Query: {format_duration(query_time)} | {row_count:,} Zeilen geladen ({format_duration(load_time)})", flush=True)

    # Phase 3: JSON schreiben mit Fortschritt
    output_file = table_dir / f"{table_name}_00000.json"
    bytes_written = 0

    if verbose and row_count > 0:
        pbar = tqdm(
            rows,
            desc=f"  💾 Schreibe {table_name}",
            unit=" rows",
            leave=False,
            ncols=80
        )
    else:
        pbar = rows

    with open(output_file, "w") as f:
        for row in pbar:
            row_dict = row_to_dict(row, table_name)
            line = json.dumps(row_dict) + "\n"
            f.write(line)
            bytes_written += len(line.encode('utf-8'))

    if verbose and row_count > 0:
        pbar.close()
        print(f"  ✓ Geschrieben: {format_bytes(bytes_written)} → {output_file.name}")

    return row_count, bytes_written


def main():
    parser = argparse.ArgumentParser(
        description="Exportiere Bitcoin-Daten von BigQuery (Sandbox-kompatibel)"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Startdatum (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="Enddatum (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/blockchain_exports",
        help="Ausgabeverzeichnis (default: data/blockchain_exports)"
    )
    parser.add_argument(
        "--project",
        default="btc-data-483415",
        help="Google Cloud Projekt-ID"
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=["blocks", "transactions"],
        help="Welche Tabellen exportieren (default: blocks, transactions). "
             "Hinweis: inputs/outputs sind in transactions als nested arrays enthalten!"
    )

    args = parser.parse_args()

    # BigQuery Client erstellen
    print(f"🔌 Verbinde mit BigQuery (Projekt: {args.project})...")
    client = bigquery.Client(project=args.project)
    print("✓ Verbunden!\n")

    # Datum-Range generieren
    dates = get_date_range(args.start_date, args.end_date)

    # Output-Verzeichnis erstellen
    output_dir = Path(args.output_dir) / f"{args.start_date}_{args.end_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"📦 BITCOIN BLOCKCHAIN EXPORT")
    print("=" * 60)
    print(f"  Zeitraum:    {args.start_date} bis {args.end_date} ({len(dates)} Tag(e))")
    print(f"  Tabellen:    {', '.join(args.tables)}")
    print(f"  Zielordner:  {output_dir}")
    print("=" * 60)

    # Mapping: Tabelle -> Datumsspalte
    date_columns = {
        "blocks": "timestamp",
        "transactions": "block_timestamp",
        "inputs": "block_timestamp",
        "outputs": "block_timestamp"
    }

    # Statistiken
    stats = {t: {"rows": 0, "bytes": 0} for t in args.tables}
    total_start = time.time()

    for day_idx, date in enumerate(dates, 1):
        print(f"\n📅 Tag {day_idx}/{len(dates)}: {date}")
        print("-" * 40)

        for table in args.tables:
            row_count, byte_count = export_table_for_date(
                client,
                table,
                date,
                output_dir,
                date_columns[table],
                verbose=True
            )
            stats[table]["rows"] += row_count
            stats[table]["bytes"] += byte_count

        # Zwischenbilanz nach jedem Tag
        total_bytes = sum(s["bytes"] for s in stats.values())
        total_rows = sum(s["rows"] for s in stats.values())
        elapsed = time.time() - total_start

        print(f"\n  📊 Zwischenbilanz: {total_rows:,} Zeilen | {format_bytes(total_bytes)} | {format_duration(elapsed)}")

        # Hochrechnung für restliche Tage
        if day_idx < len(dates):
            avg_bytes_per_day = total_bytes / day_idx
            estimated_total = avg_bytes_per_day * len(dates)
            remaining_days = len(dates) - day_idx
            avg_time_per_day = elapsed / day_idx
            estimated_remaining = avg_time_per_day * remaining_days

            print(f"  📈 Hochrechnung: ~{format_bytes(estimated_total)} gesamt | ~{format_duration(estimated_remaining)} verbleibend")

    total_time = time.time() - total_start

    print("\n" + "=" * 60)
    print("✅ EXPORT ABGESCHLOSSEN!")
    print("=" * 60)

    total_rows = 0
    total_bytes = 0
    for table, data in stats.items():
        print(f"  {table.capitalize():15} {data['rows']:>12,} Zeilen  {format_bytes(data['bytes']):>10}")
        total_rows += data["rows"]
        total_bytes += data["bytes"]

    print("-" * 60)
    print(f"  {'GESAMT':15} {total_rows:>12,} Zeilen  {format_bytes(total_bytes):>10}")
    print(f"  {'Dauer':15} {format_duration(total_time):>12}")
    print(f"  {'Speicherort':15} {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
