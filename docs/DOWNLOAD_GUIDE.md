# 📥 Bitcoin Blockchain Data Download Guide

Einfache Anleitung zum Herunterladen von Bitcoin-Blockchain-Daten für lokale Analyse.

---

## 🚀 Quick Start

### Schritt 1: Download-Tool starten

```bash
python download_bitcoin_data.py
```

Das öffnet eine GUI (funktioniert auf Mac & Windows):

![GUI Screenshot](docs/images/download_gui.png)

### Schritt 2: Konfiguration

1. **Output Directory** wählen:
   - Mac: `/Volumes/MySSD/bitcoin_data`
   - Windows: `D:\bitcoin_data` oder `E:\bitcoin_data`
   - Linux: `/mnt/ssd/bitcoin_data`

2. **Zeitraum** eingeben:
   - Format: `YYYY-MM-DD`
   - Beispiel: `2021-01-01` bis `2021-12-31`
   - Oder Quick Preset nutzen

3. **Tabellen** auswählen:
   - ✅ Blocks (~1 MB/Tag)
   - ✅ Transactions (~150 MB/Tag) ← **Wichtigste Tabelle**
   - ✅ Outputs (~250 MB/Tag)

4. **Optionen**:
   - ✅ Remove .gz files (empfohlen, spart ~70% Platz)

5. **"Calculate Size"** klicken:
   - Zeigt geschätzte Download-Größe
   - Zeigt benötigten Speicherplatz

6. **"Start Download"** klicken

### Schritt 3: Warten

- Downloads sind **sequenziell** (Blockchair-Limitation)
- Dauert 2-6 Stunden (je nach Internet & Zeitraum)
- Fortschritt wird angezeigt
- Kann unterbrochen und fortgesetzt werden

---

## 📊 Empfohlene Zeiträume

### Jahr 2021 (empfohlen)
```
Start: 2021-01-01
End:   2021-12-31
Größe: ~500 GB
Dauer: ~4-6 Stunden
```

**Warum 2021?**
- Bull Run Peak (~$69k)
- El Salvador Bitcoin-Adoption
- MicroStrategy, Tesla Käufe
- China Mining Ban
- Spannende Whale-Aktivität

### Q1 2021 (zum Testen)
```
Start: 2021-01-01
End:   2021-03-31
Größe: ~120 GB
Dauer: ~1-2 Stunden
```

### Nur Januar (schnell)
```
Start: 2021-01-01
End:   2021-01-31
Größe: ~40 GB
Dauer: ~30 Minuten
```

---

## 💾 Speicherplatz-Rechner

| Zeitraum | Komprimiert | Unkomprimiert | Mit --remove-gz |
|----------|-------------|---------------|-----------------|
| 1 Tag    | ~0.4 GB     | ~1.3 GB       | ~1.3 GB         |
| 1 Woche  | ~2.8 GB     | ~9 GB         | ~9 GB           |
| 1 Monat  | ~12 GB      | ~40 GB        | ~40 GB          |
| 1 Quartal| ~36 GB      | ~120 GB       | ~120 GB         |
| 1 Jahr   | ~145 GB     | ~480 GB       | ~480 GB         |

**Empfehlung:** Aktiviere "Remove .gz files" um ~70% Platz zu sparen.

---

## 🔧 Nach dem Download

### In Notebooks verwenden

**Methode 1: Einfach (empfohlen)**

```python
from data_config import DataConfig, load_data

# Config
config = DataConfig(source="local")  # Auto-detect Pfad

# Oder manuell:
config = DataConfig(
    source="local",
    local_data_path="/Volumes/MySSD/bitcoin_data/extracted"
)

# Daten laden
df = load_data(config, "2021-01-01", "2021-01-07", spark=spark)
df.show()
```

**Methode 2: Direkter Loader**

```python
from scripts.load_blockchair_data import BlockchairDataLoader

loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")
df = loader.load_transactions("2021-01-01", "2021-01-07")
```

### Beispiel-Notebooks

1. **`notebooks/USE_DATA_SOURCES.ipynb`** - Zeigt alle Datenquellen-Optionen
2. **`notebooks/02_local_data_exploration.ipynb`** - Lokale Daten explorieren

---

## ⚙️ Technische Details

### Verzeichnisstruktur

```
/Volumes/MySSD/bitcoin_data/
├── raw/                    # .gz Dateien (optional)
│   ├── blocks/
│   ├── transactions/
│   └── outputs/
│
└── extracted/              # .tsv Dateien (werden geladen) ⭐
    ├── blocks/
    │   ├── blockchair_bitcoin_blocks_2021-01-01.tsv
    │   └── ...
    ├── transactions/
    │   ├── blockchair_bitcoin_transactions_2021-01-01.tsv
    │   └── ...
    └── outputs/
        └── ...
```

### Download-Mechanismus

- **Sequenziell:** Ein File nach dem anderen (Blockchair-Requirement)
- **Error-Handling:** 404 Fehler = File nicht verfügbar (normal, wird übersprungen)
- **Fortsetzen:** Bereits existierende Files werden übersprungen
- **Extraktion:** Automatisch .gz → .tsv
- **Cleanup:** Optional .gz löschen nach Extraktion

### Datenformat

**Blocks:**
- CSV/TSV Format
- Header in erster Zeile
- Delimiter: Tab (`\t`)
- Encoding: UTF-8

