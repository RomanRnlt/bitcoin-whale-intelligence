# Blockchair Integration Guide

Vollständiger Guide zur Integration von lokalen Blockchair-Daten in dein Projekt.

## 📋 Übersicht

Du hast jetzt **3 Datenquellen-Optionen**:

1. **Demo-Daten** - Kleine Beispieldaten (kein Setup)
2. **Google BigQuery** - Cloud, vollständige Blockchain (benötigt Credentials)
3. **Blockchair Local** - Lokal auf SSD, Jahr 2021 (neu!)

---

## 🎯 Warum Jahr 2021?

### Spannende Markt-Events

**Bull Run Peak:**
- Bitcoin All-Time-High: ~$69,000 (November 2021)
- Extreme Whale-Aktivität während Preisbewegungen
- El Salvador macht Bitcoin zum gesetzlichen Zahlungsmittel (September)

**Institutionelle Adoption:**
- MicroStrategy: Mehrere Käufe, insgesamt >100,000 BTC
- Tesla: $1.5 Milliarden Investment (Februar)
- Viele weitere Corporate Treasuries steigen ein

**Markt-Drama:**
- **Mai:** China Mining Ban → Hash-Rate bricht ein → Massive Pool-Verschiebungen
- Elon Musk Tweet-Saga → Extreme Volatilität
- **November:** Taproot Upgrade aktiviert

### Technische Vorteile

- Vollständige Blockchair-Coverage
- Moderate Datengröße (~500GB unkomprimiert)
- Repräsentativ für moderne Bitcoin-Nutzung
- Viele Multi-Input-Transaktionen (gut für Clustering)

---

## 🚀 Quick Start

### 1. Automatischer Download (Einfachste Methode)

```bash
# Einfach Script ausführen
./download_2021_data.sh /Volumes/MySSD/bitcoin_data
```

Das Script:
- Lädt automatisch Jahr 2021 herunter
- Entpackt alle .gz Dateien
- Löscht .gz nach Extraktion (spart Speicher)
- Zeigt Fortschritt an
- Dauert ~2-6 Stunden (je nach Internet)

### 2. Manueller Download (Mehr Kontrolle)

**Komplettes Jahr 2021:**
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --output /Volumes/MySSD/bitcoin_data \
  --remove-gz \
  --workers 6
```

**Nur ein Monat (zum Testen):**
```bash
python scripts/download_blockchair.py \
  --year 2021 \
  --month 1 \
  --output /Volumes/MySSD/bitcoin_data \
  --remove-gz
```

**Spezifischer Zeitraum:**
```bash
python scripts/download_blockchair.py \
  --date-range 2021-04-01 2021-06-30 \
  --output /Volumes/MySSD/bitcoin_data \
  --remove-gz
```

### 3. Daten testen

```bash
python scripts/load_blockchair_data.py \
  --data-dir /Volumes/MySSD/bitcoin_data/extracted \
  --start-date 2021-01-01 \
  --end-date 2021-01-01
```

---

## 📊 Daten in Notebooks verwenden

### In neuem Notebook (empfohlen)

Öffne: `notebooks/02_local_data_exploration.ipynb`

```python
from scripts.load_blockchair_data import BlockchairDataLoader

# Pfad anpassen!
loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")

# Daten laden (eine Woche)
df = loader.load_transactions("2021-01-01", "2021-01-07")
df.show(10)

# Multi-Input-Transaktionen (für Clustering)
df_multi = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
```

### In bestehendem Notebook

Füge am Anfang hinzu:

```python
# ============================================================================
# KONFIGURATION: Datenquelle wählen
# ============================================================================

USE_DEMO = False
USE_BIGQUERY = False
USE_BLOCKCHAIR = True  # NEU!

if USE_BLOCKCHAIR:
    from scripts.load_blockchair_data import BlockchairDataLoader

    loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted", spark=spark)
    df_transactions = loader.load_transactions("2021-01-01", "2021-01-07")

elif USE_BIGQUERY:
    # BigQuery Code...

