#!/usr/bin/env python3
"""
Blockchair Bitcoin Blockchain Dump Downloader
Downloads, extracts, and organizes Blockchair TSV dumps for local analysis.

Usage:
    python download_blockchair.py --year 2021 --output /path/to/ssd
    python download_blockchair.py --year 2021 --month 1 --output /path/to/ssd
    python download_blockchair.py --date-range 2021-01-01 2021-03-31 --output /path/to/ssd
"""

import argparse
import gzip
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import requests
from tqdm import tqdm
import concurrent.futures
from urllib.parse import urljoin


class BlockchairDownloader:
    """Downloads and processes Blockchair Bitcoin dumps."""

    BASE_URL = "https://gz.blockchair.com/bitcoin/"
    TABLES = ["blocks", "transactions", "outputs"]  # inputs sind in transactions enthalten

    def __init__(self, output_dir: Path, max_workers: int = 4):
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.raw_dir = self.output_dir / "raw"
        self.extracted_dir = self.output_dir / "extracted"

        # Erstelle Verzeichnisstruktur
        for table in self.TABLES:
            (self.raw_dir / table).mkdir(parents=True, exist_ok=True)
            (self.extracted_dir / table).mkdir(parents=True, exist_ok=True)

    def get_date_range(self, start_date: str, end_date: str) -> List[datetime]:
        """Generiert Liste von Tagen zwischen start und end."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)

        return dates

    def build_url(self, table: str, date: datetime) -> str:
        """Konstruiert Download-URL für spezifischen Tag und Tabelle."""
        date_str = date.strftime("%Y-%m-%d")
        filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
        return urljoin(self.BASE_URL, f"{table}/{filename}")

    def download_file(self, url: str, output_path: Path, skip_existing: bool = True) -> bool:
        """Lädt einzelne Datei herunter mit Progress Bar."""
        if skip_existing and output_path.exists():
            print(f"⏭️  Skipping (exists): {output_path.name}")
            return True

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True,
                         desc=output_path.name, leave=False) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))

            print(f"✅ Downloaded: {output_path.name} ({total_size / 1024 / 1024:.1f} MB)")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️  Not found (might not exist): {output_path.name}")
            else:
                print(f"❌ HTTP Error {e.response.status_code}: {output_path.name}")
            return False
        except Exception as e:
            print(f"❌ Error downloading {output_path.name}: {str(e)}")
            return False

    def extract_gz(self, gz_path: Path, output_path: Path, remove_gz: bool = False) -> bool:
        """Entpackt .gz Datei zu .tsv."""
        if output_path.exists():
            print(f"⏭️  Skipping extraction (exists): {output_path.name}")
            return True

        try:
            with gzip.open(gz_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            print(f"📦 Extracted: {output_path.name}")

            if remove_gz:
                gz_path.unlink()
                print(f"🗑️  Removed: {gz_path.name}")

            return True

        except Exception as e:
            print(f"❌ Error extracting {gz_path.name}: {str(e)}")
            return False

    def download_and_extract_day(self, table: str, date: datetime,
                                  extract: bool = True, remove_gz: bool = False) -> bool:
        """Lädt und extrahiert Daten für einen Tag und eine Tabelle."""
        url = self.build_url(table, date)
        date_str = date.strftime("%Y-%m-%d")

        gz_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
        tsv_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv"

        gz_path = self.raw_dir / table / gz_filename
        tsv_path = self.extracted_dir / table / tsv_filename

        # Download
        success = self.download_file(url, gz_path)
        if not success:
            return False

        # Extract
        if extract:
            success = self.extract_gz(gz_path, tsv_path, remove_gz=remove_gz)
            if not success:
                return False

        return True

    def download_range(self, start_date: str, end_date: str,
                      tables: Optional[List[str]] = None,
                      extract: bool = True,
                      remove_gz: bool = False,
                      parallel: bool = True) -> dict:
        """
        Lädt Daten für Zeitraum herunter.

        Returns:
            dict mit Statistiken (successful, failed, skipped)
        """
        dates = self.get_date_range(start_date, end_date)
        tables = tables or self.TABLES

        stats = {
            'successful': 0,
            'failed': 0,
            'total': len(dates) * len(tables)
        }

        print(f"\n{'='*70}")
        print(f"📥 BLOCKCHAIR DOWNLOAD")
        print(f"{'='*70}")
        print(f"Period: {start_date} to {end_date} ({len(dates)} days)")
        print(f"Tables: {', '.join(tables)}")
        print(f"Output: {self.output_dir}")
        print(f"Extract: {extract}, Remove .gz: {remove_gz}")
        print(f"Parallel: {parallel} (workers: {self.max_workers})")
        print(f"{'='*70}\n")

        tasks = [
            (table, date)
            for date in dates
            for table in tables
        ]

        if parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self.download_and_extract_day,
                        table, date, extract, remove_gz
                    ): (table, date)
                    for table, date in tasks
                }

                for future in concurrent.futures.as_completed(futures):
                    table, date = futures[future]
                    try:
                        success = future.result()
                        if success:
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1
                    except Exception as e:
                        print(f"❌ Exception for {table} {date}: {str(e)}")
                        stats['failed'] += 1
        else:
            # Sequential download
            for table, date in tasks:
                try:
                    success = self.download_and_extract_day(table, date, extract, remove_gz)
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                except Exception as e:
                    print(f"❌ Exception for {table} {date}: {str(e)}")
                    stats['failed'] += 1

        return stats

    def print_summary(self, stats: dict):
        """Gibt Download-Zusammenfassung aus."""
        print(f"\n{'='*70}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"Total tasks: {stats['total']}")
        print(f"✅ Successful: {stats['successful']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"Success rate: {stats['successful']/stats['total']*100:.1f}%")
        print(f"{'='*70}\n")

        # Disk usage
        raw_size = sum(f.stat().st_size for f in self.raw_dir.rglob('*') if f.is_file())
        extracted_size = sum(f.stat().st_size for f in self.extracted_dir.rglob('*') if f.is_file())

        print(f"💾 Disk Usage:")
        print(f"  Raw (.gz):      {raw_size / 1024**3:.2f} GB")
        print(f"  Extracted (.tsv): {extracted_size / 1024**3:.2f} GB")
        print(f"  Total:          {(raw_size + extracted_size) / 1024**3:.2f} GB")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Download Blockchair Bitcoin blockchain dumps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download gesamtes Jahr 2021
  python download_blockchair.py --year 2021 --output /Volumes/MySSD/bitcoin_data

  # Download nur Januar 2021
  python download_blockchair.py --year 2021 --month 1 --output /Volumes/MySSD/bitcoin_data

  # Download spezifischer Zeitraum
  python download_blockchair.py --date-range 2021-01-01 2021-03-31 --output /Volumes/MySSD/bitcoin_data

  # Download ohne Extraktion (spart Zeit)
  python download_blockchair.py --year 2021 --output /Volumes/MySSD/bitcoin_data --no-extract

  # Download + Extraktion + .gz löschen (spart Platz)
  python download_blockchair.py --year 2021 --output /Volumes/MySSD/bitcoin_data --remove-gz
        """
    )

    # Zeitraum-Optionen
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--year', type=int, help='Jahr (z.B. 2021)')
    date_group.add_argument('--date-range', nargs=2, metavar=('START', 'END'),
                           help='Zeitraum (z.B. 2021-01-01 2021-12-31)')

    parser.add_argument('--month', type=int, help='Monat (1-12, nur mit --year)')
    parser.add_argument('--output', '-o', type=str, required=True,
                       help='Output-Verzeichnis (z.B. /Volumes/MySSD/bitcoin_data)')

    # Tabellen
    parser.add_argument('--tables', nargs='+',
                       choices=['blocks', 'transactions', 'outputs'],
                       default=['blocks', 'transactions', 'outputs'],
                       help='Welche Tabellen herunterladen (default: alle)')

    # Processing-Optionen
    parser.add_argument('--no-extract', action='store_true',
                       help='Nur downloaden, nicht extrahieren')
    parser.add_argument('--remove-gz', action='store_true',
                       help='.gz Dateien nach Extraktion löschen (spart Platz)')
    parser.add_argument('--sequential', action='store_true',
                       help='Sequenziell statt parallel (langsamer aber sicherer)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Anzahl paralleler Downloads (default: 4)')

    args = parser.parse_args()

    # Zeitraum bestimmen
    if args.year:
        if args.month:
            # Spezifischer Monat
            from calendar import monthrange
            start_date = f"{args.year}-{args.month:02d}-01"
            _, last_day = monthrange(args.year, args.month)
            end_date = f"{args.year}-{args.month:02d}-{last_day:02d}"
        else:
            # Ganzes Jahr
            start_date = f"{args.year}-01-01"
            end_date = f"{args.year}-12-31"
    else:
        # Custom range
        start_date, end_date = args.date_range

    # Initialisiere Downloader
    downloader = BlockchairDownloader(
        output_dir=Path(args.output),
        max_workers=args.workers
    )

    # Download starten
    stats = downloader.download_range(
        start_date=start_date,
        end_date=end_date,
        tables=args.tables,
        extract=not args.no_extract,
        remove_gz=args.remove_gz,
        parallel=not args.sequential
    )

    # Summary
    downloader.print_summary(stats)


if __name__ == "__main__":
    main()
