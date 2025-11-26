# Bitcoin Blockchain Data Scripts

Tools zum Download und Laden von Bitcoin Blockchain-Daten.

---

## 📥 Download Tool (GUI)

### Verwendung

**Starte die GUI:**
```bash
python scripts/download_bitcoin_data.py
```

### Features

✅ **User-friendly GUI**
- Grafische Oberfläche (macOS, Windows, Linux)
- Kein Command-Line-Wissen nötig
- Intuitive Bedienung

✅ **Pause/Resume**
- Download jederzeit pausieren
- GUI schließen und später fortsetzen
- Automatische Erkennung unvollständiger Downloads

✅ **State Persistence**
- Speichert Konfiguration in `.download_state.json`
- Merkt sich: Pfad, Zeitraum, Tabellen, Einstellungen
- Auto-Resume beim nächsten Start

✅ **Fortschrittsanzeige**
- Overall Progress: "File 23/365 (6.3%)"
- Current File Progress: "45.2% (67.8/150 MB)"
- ETA Berechnung: "Verbleibende Zeit: 2h 35m"

✅ **Failsafe**
- Bereits heruntergeladene Files werden übersprungen
- Kein Datenverlust bei Abbruch
- Kann jederzeit fortgesetzt werden

### Workflow

1. **GUI starten**
   ```bash
   python scripts/download_bitcoin_data.py
   ```

2. **Konfigurieren**
   - Output Directory wählen (z.B. `/Volumes/MySSD/bitcoin_data`)
   - Zeitraum eingeben (z.B. `2021-01-01` bis `2021-12-31`)
   - Tabellen auswählen (blocks, transactions, outputs)
   - "Calculate Size" klicken → Größe prüfen

3. **Download starten**
   - "Start Download" klicken
   - Optional: Pausieren mit "Pause" Button
   - Optional: GUI schließen und später fortsetzen

4. **Auto-Resume**
   - GUI neu starten
   - Popup: "Resume Download? Yes/No"
   - Klick auf "Yes" → Weitermachen wo du aufgehört hast

### Speicherplatz-Abschätzung

| Zeitraum | Größe (unkomprimiert) |
|----------|----------------------|
| 1 Tag    | ~1.3 GB              |
| 1 Woche  | ~9 GB                |
| 1 Monat  | ~40 GB               |
| Q1 2021  | ~120 GB              |
| Jahr 2021| ~480 GB              |

**Hinweis:** .gz-Files werden standardmäßig nach Extraktion gelöscht (spart ~70% Platz)

---

## 📊 Data Loader (Python Library)

### Installation

Der Loader ist bereits Teil des Projekts:
```python
from src.loaders.blockchair import BlockchairDataLoader
```

### Verwendung in Notebooks

**Einfachste Methode (empfohlen):**
```python
from src.data_config import DataConfig, load_data

# Config
config = DataConfig(source="local")  # Auto-detect Pfad

# Daten laden
df = load_data(config, "2021-01-01", "2021-01-07", spark=spark)
df.show()
```

**Direkte Loader-Verwendung:**
```python
from src.loaders.blockchair import BlockchairDataLoader

# Initialisiere Loader
loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")

# Lade Transaktionen
df_transactions = loader.load_transactions("2021-01-01", "2021-01-07")
df_transactions.show()

# Lade nur Multi-Input-Transaktionen (für Entity-Clustering)
df_multi = loader.get_multi_input_transactions(
    "2021-01-01", "2021-01-07",
    min_inputs=2,
    max_inputs=50
)
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

---

## 🔄 Integration mit Notebooks

### Datenquellen-Switching

In deinen Notebooks kannst du einfach zwischen 3 Datenquellen wechseln:

```python
from src.data_config import DataConfig, load_data

# WÄHLE EINE OPTION:

# Option 1: Demo-Daten (klein, schnell, kein Setup)
config = DataConfig(source="demo")

# Option 2: BigQuery (Cloud, vollständig)
config = DataConfig(source="bigquery")

# Option 3: Lokale Blockchair-Daten (heruntergeladen)
config = DataConfig(source="local")  # Auto-detect Pfad
# Oder manuell:
# config = DataConfig(source="local", local_data_path="/Volumes/MySSD/bitcoin_data/extracted")

