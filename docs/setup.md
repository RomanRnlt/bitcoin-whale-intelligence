# Setup Guide

## Voraussetzungen

| Software | Version | Zweck |
|----------|---------|-------|
| Python | 3.11+ | Jupyter, PySpark |
| Java | 11 | Apache Spark Runtime |
| Bitcoin Full Node | optional | Nur fuer eigenen Datenexport |

---

## Quick Start (3 Minuten)

```bash
# 1. Repo klonen
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence

# 2. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Jupyter starten
./start_project.sh
```

---

## Datenquelle: bitcoin-etl

Die Blockchain-Daten werden mit [bitcoin-etl](https://github.com/blockchain-etl/bitcoin-etl) exportiert:

```bash
# bitcoin-etl installieren
pip install bitcoin-etl

# Daten exportieren (Beispiel: H1 2011)
bitcoinetl export_all \
    --provider-uri http://user:pass@localhost:8332 \
    --start 2011-01-01 --end 2011-06-01 \
    --output-dir /path/to/blockchain_exports
```

### Erwartete Verzeichnisstruktur

```
blockchain_exports/
└── 2011-01-01_2011-06-01/
    ├── blocks/
    │   └── date=YYYY-MM-DD/
    │       └── blocks_*.json
    └── transactions/
        └── date=YYYY-MM-DD/
            └── transactions_*.json
```

### Pfad konfigurieren

In `notebooks/01_entity_clustering.ipynb`, Zelle 1:

```python
BLOCKCHAIN_DATA_PATH = "/path/to/blockchain_exports"
```

---

## Java installieren

**macOS:**
```bash
brew install openjdk@11
export JAVA_HOME=$(/usr/libexec/java_home -v 11)
```

**Ubuntu:**
```bash
sudo apt-get install openjdk-11-jdk
```

**Pruefen:**
```bash
java -version
# Sollte: openjdk version "11.x.x" zeigen
```

---

## Notebook ausfuehren

1. `./start_project.sh` (startet Jupyter)
2. Browser oeffnet `notebooks/01_entity_clustering.ipynb`
3. **Run All** (Shift+Enter durch alle Zellen)
4. Warten (ca. 2-5 Minuten fuer H1/2011 Daten)

### Output-Dateien

Nach Ausfuehrung liegen in `data/`:

| Datei | Inhalt |
|-------|--------|
| `outputs.parquet` | Alle TX Outputs (flach) |
| `inputs.parquet` | Alle TX Inputs (flach) |
| `utxos.parquet` | Unspent Outputs |
| `entities.parquet` | Address -> Entity Mapping |

---

## Troubleshooting

| Problem | Loesung |
|---------|---------|
| "No batch folders found" | `BLOCKCHAIN_DATA_PATH` pruefen |
| "Java not found" | `JAVA_HOME` setzen, Java 11 installieren |
| GraphFrames-Fehler | Spark braucht Internet (laedt Pakete) |
| Out of Memory | `DRIVER_MEMORY = "16g"` in Notebook |
| Spark UI nicht erreichbar | Port 4040 evtl. belegt |
