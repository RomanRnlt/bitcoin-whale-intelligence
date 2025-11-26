# Bitcoin Blockchain Downloader - Quick Start

Modern GUI tool to download Bitcoin blockchain data from Blockchair.

## 🚀 Quick Start (One-Time Setup)

### macOS/Linux

```bash
# 1. Create virtual environment
python3.13 -m venv download-tool-venv

# 2. Install dependencies
source download-tool-venv/bin/activate
pip install -r download-tool-requirements.txt
deactivate

# 3. Start GUI (from now on just double-click this):
./start_download_gui.sh
```

### Windows

```batch
REM 1. Create virtual environment
python -m venv download-tool-venv

REM 2. Install dependencies
download-tool-venv\Scripts\activate
pip install -r download-tool-requirements.txt
deactivate

REM 3. Start GUI (from now on just double-click this):
start_download_gui.bat
```

## ✨ Features

- **Modern Dark Mode UI** - Clean, professional interface
- **Pause/Resume** - Pause downloads anytime, resume later
- **Auto-Resume** - Close GUI and continue where you left off
- **Progress Tracking** - Real-time progress with ETA
- **Failsafe** - Already downloaded files are automatically skipped

## 📋 What You Need

**macOS:**
- Python 3.13 with tkinter: `brew install python-tk@3.13`

**Windows:**
- Python 3.9+ (from python.org - includes tkinter)

**All Platforms:**
- ~500GB free disk space (for year 2021 data)
- Internet connection

## 🎯 Usage

1. **Double-click** `start_download_gui.sh` (Mac/Linux) or `start_download_gui.bat` (Windows)
2. Select output directory
3. Choose date range (preset: Year 2021)
4. Select tables (blocks, transactions, outputs)
5. Click "Calculate Size" to see estimated download size
6. Click "Start Download"

## 💾 Download Size Estimates

| Period | Size (uncompressed) |
|--------|---------------------|
| 1 Day | ~1.3 GB |
| 1 Week | ~9 GB |
| 1 Month | ~40 GB |
| Q1 2021 | ~120 GB |
| Year 2021 | ~480 GB |

*Note: .gz files are deleted after extraction (saves ~70% disk space)*

## 🔧 Troubleshooting

### GUI doesn't start

**macOS:**
```bash
# Install python-tk
brew install python-tk@3.13
```

**Windows:**
- Reinstall Python from python.org (make sure to check "tcl/tk" option)

### "No module named 'customtkinter'"

```bash
# Reinstall dependencies
source download-tool-venv/bin/activate  # Mac/Linux
# or
download-tool-venv\Scripts\activate  # Windows

pip install -r download-tool-requirements.txt
```

## 📚 Next Steps

After downloading data:

1. Start Jupyter: `./start_project.sh`
2. Open: `notebooks/01_data_exploration.ipynb`
3. Configure data source to "local" in notebook

See [scripts/README.md](scripts/README.md) for more details.

## 🎓 About

This tool is part of a Master's thesis project on Bitcoin Whale Intelligence using entity resolution techniques.

**Technologies:**
- CustomTkinter (Modern UI)
- Blockchair API (Data source)
- Python 3.13
