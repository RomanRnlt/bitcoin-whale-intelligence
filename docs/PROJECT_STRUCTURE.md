# Bitcoin Whale Intelligence - Projekt-Struktur

## Übersicht

Dieses Projekt folgt Python Best Practices mit klarer Trennung zwischen Library-Code, Tools und Dokumentation.

```
bitcoin-whale-intelligence/
├── README.md                   # Haupt-Dokumentation
├── requirements.txt            # Python Dependencies
├── .env.example                # Environment-Variablen Template
├── .gitignore                  # Git-Konfiguration
│
├── start_project.sh            # Convenience: Jupyter starten
├── download_2021_data.sh       # Convenience: Daten downloaden
│
├── src/                        # 📦 Python Package (Library-Code)
│   ├── __init__.py             # Package exports
│   ├── data_config.py          # Datenquellen-Konfiguration
│   ├── loaders/                # Data Loader
│   │   ├── __init__.py
│   │   └── blockchair.py       # Blockchair TSV Loader
│   └── utils/                  # Utility-Funktionen (zukünftig)
│       └── __init__.py
│
├── scripts/                    # 🔧 Ausführbare Tools
│   ├── download_bitcoin_data.py    # GUI Download Tool
│   └── download_blockchair.py      # CLI Download Tool (Legacy)
│
├── notebooks/                  # 📓 Jupyter Notebooks
│   ├── 00_test_bigquery_connection.ipynb
│   └── 01_data_exploration.ipynb
│
├── docs/                       # 📚 Dokumentation
│   ├── SETUP.md                # Setup-Anleitung
│   ├── DOWNLOAD_GUIDE.md       # Download-Guide
│   ├── BLOCKCHAIR_INTEGRATION.md
│   ├── BLOCKCHAIR_QUICKSTART.txt
│   ├── PROJECT_CONTEXT.md
│   ├── NOTEBOOK_WORKFLOW.md
│   ├── SIMPLE_EXPLANATION.md
│   ├── INTEGRATION_SUMMARY.md
│   ├── STRUCTURE_PROPOSAL.md
│   └── PROJECT_STRUCTURE.md    # Diese Datei
│
├── data/                       # 💾 Lokale Daten (gitignored)
│   ├── raw/                    # Rohdaten
│   ├── processed/              # Prozessierte Daten
│   └── sample/                 # Beispieldaten
│
└── tests/                      # 🧪 Unit-Tests
    └── __init__.py
```

## Hauptkomponenten

### 1. `src/` - Python Package

**Zweck:** Wiederverwendbarer Library-Code

**Import-Beispiele:**
```python
from src.data_config import DataConfig, load_data
from src.loaders.blockchair import BlockchairDataLoader
```

**Dateien:**
- `data_config.py`: Zentrale Konfiguration für Datenquellen (demo/bigquery/local)
- `loaders/blockchair.py`: PySpark-Loader für Blockchair TSV-Dumps

### 2. `scripts/` - Ausführbare Tools

**Zweck:** Standalone-Tools die direkt ausgeführt werden

**Tools:**
- `download_bitcoin_data.py`: GUI-Tool zum Herunterladen von Blockchain-Daten
  ```bash
  python scripts/download_bitcoin_data.py
  ```

- `download_blockchair.py`: CLI-Version (Legacy, für Scripting)
  ```bash
  python scripts/download_blockchair.py --year 2021 --output /path/to/data
  ```

### 3. `notebooks/` - Jupyter Notebooks

**Zweck:** Interaktive Datenanalyse

**Notebooks:**
- `00_test_bigquery_connection.ipynb`: BigQuery-Verbindungstest
- `01_data_exploration.ipynb`: Hauptnotebook für Daten-Exploration

**Verwendung:**
```bash
./start_project.sh  # Startet Jupyter
```

### 4. `docs/` - Dokumentation

**Zweck:** Alle Projektdokumentation an einem Ort

**Wichtige Dokumente:**
- `SETUP.md`: Installations- und Setup-Anleitung
- `DOWNLOAD_GUIDE.md`: Kompletter Guide zum Daten-Download
- `BLOCKCHAIR_QUICKSTART.txt`: Schnellstart-Referenz
- `PROJECT_CONTEXT.md`: Projekt-Kontext und Ziele

## Workflow-Beispiele

### Daten herunterladen

**Option 1: GUI (empfohlen)**
```bash
python scripts/download_bitcoin_data.py
```

**Option 2: Automatisches Jahr 2021**
```bash
./download_2021_data.sh /Volumes/MySSD/bitcoin_data
```

### In Notebooks verwenden

```python
# In Jupyter Notebook
from src.data_config import DataConfig, load_data

# Datenquelle wählen
config = DataConfig(source="local")  # oder "bigquery" oder "demo"

# Daten laden
df = load_data(config, "2021-01-01", "2021-01-07", spark=spark)
df.show()
```

### Erweiterte Nutzung (Loader direkt)

```python
from src.loaders.blockchair import BlockchairDataLoader

loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

## Vorteile dieser Struktur

1. **Sauber & Professionell**
   - Entspricht Python Best Practices
   - Klare Trennung von Concerns
   - Einfach zu navigieren

2. **Skalierbar**
   - Neue Loader einfach zu `src/loaders/` hinzufügen
   - Neue Utils zu `src/utils/`
   - Neue Scripts zu `scripts/`

3. **Wiederverwendbar**
   - `src/` ist ein richtiges Python Package
   - Import aus anderen Projekten möglich
   - Saubere API-Definitionen in `__init__.py`

4. **Wartbar**
   - Alle Dokumentation in `docs/`
   - Imports klar nachvollziehbar
   - Keine Code-Duplikation

## Best Practices

### Imports

**Innerhalb des Projekts:**
```python
from src.data_config import DataConfig
from src.loaders.blockchair import BlockchairDataLoader
```

**Neue Module hinzufügen:**

1. Code nach `src/` verschieben
2. In entsprechendem `__init__.py` exportieren:
   ```python
   # src/__init__.py
   from .data_config import DataConfig
   from .new_module import NewClass
   
   __all__ = ["DataConfig", "NewClass"]
   ```

### Dateiorganisation

- **Library-Code** → `src/`
- **Executable Scripts** → `scripts/`
- **Dokumentation** → `docs/`
- **Tests** → `tests/`
- **Daten** → `data/` (gitignored)

## Migration von alter Struktur

Falls du Code von der alten Struktur hast:

**Alt:**
```python
from data_config import DataConfig
from scripts.load_blockchair_data import BlockchairDataLoader
```

**Neu:**
```python
from src.data_config import DataConfig
from src.loaders.blockchair import BlockchairDataLoader
```

## Weitere Informationen

- Setup: `docs/SETUP.md`
- Download: `docs/DOWNLOAD_GUIDE.md`
- Integration: `docs/BLOCKCHAIR_INTEGRATION.md`
- Projekt-Kontext: `docs/PROJECT_CONTEXT.md`
