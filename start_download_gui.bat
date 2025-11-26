@echo off
REM Bitcoin Blockchain Downloader - Windows Launcher
REM Doppelklick auf diese Datei öffnet die GUI

cd /d %~dp0
call download-tool-venv\Scripts\activate.bat
python scripts\download_bitcoin_data.py
pause
