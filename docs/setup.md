# Setup Guide

## Voraussetzungen

- Python 3.11+
- Java 11 (fuer Apache Spark)
- Bitcoin Full Node (fuer Datenexport)

## Quick Start

```bash
# 1. Repo klonen
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence

# 2. Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install -r requirements.txt

# 4. Jupyter starten
./start_project.sh
```

## Blockchain-Daten exportieren

Die Daten werden mit [bitcoin-etl](https://github.com/blockchain-etl/bitcoin-etl) von einem Bitcoin Full Node exportiert:

```bash
# Bitcoin-ETL installieren
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

In `notebooks/01_entity_clustering.ipynb`:

```python
BLOCKCHAIN_DATA_PATH = "/path/to/blockchain_exports"
```

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

## Notebook ausfuehren

1. `./start_project.sh`
2. Browser oeffnet sich mit Jupyter
3. `notebooks/01_entity_clustering.ipynb` oeffnen
4. Alle Zellen ausfuehren (Shift+Enter oder "Run All")

## Troubleshooting

| Problem | Loesung |
|---------|---------|
| "No batch folders found" | BLOCKCHAIN_DATA_PATH pruefen |
| Java nicht gefunden | JAVA_HOME setzen |
| GraphFrames-Fehler | Spark muss Internet-Zugang haben (laedt Pakete) |
| Out of Memory | DRIVER_MEMORY erhoehen (z.B. "16g") |