# Daten laden (funktioniert mit allen 3 Quellen!)
df = load_data(config, "2021-01-01", "2021-01-07", spark=spark)
```

### Verzeichnisstruktur nach Download

```
/Volumes/MySSD/bitcoin_data/
├── raw/                          # .gz Dateien (wird automatisch gelöscht)
│   ├── blocks/
│   ├── transactions/
│   └── outputs/
├── extracted/                    # .tsv Dateien (werden geladen) ⭐
│   ├── blocks/
│   │   ├── blockchair_bitcoin_blocks_2021-01-01.tsv
│   │   └── ...
│   ├── transactions/
│   │   ├── blockchair_bitcoin_transactions_2021-01-01.tsv
│   │   └── ...
│   └── outputs/
│       └── ...
└── .download_state.json          # State für Resume (automatisch)
```

---

## 📌 Warum Jahr 2021?

**Bull Run Peak:**
- Bitcoin All-Time-High (~$69k im November)
- Extreme Whale-Aktivität
- El Salvador Bitcoin-Adoption (September)

**Institutionelle Adoption:**
- MicroStrategy massive Käufe
- Tesla Investment ($1.5B)
- Corporate Treasuries steigen ein

**Markt-Events:**
- China Mining Ban (Mai) → Hash-Rate Crash
- Elon Musk Tweet-Drama → Volatilität
- Taproot Upgrade (November)

**Daten-Qualität:**
- Vollständige Blockchair-Coverage
- Moderate Größe (~500GB)
- Repräsentativ für moderne Bitcoin-Nutzung

---

## ⚠️ Troubleshooting

### GUI startet nicht

**Problem:** `ModuleNotFoundError: No module named 'tkinter'`

**Lösung:**
```bash
# macOS
brew install python-tk

# Linux
sudo apt-get install python3-tk

# Windows: Normalerweise vorinstalliert
```

### Download zu langsam

**Ursache:** Blockchair-Server oder langsames Internet

**Lösung:**
- Kleineren Zeitraum wählen (z.B. nur Q1 statt ganzes Jahr)
- Zu anderer Tageszeit versuchen
- Nur wichtigste Tabelle: transactions

### Zu wenig Speicherplatz

**Lösungen:**
1. Kleinerer Zeitraum (Monat statt Jahr)
2. Nur transactions-Tabelle (wichtigste für Entity-Clustering)
3. Remove .gz aktiviert lassen (Standard, spart ~70%)

### Download bricht ab

**Lösung:** Einfach GUI neu starten!
- Bereits heruntergeladene Files werden erkannt
- Automatische Resume-Funktion
- Kein Datenverlust

---

## 📈 Performance-Tipps

### Schnelleres Laden in Spark

**1. Kleinere Zeiträume:**
```python
# Statt ganzer Monat
df = loader.load_transactions("2021-01-01", "2021-01-31")

# Besser: Wochenweise
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

**2. Parquet konvertieren (für wiederholte Nutzung):**
```python
# Einmalig: TSV → Parquet
df = loader.load_transactions("2021-01-01", "2021-12-31")
df.write.parquet("/path/parquet/transactions_2021.parquet")

# Später ~5x schneller:
df = spark.read.parquet("/path/parquet/transactions_2021.parquet")
```

**3. Nur benötigte Spalten:**
```python
df = df.select("hash", "input_count", "output_count", "fee")
```

**4. Filter früh anwenden:**
```python
# Nur Multi-Input-Transaktionen laden
df = loader.get_multi_input_transactions("2021-01-01", "2021-01-07")
```

---

## 📚 Weitere Informationen

- **Download-Guide:** `docs/DOWNLOAD_GUIDE.md`
- **Blockchair Integration:** `docs/BLOCKCHAIR_INTEGRATION.md`
- **Quickstart:** `docs/BLOCKCHAIR_QUICKSTART.txt`
- **Blockchair API:** https://blockchair.com/api/docs
- **Blockchair Dumps:** https://gz.blockchair.com/bitcoin/