**Transactions:**
- Wichtigste Tabelle für Entity-Clustering
- Enthält: hash, input_count, output_count, fee, etc.
- ~40% sind Multi-Input-Transactions

**Outputs:**
- Alle Transaction Outputs (UTXOs)
- Enthält: recipient (Adresse), value, is_spent, etc.
- Wichtig für Balance-Berechnung

---

## 🐛 Troubleshooting

### Problem: GUI startet nicht

**Lösung:** Installiere tkinter
```bash
# macOS
brew install python-tk

# Windows (sollte standardmäßig installiert sein)
# Falls nicht: Python neu installieren mit tkinter Option

# Linux
sudo apt-get install python3-tk
```

### Problem: "404 Not Found" Fehler

**Normal!** Blockchair hat nicht für jeden Tag Daten. Script überspringt automatisch.

### Problem: Download zu langsam

**Mögliche Ursachen:**
- Langsame Internet-Verbindung
- Blockchair Server ausgelastet

**Lösungen:**
- Kleineren Zeitraum wählen
- Zu anderer Tageszeit versuchen
- Nur wichtigste Tabelle downloaden (transactions)

### Problem: Zu wenig Speicherplatz

**Lösungen:**

1. **Kleineren Zeitraum:**
   - Statt Jahr → Quartal
   - Statt Quartal → Monat

2. **Nur wichtigste Tabelle:**
   - Deaktiviere Blocks & Outputs
   - Nur Transactions (wichtigste Tabelle)

3. **Remove .gz aktivieren:**
   - Spart ~70% Platz
   - Nur unkomprimierte .tsv bleiben

4. **Zu Parquet konvertieren (später):**
   ```python
   df = loader.load_transactions("2021-01-01", "2021-12-31")
   df.write.parquet("/path/transactions_2021.parquet")
   # Dann .tsv löschen → spart ~50% zusätzlich
   ```

### Problem: Download bricht ab

**Lösung:** Einfach neu starten!
- Bereits heruntergeladene Files werden erkannt
- Download setzt dort fort wo er abgebrochen wurde

---

## 📈 Performance-Tipps

### Schnellerer Download

1. **Stabile Internet-Verbindung**
   - LAN statt WLAN
   - Keine anderen Downloads parallel

2. **Zu richtiger Tageszeit**
   - Nachts/früh morgens oft schneller
   - Blockchair Server weniger ausgelastet

### Schnelleres Laden in Notebooks

1. **Kleinere Zeiträume laden:**
   ```python
   # Statt ganzen Monat
   df = load_data(config, "2021-01-01", "2021-01-31")

   # Besser: Wochenweise
   df = load_data(config, "2021-01-01", "2021-01-07")
   ```

2. **Zu Parquet konvertieren** (für wiederholte Nutzung):
   ```python
   # Einmalig: TSV → Parquet
   df = loader.load_transactions("2021-01-01", "2021-12-31")
   df.write.parquet("/path/parquet/transactions_2021.parquet")

   # Später ~5x schneller:
   df = spark.read.parquet("/path/parquet/transactions_2021.parquet")
   ```

3. **Nur benötigte Spalten:**
   ```python
   df = df.select("hash", "input_count", "output_count", "fee")
   ```

---

## 🔄 Datenquellen-Vergleich

| Feature | Demo | BigQuery | Local (Blockchair) |
|---------|------|----------|--------------------|
| **Setup** | Keine | Credentials nötig | Download nötig |
| **Kosten** | Kostenlos | ~$5/TB | Kostenlos (nur Internet) |
| **Offline** | ✅ Ja | ❌ Nein | ✅ Ja |
| **Zeitraum** | Nur Sample | 2009-heute | Heruntergeladene Periode |
| **Geschwindigkeit** | Sofort | Variabel | Schnell (lokal) |
| **Größe** | ~5 Rows | Vollständig | Zeitraum-abhängig |

**Empfehlung:**
- **Entwicklung/Testing:** Local (Blockchair)
- **Finale Analyse:** BigQuery (vollständiges Dataset)
- **Quick Demo:** Demo-Daten

---

## 📚 Weitere Ressourcen

- **Blockchair API:** https://blockchair.com/api/docs
- **Blockchair Dumps:** https://gz.blockchair.com/bitcoin/
- **Projekt-Dokumentation:** [docs/BLOCKCHAIR_INTEGRATION.md](docs/BLOCKCHAIR_INTEGRATION.md)
- **Script-Details:** [scripts/README.md](scripts/README.md)

---

## ✅ Checkliste

Bevor du downloadest:

- [ ] Genug Speicherplatz? (Check mit "Calculate Size")
- [ ] Output Directory gewählt?
- [ ] Zeitraum sinnvoll? (Empfohlen: 2021)
- [ ] Tabellen ausgewählt? (Minimum: Transactions)
- [ ] "Remove .gz" aktiviert? (Spart Platz)
- [ ] Stabile Internet-Verbindung?
- [ ] Zeit? (2-6 Stunden)

Nach Download:

- [ ] Daten in `extracted/` Ordner vorhanden?
- [ ] Notebook `USE_DATA_SOURCES.ipynb` ausprobiert?
- [ ] Config in eigenem Notebook angepasst?
- [ ] Erste Analysen durchgeführt?

---

**Viel Erfolg beim Whale-Hunting! 🐋**