elif USE_DEMO:
    # Demo Code...
```

### SQL Queries

```python
# Temp Views erstellen
loader.create_temp_views("2021-01-01", "2021-01-07")

# SQL ausführen
spark.sql("""
    SELECT
        date,
        COUNT(*) as tx_count,
        AVG(input_count) as avg_inputs
    FROM transactions
    WHERE input_count >= 2
    GROUP BY date
    ORDER BY date
""").show()
```

---

## 💾 Speicherplatz-Management

### Geschätzte Größen

**Komplettes Jahr 2021:**
- Komprimiert (.gz): ~120-150 GB
- Unkomprimiert (.tsv): ~450-550 GB
- **Mit `--remove-gz`:** ~450-550 GB total ✅
- **Ohne `--remove-gz`:** ~600-700 GB total

**Nur ein Monat:**
- Komprimiert: ~10-15 GB
- Unkomprimiert: ~40-50 GB

### Speicher sparen

**Option 1: .gz löschen**
```bash
# Beim Download
python scripts/download_blockchair.py --year 2021 --remove-gz --output /path

# Nachträglich manuell
rm -rf /Volumes/MySSD/bitcoin_data/raw/
```

**Option 2: Nur wichtige Tabellen**
```bash
# Nur transactions (wichtigste Tabelle für Clustering)
python scripts/download_blockchair.py \
  --year 2021 \
  --tables transactions \
  --output /path
```

**Option 3: Kleinerer Zeitraum**
```bash
# Nur Q1 2021 (spannendster Zeitraum)
python scripts/download_blockchair.py \
  --date-range 2021-01-01 2021-03-31 \
  --output /path
```

**Option 4: Zu Parquet konvertieren (für wiederholte Nutzung)**
```python
# Einmalig konvertieren (kleiner und schneller)
df = loader.load_transactions("2021-01-01", "2021-12-31")
df.write.parquet("/Volumes/MySSD/bitcoin_data/parquet/transactions_2021.parquet")

# Dann .tsv Dateien löschen
# Später ~5x schneller laden:
df = spark.read.parquet("/Volumes/MySSD/bitcoin_data/parquet/transactions_2021.parquet")
```

---

## 🔄 Verzeichnisstruktur

Nach Download:

```
/Volumes/MySSD/bitcoin_data/
├── raw/                          # .gz Dateien (optional)
│   ├── blocks/
│   │   ├── blockchair_bitcoin_blocks_2021-01-01.tsv.gz
│   │   └── ...
│   ├── transactions/
│   └── outputs/
│
├── extracted/                    # .tsv Dateien (werden geladen)
│   ├── blocks/
│   │   ├── blockchair_bitcoin_blocks_2021-01-01.tsv
│   │   ├── blockchair_bitcoin_blocks_2021-01-02.tsv
│   │   └── ...
│   ├── transactions/
│   │   ├── blockchair_bitcoin_transactions_2021-01-01.tsv
│   │   └── ...
│   └── outputs/
│       ├── blockchair_bitcoin_outputs_2021-01-01.tsv
│       └── ...
│
└── parquet/                      # Optional: Konvertierte Daten
    ├── transactions_2021.parquet
    └── outputs_2021.parquet
```

---

## 📚 Verfügbare Tabellen

### 1. Blocks

**Schema:** Block-Metadaten (Timestamp, Size, Transaction Count)

**Verwendung:**
```python
df_blocks = loader.load_blocks("2021-01-01", "2021-01-07")
```

**Wichtige Spalten:**
- `id`: Block-Nummer
- `time`: Timestamp
- `transaction_count`: Anzahl Transaktionen
- `difficulty`: Mining-Difficulty

### 2. Transactions

**Schema:** Alle Bitcoin-Transaktionen

**Verwendung:**
```python
df_tx = loader.load_transactions("2021-01-01", "2021-01-07")

# Ohne Coinbase
df_tx = loader.load_transactions("2021-01-01", "2021-01-07", filter_coinbase=True)

