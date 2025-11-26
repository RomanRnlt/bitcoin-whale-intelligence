#!/bin/bash
# Quick Start: Download Bitcoin 2021 Blockchain Data from Blockchair
# Dieser Script lädt automatisch das Jahr 2021 herunter (ca. 4-6 Stunden je nach Internet)

set -e  # Exit on error

echo "🚀 Bitcoin Whale Intelligence - Blockchair Data Download"
echo "=========================================================="
echo ""
echo "Dieses Script lädt das Jahr 2021 von Blockchair herunter."
echo ""
echo "Geschätzte Download-Größe: 120-150 GB (komprimiert)"
echo "Geschätzter Speicherbedarf: 450-550 GB (unkomprimiert)"
echo "Geschätzte Dauer: 2-6 Stunden (je nach Internet)"
echo ""

# Prüfe ob SSD-Pfad gesetzt ist
if [ -z "$1" ]; then
    echo "❌ Fehler: Kein Output-Pfad angegeben!"
    echo ""
    echo "Usage:"
    echo "  ./download_2021_data.sh /Volumes/MySSD/bitcoin_data"
    echo ""
    echo "Beispiele:"
    echo "  ./download_2021_data.sh /Volumes/ExternalSSD/bitcoin_data"
    echo "  ./download_2021_data.sh /mnt/ssd/bitcoin_data"
    echo ""
    exit 1
fi

OUTPUT_DIR="$1"

echo "Output-Verzeichnis: $OUTPUT_DIR"
echo ""

# Prüfe ob Verzeichnis existiert oder erstellt werden kann
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "📁 Erstelle Verzeichnis: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR" || {
        echo "❌ Fehler: Kann Verzeichnis nicht erstellen!"
        exit 1
    }
fi

# Prüfe verfügbaren Speicherplatz (macOS)
if command -v df &> /dev/null; then
    AVAILABLE=$(df -h "$OUTPUT_DIR" | awk 'NR==2 {print $4}')
    echo "💾 Verfügbarer Speicherplatz: $AVAILABLE"
    echo ""
fi

# Warnung
echo "⚠️  WICHTIG:"
echo "   - Download dauert mehrere Stunden"
echo "   - Benötigt ~500 GB freien Speicher"
echo "   - Internet-Verbindung muss stabil sein"
echo ""

read -p "Fortfahren? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "🔧 Prüfe Python Dependencies..."
pip install requests tqdm > /dev/null 2>&1 || {
    echo "⚠️  Warning: Konnte requests/tqdm nicht installieren"
    echo "   Installiere manuell: pip install requests tqdm"
}

echo ""
echo "📥 Starte Download..."
echo "=========================================================="
echo ""

# Download-Optionen
YEAR=2021
WORKERS=4  # Parallele Downloads (erhöhen wenn Internet schnell)
TABLES="blocks transactions outputs"

# Starte Download
python scripts/download_blockchair.py \
    --year $YEAR \
    --output "$OUTPUT_DIR" \
    --tables $TABLES \
    --workers $WORKERS \
    --remove-gz \
    || {
        echo ""
        echo "❌ Download fehlgeschlagen!"
        echo ""
        echo "Mögliche Gründe:"
        echo "  - Internet-Verbindung unterbrochen"
        echo "  - Zu wenig Speicherplatz"
        echo "  - Blockchair Server nicht erreichbar"
        echo ""
        echo "Du kannst den Download später fortsetzen mit:"
        echo "  python scripts/download_blockchair.py --year 2021 --output $OUTPUT_DIR --remove-gz"
        echo ""
        exit 1
    }

echo ""
echo "=========================================================="
echo "✅ DOWNLOAD ABGESCHLOSSEN!"
echo "=========================================================="
echo ""
echo "Daten gespeichert in: $OUTPUT_DIR"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. Teste ob Daten korrekt geladen werden können"
echo ""
echo "2. Öffne Jupyter Notebook:"
echo "   ./start_project.sh"
echo ""
echo "3. Öffne notebooks/01_data_exploration.ipynb"
echo "   und ändere cell-2 zu: config = DataConfig(source='local', local_data_path='$OUTPUT_DIR/extracted')"
echo ""
echo "🎉 Viel Erfolg beim Whale-Hunting!"
