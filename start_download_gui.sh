#!/bin/bash
# Bitcoin Blockchain Downloader - macOS/Linux Launcher
# Doppelklick auf diese Datei öffnet die GUI

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate venv and start GUI
source download-tool-venv/bin/activate
python scripts/download_bitcoin_data.py