# Nur Multi-Input (für Clustering)
df_multi = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
```

**Wichtige Spalten:**
- `hash`: Transaction Hash
- `input_count`: Anzahl Inputs
- `output_count`: Anzahl Outputs
- `input_total`: Gesamtwert Inputs (Satoshis)
- `output_total`: Gesamtwert Outputs (Satoshis)
- `fee`: Transaction Fee (Satoshis)
- `is_coinbase`: Boolean

### 3. Outputs (UTXOs)

**Schema:** Alle Transaction Outputs (UTXOs)

**Verwendung:**
```python
df_outputs = loader.load_outputs("2021-01-01", "2021-01-07")

# Nur unverbrauchte UTXOs
df_utxos = loader.load_outputs("2021-01-01", "2021-01-07", unspent_only=True)
```

**Wichtige Spalten:**
- `transaction_hash`: Zu welcher TX gehört dieser Output
- `index`: Position in der Transaction
- `value`: Wert in Satoshis
- `recipient`: Bitcoin-Adresse
- `is_spent`: Boolean (wurde ausgegeben?)
- `spending_transaction_hash`: Hash der TX die diesen Output ausgegeben hat

---

## ⚡ Performance-Tipps

### Download beschleunigen

```bash
# Mehr parallele Downloads (wenn Internet schnell)
python scripts/download_blockchair.py --year 2021 --workers 8 --output /path

