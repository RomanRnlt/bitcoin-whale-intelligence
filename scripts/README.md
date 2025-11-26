# Blockchair Data Scripts

Automatisierter Download und Integration von Blockchair Bitcoin Blockchain Dumps.

## 📥 Download Script

### Installation

```bash
pip install requests tqdm
```

### Verwendung

**Komplettes Jahr herunterladen (empfohlen: 2021):**
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --output /Volumes/MySSD/bitcoin_data \
  --remove-gz
```

**Nur ein Monat:**
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --month 1 \
  --output /Volumes/MySSD/bitcoin_data
```

**Spezifischer Zeitraum:**
```bash
python scripts/download_blockchair.py \
  --date-range 2021-01-01 2021-03-31 \
  --output /Volumes/MySSD/bitcoin_data
```

**Nur spezifische Tabellen:**
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --tables transactions outputs \
  --output /Volumes/MySSD/bitcoin_data
```

### Optionen

- `--no-extract`: Nur download, keine Extraktion (schneller, aber .gz bleibt)
- `--remove-gz`: .gz nach Extraktion löschen (spart ~70% Speicher)
- `--sequential`: Sequenziell statt parallel (langsamer, aber stabiler)
- `--workers N`: Anzahl paralleler Downloads (default: 4)

### Speicherplatz-Abschätzung

**Jahr 2021:**
- Komprimiert (.gz): ~120-150 GB
- Unkomprimiert (.tsv): ~450-550 GB
- Mit `--remove-gz`: ~450-550 GB total
- Ohne `--remove-gz`: ~600-700 GB total

**Monat 2021:**
- Komprimiert: ~10-15 GB
- Unkomprimiert: ~40-50 GB

---

## 📊 Data Loader Script

### Verwendung in Python/Notebook

```python
from scripts.load_blockchair_data import BlockchairDataLoader

# Initialisiere Loader
loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")

# Lade Transaktionen für eine Woche
df_transactions = loader.load_transactions("2021-01-01", "2021-01-07")
df_transactions.show()

# Lade Multi-Input-Transaktionen (für Entity-Clustering)
df_multi = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
print(f"Multi-Input Transactions: {df_multi.count():,}")

# Lade Outputs (UTXOs)
df_outputs = loader.load_outputs("2021-01-01", "2021-01-07", unspent_only=True)

# Lade Blocks
df_blocks = loader.load_blocks("2021-01-01", "2021-01-07")
```

### SQL Queries (via Temp Views)

```python
# Erstelle SQL Views
loader.create_temp_views("2021-01-01", "2021-01-07")

# Jetzt SQL-Queries ausführen
spark.sql("""
    SELECT
        hash,
        input_count,
        output_count,
        fee / 100000000 as fee_btc
    FROM transactions
    WHERE input_count >= 5
    ORDER BY input_count DESC
    LIMIT 10
""").show()
```

### Alle Daten auf einmal laden

```python
from scripts.load_blockchair_data import load_blockchair_data

data = load_blockchair_data(
    data_dir="/Volumes/MySSD/bitcoin_data/extracted",
    start_date="2021-01-01",
    end_date="2021-01-07"
)

df_blocks = data['blocks']
df_transactions = data['transactions']
df_outputs = data['outputs']
```

---

## 🔄 Integration mit bestehendem Projekt

### 1. Verzeichnisstruktur nach Download

```
/Volumes/MySSD/bitcoin_data/
├── raw/                          # .gz Dateien (optional, mit --remove-gz gelöscht)
│   ├── blocks/
│   ├── transactions/
│   └── outputs/
└── extracted/                    # .tsv Dateien (werden geladen)
    ├── blocks/
    │   ├── blockchair_bitcoin_blocks_2021-01-01.tsv
    │   ├── blockchair_bitcoin_blocks_2021-01-02.tsv
    │   └── ...
    ├── transactions/
    │   ├── blockchair_bitcoin_transactions_2021-01-01.tsv
    │   └── ...
    └── outputs/
        ├── blockchair_bitcoin_outputs_2021-01-01.tsv
        └── ...
```

### 2. In Notebooks verwenden

Siehe `notebooks/02_local_data_exploration.ipynb` (neu erstellt) für vollständiges Beispiel.

**Kurz-Version:**

```python
# Am Anfang des Notebooks
from scripts.load_blockchair_data import BlockchairDataLoader

# Pfad zu deiner SSD
DATA_DIR = "/Volumes/MySSD/bitcoin_data/extracted"

# Loader initialisieren
loader = BlockchairDataLoader(DATA_DIR)

# Daten laden
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

### 3. Switching zwischen Datenquellen

Du kannst jetzt in deinen Notebooks zwischen 3 Modi wählen:

```python
# Option 1: Demo-Daten (klein, schnell)
USE_DEMO = True

# Option 2: BigQuery (Cloud, vollständig)
USE_BIGQUERY = True
USE_DEMO = False

# Option 3: Lokale Blockchair-Daten (SSD, 2021 nur)
USE_BLOCKCHAIR = True
USE_DEMO = False
USE_BIGQUERY = False

if USE_DEMO:
    # Demo-Daten aus Code
    df = create_demo_data()
elif USE_BIGQUERY:
    # BigQuery
    df = client.query(query).to_dataframe()
elif USE_BLOCKCHAIR:
    # Lokale Daten
    loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")
    df = loader.load_transactions("2021-01-01", "2021-01-07")
```

