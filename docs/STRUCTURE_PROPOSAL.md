# Vorgeschlagene Projektstruktur-Verbesserung

## Problem: Aktuelle Struktur

```
bitcoin-whale-intelligence/
├── download_bitcoin_data.py        # ❌ Sollte in scripts/ sein
├── data_config.py                  # ❌ Sollte in src/ sein
├── DOWNLOAD_GUIDE.md               # ❌ Sollte in docs/ sein
├── INTEGRATION_SUMMARY.md          # ❌ Sollte in docs/ sein
├── BLOCKCHAIR_QUICKSTART.txt       # ❌ Sollte in docs/ sein
├── download_2021_data.sh           # ✅ OK (Convenience Script im Root)
├── start_project.sh                # ✅ OK (Convenience Script im Root)
├── scripts/
│   ├── download_blockchair.py      # ✅ OK
│   └── load_blockchair_data.py     # ❌ Sollte in src/ sein (ist Library-Code)
├── src/
│   └── __init__.py                 # ❌ Leeres Verzeichnis, wird nicht genutzt
└── docs/                           # ✅ Gut, aber unvollständig
```

## Lösung: Verbesserte Struktur

```
bitcoin-whale-intelligence/
├── README.md                       # ✅ Haupt-Dokumentation
├── requirements.txt                # ✅ Dependencies
├── .env.example                    # ✅ Config-Template
├── .gitignore                      # ✅ Git-Config
│
├── start_project.sh                # ✅ Convenience: Projekt starten
├── download_2021_data.sh           # ✅ Convenience: Daten downloaden
│
├── src/                            # 📦 Python-Package (Bibliotheks-Code)
│   ├── __init__.py
│   ├── data_config.py              # ← Hierhin verschieben
│   ├── loaders/
│   │   ├── __init__.py
│   │   └── blockchair.py           # ← load_blockchair_data.py hierhin
│   └── utils/
│       └── __init__.py
│
├── scripts/                        # 🔧 Ausführbare Tools
│   ├── download_bitcoin_data.py    # ← GUI Tool hierhin verschieben
│   └── download_blockchair.py      # ← CLI Tool (Legacy)
│
├── notebooks/                      # 📓 Jupyter Notebooks
│   ├── 00_test_bigquery_connection.ipynb
│   └── 01_data_exploration.ipynb
│
├── docs/                           # 📚 Alle Dokumentation
│   ├── SETUP.md
│   ├── PROJECT_CONTEXT.md
│   ├── NOTEBOOK_WORKFLOW.md
│   ├── SIMPLE_EXPLANATION.md
│   ├── DOWNLOAD_GUIDE.md           # ← Hierhin verschieben
│   ├── BLOCKCHAIR_INTEGRATION.md
│   ├── BLOCKCHAIR_QUICKSTART.txt   # ← Hierhin verschieben
│   └── STRUCTURE.md                # ← Neue Datei: Projektstruktur-Erklärung
│
├── data/                           # 💾 Lokale Daten (gitignored)
│   ├── raw/
│   ├── processed/
│   └── sample/
│
└── tests/                          # 🧪 Unit-Tests
    └── __init__.py
```

## Vorteile der neuen Struktur:

1. **Klare Trennung**:
   - `src/` = Bibliotheks-Code (importierbar)
   - `scripts/` = Ausführbare Tools
   - `docs/` = Alle Dokumentation

2. **Python-Best-Practices**:
   - `src/` ist ein richtiges Package
   - Import: `from src.data_config import DataConfig`
   - Import: `from src.loaders.blockchair import BlockchairDataLoader`

3. **Aufgeräumtes Root**:
   - Nur essenzielle Dateien im Root
   - Convenience-Scripts (start_project.sh, download_2021_data.sh)
   - Keine .md Dateien außer README.md

4. **Skalierbar**:
   - Neue Loader einfach zu src/loaders/ hinzufügen
   - Neue Utils zu src/utils/
   - Neue Scripts zu scripts/

## Migration-Plan:

### Schritt 1: Verschieben
```bash
# Library-Code nach src/
mv data_config.py src/
mkdir -p src/loaders
mv scripts/load_blockchair_data.py src/loaders/blockchair.py

# GUI Tool nach scripts/
mv download_bitcoin_data.py scripts/

# Dokumentation nach docs/
mv DOWNLOAD_GUIDE.md docs/
mv BLOCKCHAIR_QUICKSTART.txt docs/
mv INTEGRATION_SUMMARY.md docs/
```

### Schritt 2: Imports anpassen
- In Notebooks: `from src.data_config import DataConfig`
- In Scripts: `from src.loaders.blockchair import BlockchairDataLoader`

### Schritt 3: __init__.py aktualisieren
```python
# src/__init__.py
from .data_config import DataConfig, load_data, get_loader

# src/loaders/__init__.py
from .blockchair import BlockchairDataLoader
```

### Schritt 4: Testen
- Notebook 01 ausführen
- GUI Tool testen: `python scripts/download_bitcoin_data.py`

## Alternative: Minimal-Änderung (falls weniger Aufwand gewünscht)

Falls komplette Umstrukturierung zu viel ist, zumindest:

1. **Dokumentation aufräumen**:
   ```bash
   mv DOWNLOAD_GUIDE.md docs/
   mv BLOCKCHAIR_QUICKSTART.txt docs/
   mv INTEGRATION_SUMMARY.md docs/
   ```

2. **GUI Tool verschieben** (optional):
   ```bash
   mv download_bitcoin_data.py scripts/
   # download_2021_data.sh anpassen
   ```

Dadurch bleibt Root aufgeräumt, ohne größere Code-Änderungen.

## Empfehlung:

Für ein **Master-Projekt** würde ich die **vollständige Struktur** empfehlen:
- Zeigt professionelle Python-Projekt-Organisation
- Entspricht Best Practices
- Erleichtert spätere Erweiterungen
- Klarer für Reviewer/Betreuer

**Minimal-Änderung** ist OK wenn:
- Zeit knapp ist
- Fokus auf Inhalt statt Struktur
- Nur kleine Refactorings gewünscht