# Ohne Extraktion während Download (schneller)
python scripts/download_blockchair.py --year 2021 --no-extract --output /path
# Dann später extrahieren:
gunzip /path/raw/*/*.gz
```

### Laden in Spark beschleunigen

**Tipp 1: Kleinere Zeiträume**
```python
# Statt ganzen Monat
df = loader.load_transactions("2021-01-01", "2021-01-31")

# Besser: Wochenweise
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

**Tipp 2: Filter früh anwenden**
```python
# Gut: Filter beim Laden
df = loader.load_transactions("2021-01-01", "2021-01-07", filter_coinbase=True)

# Besser: Nur relevante Daten
df = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
```

**Tipp 3: Zu Parquet konvertieren**
```python
# Einmalig: TSV → Parquet (deutlich schneller)
df = loader.load_transactions("2021-01-01", "2021-12-31")
df.write.mode("overwrite").parquet("/path/parquet/transactions_2021.parquet")

# Später ~5-10x schneller:
df = spark.read.parquet("/path/parquet/transactions_2021.parquet")
```

---

## 🔍 Datenqualität & Unterschiede zu BigQuery

### Was ist gleich?

- Gleiche Blockchain-Daten
- Gleiche Transaktionen
- Gleiche UTXOs
- Gleiche Konzepte (Multi-Input, etc.)

### Was ist anders?

| Aspekt | BigQuery | Blockchair Local |
|--------|----------|-----------------|
| **Zeitraum** | 2009-heute | Nur heruntergeladene Periode (z.B. 2021) |
| **Aktualisierung** | Täglich | Manuell (neuer Download) |
| **Kosten** | Scan-basiert ($5/TB) | Einmalig: Internet/Speicher |
| **Geschwindigkeit** | Variabel (Cloud) | Schnell (lokal) |
| **Schema** | BigQuery-optimiert | Blockchair-Format |
| **Verfügbarkeit** | Internet nötig | Offline möglich |

### Schema-Unterschiede

**BigQuery:**
- `block_timestamp` (Timestamp)
- `addresses` (Array von Strings)
- Werte oft als NUMERIC

**Blockchair:**
- `time` (Timestamp)
- `recipient` (String, einzelne Adresse)
- Werte als BIGINT (Satoshis)

**Lösung:** Der `BlockchairDataLoader` mapped alles automatisch auf PySpark-kompatible Typen!

---

## 🚨 Troubleshooting

### Problem: Download schlägt fehl

**Symptom:** HTTP 404 Fehler für manche Tage

**Lösung:** Normal! Blockchair hat nicht für jeden Tag Daten verfügbar. Script überspringt automatisch.

### Problem: Zu langsam

**Lösung:**
```bash
# Mehr Workers (wenn Internet schnell)
python scripts/download_blockchair.py --year 2021 --workers 8 --output /path
```

### Problem: Spark Memory Error

**Symptom:** `OutOfMemoryError` beim Laden

**Lösung 1:** Kleinere Zeiträume
```python
# Statt ganzen Monat → nur eine Woche
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

**Lösung 2:** Mehr Spark Memory
```python
spark = SparkSession.builder \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()
```

**Lösung 3:** Nur relevante Spalten laden
```python
df = loader.load_transactions("2021-01-01", "2021-01-07")
df = df.select("hash", "input_count", "output_count", "fee")  # Nur was du brauchst
```

### Problem: .tsv Dateien fehlen

**Symptom:** `ValueError: Keine transactions-Daten gefunden`

**Lösung:** Prüfe ob Extraktion funktioniert hat
```bash
# Prüfe ob .tsv Dateien da sind
ls /Volumes/MySSD/bitcoin_data/extracted/transactions/

# Falls nur .gz: Manuell entpacken
gunzip /Volumes/MySSD/bitcoin_data/raw/transactions/*.gz
mv /Volumes/MySSD/bitcoin_data/raw/transactions/*.tsv /Volumes/MySSD/bitcoin_data/extracted/transactions/
```

---

## 📈 Use Cases

### Use Case 1: Entity-Clustering entwickeln

```python
# Lade nur Multi-Input-Transactions (2-50 Inputs)
df_multi = loader.get_multi_input_transactions(
    "2021-01-01", "2021-01-31",
    min_inputs=2,
    max_inputs=50
)

# Jetzt GraphFrames Connected Components darauf anwenden
# (Siehe Notebook 02: Entity Clustering)
```

### Use Case 2: Whale-Detection testen

```python
# Lade Outputs (UTXOs) für Januar
df_outputs = loader.load_outputs("2021-01-01", "2021-01-31", unspent_only=True)

# Aggregiere nach Adresse
from pyspark.sql.functions import sum as spark_sum

df_balances = df_outputs.groupBy("recipient") \
    .agg(spark_sum("value").alias("balance")) \
    .orderBy("balance", ascending=False)

df_balances.show(20)
```

### Use Case 3: Zeitreihen-Analyse

```python
# Lade tägliche Transactions für Q1 2021
from datetime import datetime, timedelta

start = datetime(2021, 1, 1)
for i in range(90):  # 90 Tage
    date = start + timedelta(days=i)
    date_str = date.strftime("%Y-%m-%d")

    df = loader.load_transactions(date_str, date_str)

    # Analysiere Tag
    stats = df.select(
        avg("input_count"),
        avg("fee"),
        count("*")
    ).collect()[0]

    print(f"{date_str}: {stats}")
```

---

## 🎯 Nächste Schritte

1. **Download starten:**
   ```bash
   ./download_2021_data.sh /Volumes/MySSD/bitcoin_data
   ```

2. **Testen:**
   ```bash
   python scripts/load_blockchair_data.py \
     --data-dir /Volumes/MySSD/bitcoin_data/extracted \
     --start-date 2021-01-01 \
     --end-date 2021-01-01
   ```

3. **Notebook öffnen:**
   ```bash
   ./start_project.sh
   # Dann: notebooks/02_local_data_exploration.ipynb
   ```

4. **Für Projekt nutzen:**
   - Notebook 02: Entity-Clustering mit lokalen Daten entwickeln
   - Notebook 03: Whale-Detection testen
   - Notebook 04: Zeitreihen-Analyse für 2021 Bull-Run

---

## 📚 Weitere Ressourcen

- **Blockchair API Docs:** https://blockchair.com/api/docs
- **Blockchair Dumps:** https://gz.blockchair.com/bitcoin/
- **Script README:** [scripts/README.md](../scripts/README.md)
- **Beispiel-Notebook:** [notebooks/02_local_data_exploration.ipynb](../notebooks/02_local_data_exploration.ipynb)

---

**Viel Erfolg beim Whale-Hunting! 🐋**