---

## 🚀 Quick Start Guide

### Schritt 1: Download Daten

```bash
# Terminal öffnen, zu Projekt navigieren
cd /Users/roman/spark_project/bitcoin-whale-intelligence

# Jahr 2021 herunterladen (dauert 2-4 Stunden je nach Internet)
python scripts/download_blockchair.py \
  --year 2021 \
  --output /Volumes/MySSD/bitcoin_data \
  --remove-gz \
  --workers 6
```

**Tipp:** Mit `--workers 6` kannst du mehr parallel laden (wenn dein Internet schnell ist).

### Schritt 2: Daten testen

```bash
# Test ob Daten korrekt geladen werden können
python scripts/load_blockchair_data.py \
  --data-dir /Volumes/MySSD/bitcoin_data/extracted \
  --start-date 2021-01-01 \
  --end-date 2021-01-01
```

### Schritt 3: In Notebook verwenden

```bash
# Jupyter starten
./start_project.sh

# Dann neues Notebook öffnen: notebooks/02_local_data_exploration.ipynb
```

---

## 📌 Warum Jahr 2021?

**Bull Run Peak:**
- Bitcoin erreichte All-Time-High (~$69k im November)
- Extreme Whale-Aktivität während Preisbewegungen
- El Salvador Bitcoin-Adoption (September)

**Institutionelle Adoption:**
- MicroStrategy massive Käufe
- Tesla Investment ($1.5B im Februar)
- Viele Corporate Treasuries steigen ein

**Markt-Events:**
- China Mining Ban (Mai) → Hash-Rate Crash → Pool-Verschiebungen
- Elon Musk Tweet-Drama → Massive Volatilität
- Taproot Upgrade (November) → Technische Veränderung

**Daten-Qualität:**
- Vollständige Blockchair-Coverage
- Moderate Größe (~500GB unkomprimiert)
- Repräsentativ für moderne Bitcoin-Nutzung

**Alternative Zeiträume:**
- **2017:** ICO-Boom, erste große Bull-Run (~100GB)
- **2020:** COVID-Crash + Recovery (~120GB)
- **2023:** Ordinals/Inscriptions Hype (~150GB)

---

## ⚠️ Troubleshooting

### Download schlägt fehl

**Problem:** HTTP 404 Fehler für manche Tage

**Lösung:** Normal! Blockchair hat nicht für jeden Tag Daten. Script überspringt automatisch.

### Zu langsam

**Lösung:**
```bash
# Mehr parallele Downloads
python scripts/download_blockchair.py --year 2021 --workers 8 --output /path
```

### Zu wenig Speicherplatz

**Option 1:** Kleinerer Zeitraum
```bash
# Nur Q1 2021
python scripts/download_blockchair.py \
  --date-range 2021-01-01 2021-03-31 \
  --output /path
```

**Option 2:** Nur wichtige Tabellen
```bash
# Nur transactions (wichtigste Tabelle)
python scripts/download_blockchair.py \
  --year 2021 \
  --tables transactions \
  --output /path
```

**Option 3:** Mit --remove-gz (spart ~70% Platz)
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --remove-gz \
  --output /path
```

### Spark läuft nicht mit lokalen Daten

**Problem:** Memory Error beim Laden großer Zeiträume

**Lösung:** Kleinere Zeiträume laden
```python
# Statt ganzer Monat
loader.load_transactions("2021-01-01", "2021-01-31")

# Besser: Wochenweise
loader.load_transactions("2021-01-01", "2021-01-07")
```

---

## 📈 Performance-Tipps

### Schnellerer Download

1. **Mehr Workers:** `--workers 8` (wenn Internet schnell)
2. **Keine Extraktion während Download:** `--no-extract`, dann später extrahieren
3. **Nur benötigte Tabellen:** `--tables transactions outputs`

### Schnelleres Laden in Spark

1. **Parquet konvertieren** (optional, für wiederholte Nutzung):
```python
df = loader.load_transactions("2021-01-01", "2021-12-31")
df.write.parquet("/Volumes/MySSD/bitcoin_data/parquet/transactions_2021.parquet")

# Später deutlich schneller:
df = spark.read.parquet("/Volumes/MySSD/bitcoin_data/parquet/transactions_2021.parquet")
```

2. **Kleinere Zeiträume:** Wochenweise statt monatsweise laden

3. **Filter früh anwenden:**
```python
# Gut: Filter direkt beim Laden
df = loader.load_transactions("2021-01-01", "2021-01-07", filter_coinbase=True)

# Noch besser: Nur Multi-Input laden
df = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
```

---

## 📚 Weitere Informationen

- **Blockchair Dokumentation:** https://blockchair.com/dumps
- **Schema-Referenz:** https://blockchair.com/api/docs#link_M03
- **Bitcoin Timestamps:** Alle Zeiten in UTC
