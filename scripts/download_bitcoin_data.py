#!/usr/bin/env python3
"""
Bitcoin Blockchain Data Downloader (Blockchair)
Cross-platform GUI tool for downloading Bitcoin blockchain dumps.

Works on: macOS, Windows, Linux
"""

import os
import sys
import gzip
import shutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
import threading
import queue


class BlockchairDownloader:
    """Handles Blockchair data downloads."""

    BASE_URL = "https://gz.blockchair.com/bitcoin/"
    TABLES = {
        "blocks": 0.8,        # MB per day (approximate)
        "transactions": 150,   # MB per day
        "outputs": 250        # MB per day
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.extracted_dir = self.output_dir / "extracted"

    def estimate_size(self, start_date: datetime, end_date: datetime,
                     tables: List[str]) -> Tuple[float, float]:
        """
        Estimates download size.

        Returns:
            (compressed_gb, uncompressed_gb)
        """
        days = (end_date - start_date).days + 1

        total_mb_compressed = 0
        for table in tables:
            total_mb_compressed += self.TABLES[table] * days

        compressed_gb = total_mb_compressed / 1024
        uncompressed_gb = compressed_gb / 0.3  # .gz compression ratio ~30%

        return compressed_gb, uncompressed_gb

    def get_date_range(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate list of dates between start and end."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def build_url(self, table: str, date: datetime) -> str:
        """Build download URL for specific table and date."""
        date_str = date.strftime("%Y-%m-%d")
        filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
        return self.BASE_URL + f"{table}/{filename}"

    def download_file(self, url: str, output_path: Path,
                     progress_callback=None) -> bool:
        """Download single file with progress tracking."""
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress, downloaded, total_size)

            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False  # File doesn't exist (normal)
            raise
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def extract_gz(self, gz_path: Path, output_path: Path) -> bool:
        """Extract .gz file."""
        try:
            with gzip.open(gz_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")

    def download_and_extract(self, start_date: datetime, end_date: datetime,
                           tables: List[str], remove_gz: bool = True,
                           progress_callback=None, log_callback=None) -> dict:
        """
        Download and extract data for date range.

        Returns:
            dict with statistics
        """
        # Create directories
        for table in tables:
            (self.raw_dir / table).mkdir(parents=True, exist_ok=True)
            (self.extracted_dir / table).mkdir(parents=True, exist_ok=True)

        dates = self.get_date_range(start_date, end_date)

        stats = {
            'total': len(dates) * len(tables),
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'downloaded_mb': 0
        }

        current_task = 0

        for date in dates:
            for table in tables:
                current_task += 1
                date_str = date.strftime("%Y-%m-%d")

                # File paths
                gz_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
                tsv_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv"

                gz_path = self.raw_dir / table / gz_filename
                tsv_path = self.extracted_dir / table / tsv_filename

                # Log progress
                if log_callback:
                    log_callback(f"[{current_task}/{stats['total']}] {table} {date_str}")

                # Skip if already extracted
                if tsv_path.exists():
                    if log_callback:
                        log_callback(f"  → Already exists, skipping")
                    stats['skipped'] += 1
                    if progress_callback:
                        progress_callback(current_task, stats['total'])
                    continue

                # Download
                url = self.build_url(table, date)

                try:
                    if log_callback:
                        log_callback(f"  → Downloading...")

                    def download_progress(pct, downloaded, total):
                        if log_callback:
                            log_callback(f"  → Downloading: {pct:.1f}% ({downloaded/1024/1024:.1f} MB)")

                    success = self.download_file(url, gz_path, download_progress)

                    if not success:
                        if log_callback:
                            log_callback(f"  → Not found (404), skipping")
                        stats['skipped'] += 1
                        if progress_callback:
                            progress_callback(current_task, stats['total'])
                        continue

                    # Track size
                    file_size_mb = gz_path.stat().st_size / 1024 / 1024
                    stats['downloaded_mb'] += file_size_mb

                    # Extract
                    if log_callback:
                        log_callback(f"  → Extracting...")

                    self.extract_gz(gz_path, tsv_path)

                    # Remove .gz if requested
                    if remove_gz:
                        gz_path.unlink()
                        if log_callback:
                            log_callback(f"  → Removed .gz file")

                    stats['successful'] += 1
                    if log_callback:
                        log_callback(f"  ✓ Complete ({file_size_mb:.1f} MB)")

                except Exception as e:
                    stats['failed'] += 1
                    if log_callback:
                        log_callback(f"  ✗ Error: {str(e)}")

                # Update overall progress
                if progress_callback:
                    progress_callback(current_task, stats['total'])

        return stats


class DownloaderGUI:
    """GUI for Bitcoin data downloader."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bitcoin Blockchain Data Downloader")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Style
        self.style = ttk.Style()
        if sys.platform == "darwin":  # macOS
            self.style.theme_use("aqua")
        elif sys.platform == "win32":  # Windows
            self.style.theme_use("vista")
        else:  # Linux
            self.style.theme_use("clam")

        # Variables
        self.output_dir = tk.StringVar()
        self.start_date = tk.StringVar(value="2021-01-01")
        self.end_date = tk.StringVar(value="2021-12-31")
        self.remove_gz = tk.BooleanVar(value=True)

        # Table selection
        self.table_blocks = tk.BooleanVar(value=True)
        self.table_transactions = tk.BooleanVar(value=True)
        self.table_outputs = tk.BooleanVar(value=True)

        # Download state
        self.is_downloading = False
        self.download_thread = None
        self.log_queue = queue.Queue()

        self.setup_ui()
        self.process_log_queue()

    def setup_ui(self):
        """Setup UI components."""
        # Header
        header = ttk.Frame(self.root, padding="20")
        header.pack(fill=tk.X)

        title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        title = ttk.Label(header, text="🐋 Bitcoin Blockchain Data Downloader",
                         font=title_font)
        title.pack()

        subtitle = ttk.Label(header, text="Download Blockchair dumps locally for analysis",
                            foreground="gray")
        subtitle.pack()

        # Main content
        content = ttk.Frame(self.root, padding="20")
        content.pack(fill=tk.BOTH, expand=True)

        # Output directory
        dir_frame = ttk.LabelFrame(content, text="📁 Output Directory", padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        dir_input = ttk.Frame(dir_frame)
        dir_input.pack(fill=tk.X)

        ttk.Entry(dir_input, textvariable=self.output_dir, width=60).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(dir_input, text="Browse...", command=self.browse_directory).pack(side=tk.LEFT)

        # Date range
        date_frame = ttk.LabelFrame(content, text="📅 Date Range", padding="10")
        date_frame.pack(fill=tk.X, pady=(0, 10))

        date_grid = ttk.Frame(date_frame)
        date_grid.pack(fill=tk.X)

        ttk.Label(date_grid, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(date_grid, textvariable=self.start_date, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(date_grid, text="End Date (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(date_grid, textvariable=self.end_date, width=20).grid(row=1, column=1, padx=5, pady=5)

        # Quick presets
        preset_frame = ttk.Frame(date_grid)
        preset_frame.grid(row=0, column=2, rowspan=2, padx=20)

        ttk.Label(preset_frame, text="Quick Presets:").pack(anchor=tk.W)
        ttk.Button(preset_frame, text="Year 2021",
                  command=lambda: self.set_preset("2021-01-01", "2021-12-31")).pack(fill=tk.X, pady=2)
        ttk.Button(preset_frame, text="Q1 2021",
                  command=lambda: self.set_preset("2021-01-01", "2021-03-31")).pack(fill=tk.X, pady=2)
        ttk.Button(preset_frame, text="January 2021",
                  command=lambda: self.set_preset("2021-01-01", "2021-01-31")).pack(fill=tk.X, pady=2)

        # Tables selection
        tables_frame = ttk.LabelFrame(content, text="📊 Tables to Download", padding="10")
        tables_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(tables_frame, text="Blocks (~1 MB/day)",
                       variable=self.table_blocks).pack(anchor=tk.W)
        ttk.Checkbutton(tables_frame, text="Transactions (~150 MB/day)",
                       variable=self.table_transactions).pack(anchor=tk.W)
        ttk.Checkbutton(tables_frame, text="Outputs (~250 MB/day)",
                       variable=self.table_outputs).pack(anchor=tk.W)

        # Options
        options_frame = ttk.LabelFrame(content, text="⚙️ Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(options_frame, text="Remove .gz files after extraction (saves ~70% disk space)",
                       variable=self.remove_gz).pack(anchor=tk.W)

        # Size estimate
        self.size_frame = ttk.Frame(content)
        self.size_frame.pack(fill=tk.X, pady=(0, 10))

        self.size_label = ttk.Label(self.size_frame, text="", foreground="blue",
                                    font=tkfont.Font(size=10, weight="bold"))
        self.size_label.pack()

        ttk.Button(content, text="Calculate Size",
                  command=self.calculate_size).pack(pady=5)

        # Download button
        self.download_button = ttk.Button(content, text="▶ Start Download",
                                         command=self.start_download)
        self.download_button.pack(pady=10)

        # Progress
        progress_frame = ttk.LabelFrame(content, text="📥 Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Ready to download")
        self.progress_label.pack(anchor=tk.W)

        # Log
        log_scroll = ttk.Scrollbar(progress_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(progress_frame, height=15, wrap=tk.WORD,
                               yscrollcommand=log_scroll.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)

    def set_preset(self, start: str, end: str):
        """Set date preset."""
        self.start_date.set(start)
        self.end_date.set(end)

    def get_selected_tables(self) -> List[str]:
        """Get selected tables."""
        tables = []
        if self.table_blocks.get():
            tables.append("blocks")
        if self.table_transactions.get():
            tables.append("transactions")
        if self.table_outputs.get():
            tables.append("outputs")
        return tables

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    def calculate_size(self):
        """Calculate and display estimated size."""
        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
            tables = self.get_selected_tables()

            if not tables:
                messagebox.showerror("Error", "Please select at least one table")
                return

            if start > end:
                messagebox.showerror("Error", "Start date must be before end date")
                return

            # Calculate
            downloader = BlockchairDownloader(self.output_dir.get() or "/tmp")
            compressed_gb, uncompressed_gb = downloader.estimate_size(start, end, tables)

            days = (end - start).days + 1

            # Display
            text = f"📊 Estimated Size for {days} days:\n"
            text += f"   Compressed (.gz): ~{compressed_gb:.1f} GB\n"
            text += f"   Uncompressed (.tsv): ~{uncompressed_gb:.1f} GB\n"

            if self.remove_gz.get():
                text += f"   Total (with --remove-gz): ~{uncompressed_gb:.1f} GB"
            else:
                text += f"   Total (keeping .gz): ~{compressed_gb + uncompressed_gb:.1f} GB"

            self.size_label.config(text=text)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def log(self, message: str):
        """Add message to log."""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Process log messages from queue."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_log_queue)

    def start_download(self):
        """Start download in background thread."""
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return

        # Validate inputs
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return

        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        tables = self.get_selected_tables()
        if not tables:
            messagebox.showerror("Error", "Please select at least one table")
            return

        if start > end:
            messagebox.showerror("Error", "Start date must be before end date")
            return

        # Create output directory
        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        # Confirm
        days = (end - start).days + 1
        confirm = messagebox.askyesno(
            "Confirm Download",
            f"Download {days} days of data for {len(tables)} table(s)?\n\n"
            f"This may take several hours.\n"
            f"The download cannot run in parallel - files are downloaded sequentially."
        )

        if not confirm:
            return

        # Start download thread
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED, text="⏸ Downloading...")
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)

        self.download_thread = threading.Thread(
            target=self.download_worker,
            args=(start, end, tables),
            daemon=True
        )
        self.download_thread.start()

    def download_worker(self, start: datetime, end: datetime, tables: List[str]):
        """Worker thread for downloading."""
        try:
            downloader = BlockchairDownloader(self.output_dir.get())

            def progress_callback(current, total):
                pct = (current / total) * 100
                self.progress_var.set(pct)
                self.progress_label.config(text=f"Progress: {current}/{total} files ({pct:.1f}%)")

            def log_callback(message):
                self.log(message)

            self.log("="*60)
            self.log("BITCOIN BLOCKCHAIN DATA DOWNLOAD")
            self.log("="*60)
            self.log(f"Period: {start.date()} to {end.date()}")
            self.log(f"Tables: {', '.join(tables)}")
            self.log(f"Output: {self.output_dir.get()}")
            self.log(f"Remove .gz: {self.remove_gz.get()}")
            self.log("="*60)
            self.log("")
            self.log("⚠️  Downloads are sequential (Blockchair limitation)")
            self.log("   Please be patient, this may take several hours.")
            self.log("")

            stats = downloader.download_and_extract(
                start, end, tables,
                remove_gz=self.remove_gz.get(),
                progress_callback=progress_callback,
                log_callback=log_callback
            )

            self.log("")
            self.log("="*60)
            self.log("DOWNLOAD COMPLETE")
            self.log("="*60)
            self.log(f"Total files: {stats['total']}")
            self.log(f"✓ Successful: {stats['successful']}")
            self.log(f"⏭ Skipped: {stats['skipped']}")
            self.log(f"✗ Failed: {stats['failed']}")
            self.log(f"📦 Downloaded: {stats['downloaded_mb']:.1f} MB")
            self.log("="*60)
            self.log("")
            self.log(f"Data saved to: {self.output_dir.get()}/extracted")
            self.log("")
            self.log("Next steps:")
            self.log("1. Open Jupyter: ./start_project.sh")
            self.log("2. Open notebook: notebooks/02_local_data_exploration.ipynb")
            self.log("3. Set: BLOCKCHAIR_DATA_DIR = \"<your_path>/extracted\"")

            messagebox.showinfo("Success",
                              f"Download complete!\n\n"
                              f"Successful: {stats['successful']}\n"
                              f"Skipped: {stats['skipped']}\n"
                              f"Failed: {stats['failed']}")

        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}")
            messagebox.showerror("Download Failed", str(e))

        finally:
            self.is_downloading = False
            self.download_button.config(state=tk.NORMAL, text="▶ Start Download")

    def run(self):
        """Run the GUI."""
        self.root.mainloop()


if __name__ == "__main__":
    app = DownloaderGUI()
    app.run()
