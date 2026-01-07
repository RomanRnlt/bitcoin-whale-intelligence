#!/usr/bin/env python3
"""
Bitcoin Blockchain Download von Blockchair (KOSTENLOS, kein Account nötig)

Lädt Bitcoin Blocks und Transactions von Blockchair herunter und konvertiert
sie ins bitcoin-etl Format:

blockchain_exports/
└── YYYY-MM-DD_YYYY-MM-DD/
    ├── blocks/
    │   └── date=YYYY-MM-DD/
    │       └── blocks_00000.json
    └── transactions/
        └── date=YYYY-MM-DD/
            └── transactions_00000.json

Verwendung:
    # Ein Tag herunterladen
    python src/download_btc_blockchair.py --date 2024-01-15

    # Mehrere Tage
    python src/download_btc_blockchair.py --start-date 2024-01-01 --end-date 2024-01-07

    # Nur Transactions
    python src/download_btc_blockchair.py --date 2024-01-15 --transactions-only

Hinweis: Blockchair TSV-Dumps sind täglich verfügbar ab 2009-01-03
"""

import argparse
import gzip
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from tqdm import tqdm


BLOCKCHAIR_BASE_URL = "https://gz.blockchair.com/bitcoin"


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


def download_file(url: str, output_path: Path) -> bool:
    """Lädt eine Datei mit curl herunter."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "-o", str(output_path), url],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        print(f"Download-Fehler: {e}")
        return False


def convert_blockchair_transactions_to_etl(tsv_path: Path, json_path: Path) -> int:
    """
    Konvertiert Blockchair TSV zu bitcoin-etl JSON Format.

    Blockchair TSV Spalten (transactions):
    block_id, hash, time, size, weight, version, lock_time, is_coinbase,
    has_witness, input_count, output_count, input_total, input_total_usd,
    output_total, output_total_usd, fee, fee_usd, fee_per_kb, fee_per_kb_usd,
    fee_per_kwu, fee_per_kwu_usd, cdd_total
    """
    count = 0

    with gzip.open(tsv_path, 'rt', encoding='utf-8') as infile, \
         open(json_path, 'w', encoding='utf-8') as outfile:

        # Header lesen
        header = infile.readline().strip().split('\t')

        for line in infile:
            fields = line.strip().split('\t')
            if len(fields) < len(header):
                continue

            row = dict(zip(header, fields))

            # Konvertiere zu bitcoin-etl Format
            tx = {
                "hash": row.get("hash", ""),
                "block_number": int(row.get("block_id", 0)),
                "block_timestamp": row.get("time", ""),
                "size": int(row.get("size", 0)),
                "virtual_size": int(row.get("weight", 0)) // 4 if row.get("weight") else 0,
                "version": int(row.get("version", 0)),
                "lock_time": int(row.get("lock_time", 0)),
                "is_coinbase": row.get("is_coinbase", "0") == "1",
                "input_count": int(row.get("input_count", 0)),
                "output_count": int(row.get("output_count", 0)),
                "input_value": int(row.get("input_total", 0)),
                "output_value": int(row.get("output_total", 0)),
                "fee": int(row.get("fee", 0)),
                # inputs und outputs sind in separaten Dateien bei Blockchair
                "inputs": [],
                "outputs": []
            }

            outfile.write(json.dumps(tx) + "\n")
            count += 1

    return count


def convert_blockchair_blocks_to_etl(tsv_path: Path, json_path: Path) -> int:
    """
    Konvertiert Blockchair Blocks TSV zu bitcoin-etl JSON Format.
    """
    count = 0

    with gzip.open(tsv_path, 'rt', encoding='utf-8') as infile, \
         open(json_path, 'w', encoding='utf-8') as outfile:

        header = infile.readline().strip().split('\t')

        for line in infile:
            fields = line.strip().split('\t')
            if len(fields) < len(header):
                continue

            row = dict(zip(header, fields))

            block = {
                "hash": row.get("hash", ""),
                "number": int(row.get("id", 0)),
                "timestamp": row.get("time", ""),
                "size": int(row.get("size", 0)),
                "weight": int(row.get("weight", 0)),
                "version": int(row.get("version", 0)),
                "merkle_root": row.get("merkle_root", ""),
                "nonce": int(row.get("nonce", 0)),
                "bits": row.get("bits", ""),
                "transaction_count": int(row.get("transaction_count", 0)),
            }

            outfile.write(json.dumps(block) + "\n")
            count += 1

    return count


def download_inputs_outputs(target_date: str, output_dir: Path) -> tuple[int, int]:
    """
    Lädt die separaten inputs und outputs Dateien von Blockchair.
    Diese enthalten die detaillierten Input/Output-Daten mit Adressen.
    """
    date_compact = target_date.replace("-", "")

    inputs_count = 0
    outputs_count = 0

    # Inputs herunterladen
    inputs_url = f"{BLOCKCHAIR_BASE_URL}/inputs/blockchair_bitcoin_inputs_{date_compact}.tsv.gz"
    inputs_dir = output_dir / f"inputs/date={target_date}"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix='.tsv.gz', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    if download_file(inputs_url, tmp_path):
        json_path = inputs_dir / "inputs_00000.json"
        inputs_count = convert_blockchair_inputs_to_etl(tmp_path, json_path)
        tmp_path.unlink()

    # Outputs herunterladen
    outputs_url = f"{BLOCKCHAIR_BASE_URL}/outputs/blockchair_bitcoin_outputs_{date_compact}.tsv.gz"
    outputs_dir = output_dir / f"outputs/date={target_date}"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix='.tsv.gz', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    if download_file(outputs_url, tmp_path):
        json_path = outputs_dir / "outputs_00000.json"
        outputs_count = convert_blockchair_outputs_to_etl(tmp_path, json_path)
        tmp_path.unlink()

    return inputs_count, outputs_count


def convert_blockchair_inputs_to_etl(tsv_path: Path, json_path: Path) -> int:
    """Konvertiert Blockchair inputs TSV zu JSON."""
    count = 0

    with gzip.open(tsv_path, 'rt', encoding='utf-8') as infile, \
         open(json_path, 'w', encoding='utf-8') as outfile:

        header = infile.readline().strip().split('\t')

        for line in infile:
            fields = line.strip().split('\t')
            if len(fields) < len(header):
                continue

            row = dict(zip(header, fields))

            inp = {
                "transaction_hash": row.get("transaction_hash", ""),
                "index": int(row.get("index", 0)),
                "spent_transaction_hash": row.get("spending_transaction_hash", ""),
                "spent_output_index": int(row.get("spending_index", 0)) if row.get("spending_index") else 0,
                "value": int(row.get("value", 0)),
                "addresses": [row.get("recipient", "")] if row.get("recipient") else [],
            }

            outfile.write(json.dumps(inp) + "\n")
            count += 1

    return count


def convert_blockchair_outputs_to_etl(tsv_path: Path, json_path: Path) -> int:
    """Konvertiert Blockchair outputs TSV zu JSON."""
    count = 0

    with gzip.open(tsv_path, 'rt', encoding='utf-8') as infile, \
         open(json_path, 'w', encoding='utf-8') as outfile:

        header = infile.readline().strip().split('\t')

        for line in infile:
            fields = line.strip().split('\t')
            if len(fields) < len(header):
                continue

            row = dict(zip(header, fields))

            out = {
                "transaction_hash": row.get("transaction_hash", ""),
                "index": int(row.get("index", 0)),
                "value": int(row.get("value", 0)),
                "addresses": [row.get("recipient", "")] if row.get("recipient") else [],
                "type": row.get("type", ""),
                "is_spent": row.get("is_spent", "0") == "1",
            }

            outfile.write(json.dumps(out) + "\n")
            count += 1

    return count


def download_and_convert_day(
    target_date: str,
    output_dir: Path,
    transactions_only: bool = False,
    blocks_only: bool = False,
    include_inputs_outputs: bool = True
) -> dict:
    """Lädt und konvertiert alle Daten für einen Tag."""

    date_compact = target_date.replace("-", "")
    stats = {"blocks": 0, "transactions": 0, "inputs": 0, "outputs": 0}

    # Blocks
    if not transactions_only:
        blocks_url = f"{BLOCKCHAIR_BASE_URL}/blocks/blockchair_bitcoin_blocks_{date_compact}.tsv.gz"
        blocks_dir = output_dir / f"blocks/date={target_date}"
        blocks_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(suffix='.tsv.gz', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        if download_file(blocks_url, tmp_path):
            json_path = blocks_dir / "blocks_00000.json"
            stats["blocks"] = convert_blockchair_blocks_to_etl(tmp_path, json_path)
            tmp_path.unlink()

    # Transactions
    if not blocks_only:
        tx_url = f"{BLOCKCHAIR_BASE_URL}/transactions/blockchair_bitcoin_transactions_{date_compact}.tsv.gz"
        tx_dir = output_dir / f"transactions/date={target_date}"
        tx_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(suffix='.tsv.gz', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        if download_file(tx_url, tmp_path):
            json_path = tx_dir / "transactions_00000.json"
            stats["transactions"] = convert_blockchair_transactions_to_etl(tmp_path, json_path)
            tmp_path.unlink()

        # Inputs und Outputs (für Whale-Analyse wichtig!)
        if include_inputs_outputs:
            stats["inputs"], stats["outputs"] = download_inputs_outputs(target_date, output_dir)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Lade Bitcoin-Daten von Blockchair (kostenlos, kein Account)"
    )
    parser.add_argument(
        "--date",
        help="Einzelnes Datum (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--start-date",
        help="Startdatum für Bereich (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        help="Enddatum für Bereich (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/blockchain_exports",
        help="Ausgabeverzeichnis (default: data/blockchain_exports)"
    )
    parser.add_argument(
        "--transactions-only",
        action="store_true",
        help="Nur Transactions herunterladen"
    )
    parser.add_argument(
        "--blocks-only",
        action="store_true",
        help="Nur Blocks herunterladen"
    )
    parser.add_argument(
        "--no-inputs-outputs",
        action="store_true",
        help="Keine separaten Input/Output-Dateien (schneller, aber weniger Daten)"
    )

    args = parser.parse_args()

    # Datum(e) bestimmen
    if args.date:
        dates = [args.date]
        date_range_str = args.date
    elif args.start_date and args.end_date:
        dates = get_date_range(args.start_date, args.end_date)
        date_range_str = f"{args.start_date}_{args.end_date}"
    else:
        parser.error("Entweder --date oder --start-date und --end-date angeben")
        return

    # Output-Verzeichnis
    output_dir = Path(args.output_dir) / date_range_str
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLade {len(dates)} Tag(e) von Blockchair herunter...")
    print(f"Ziel: {output_dir}")
    print("-" * 60)

    total_stats = {"blocks": 0, "transactions": 0, "inputs": 0, "outputs": 0}

    for date in tqdm(dates, desc="Lade Tage"):
        stats = download_and_convert_day(
            date,
            output_dir,
            transactions_only=args.transactions_only,
            blocks_only=args.blocks_only,
            include_inputs_outputs=not args.no_inputs_outputs
        )
        for key in total_stats:
            total_stats[key] += stats[key]

    print("-" * 60)
    print("Download abgeschlossen!")
    print(f"  Blocks:       {total_stats['blocks']:,}")
    print(f"  Transactions: {total_stats['transactions']:,}")
    print(f"  Inputs:       {total_stats['inputs']:,}")
    print(f"  Outputs:      {total_stats['outputs']:,}")
    print(f"  Speicherort:  {output_dir}")


if __name__ == "__main__":
    main()
