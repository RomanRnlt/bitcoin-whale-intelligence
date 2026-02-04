# Bitcoin Whale Intelligence - Notebook Anleitung

Schritt-für-Schritt Anleitung zur Nutzung des Notebooks für Bitcoin Whale Detection mit Apache Spark.

---

## Voraussetzungen

### System-Anforderungen

- **Java**: Version 17 oder 21 (für Apache Spark 4.x)
- **Python**: Version 3.11 (Spark 4.x unterstützt noch kein Python 3.12+)
- **RAM**: Mindestens 8 GB, empfohlen 16+ GB für größere Datasets
- **Speicher**: Ca. 10 GB freier Speicherplatz für Output-Dateien

### Java Installation prüfen

```bash
java -version
# Sollte: openjdk version "17.x.x" oder "21.x.x" anzeigen
```

---

## Installation

### 1. Projekt entpacken

Entpacke die bereitgestellte `bitcoin-whale-intelligence.zip` Datei:

```bash
# macOS/Linux
unzip bitcoin-whale-intelligence.zip
cd bitcoin-whale-intelligence

# Windows: Rechtsklick auf .zip → "Alle extrahieren..."
```

### 2. Python-Umgebung mit `uv` erstellen

Dieses Projekt nutzt [uv](https://github.com/astral-sh/uv) als Package Manager (schneller als pip/poetry).

```bash
# uv installieren (falls noch nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Virtual Environment erstellen und Dependencies installieren
uv venv --python 3.11
source .venv/bin/activate  # macOS/Linux
# oder: .venv\Scripts\activate  # Windows

# Dependencies aus pyproject.toml installieren
uv sync
```

**Alternative mit Standard-pip:**

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Dataset herunterladen

Wähle ein Dataset je nach verfügbarem Speicherplatz und gewünschter Laufzeit:

| Dataset | Komprimiert | Entpackt | Link |
|---------|-------------|----------|------|
| **Klein** | ~200 MB | ~1 GB | [Download](https://drive.google.com/file/d/1cjEeRarQR2jGw10CzSCkbczFDldn_jBR/view?usp=sharing) |
| **Mittel** | ~1 GB | ~6 GB | [Download](https://drive.google.com/file/d/1pkkTnLg2QOpS4Y3BOYGhJQ3nFgDV9k9g/view?usp=sharing) |
| **Groß** | ~4 GB | ~20 GB | [Download](https://drive.google.com/file/d/1NTtyUTrDkFNAY1IJ3lhYB-7eiz09REYk/view?usp=sharing) |

**Schritte:**
1. ZIP-Datei herunterladen
2. Entpacken in den `blockchain_exports` Ordner
3. Pfad zum Ordner merken

Erwartete Struktur:
```
blockchain_exports/              ← Diesen Pfad im Notebook angeben
└── 2024-01-15_2024-02-04/      ← Entpacktes Dataset (Ordnername = Datumsbereich)
    ├── blocks/*.json
    └── transactions/*.json
```

**Hinweis:** Der Ordnername des Datasets (z.B. `2024-01-15_2024-02-04`) entspricht dem Zeitraum der Blockchain-Daten. Es können auch mehrere Datasets im `blockchain_exports` Ordner liegen.

---

## Konfiguration

### 1. Environment-Datei erstellen

Das Notebook wird über eine `.env` Datei konfiguriert:

```bash
cd notebooks
cp .env.experiment .env
```

### 2. Pfade anpassen

Öffne `notebooks/.env` und passe folgende Pfade an:

```bash
# =============================================================================
# PFADE (HIER ANPASSEN!)
# =============================================================================

# Ordner mit den Bitcoin Blockchain JSON-Dateien
BLOCKCHAIN_DATA_PATH=../blockchain_exports

# Ordner für Pipeline-Ergebnisse (Parquet, CSVs, etc.)
OUTPUT_PATH=../output
```

**Pfad-Beispiele:**

| System | Pfad-Format |
|--------|-------------|
| macOS/Linux | `BLOCKCHAIN_DATA_PATH=/Users/roman/blockchain_exports` |
| macOS/Linux (relativ) | `BLOCKCHAIN_DATA_PATH=../blockchain_exports` |
| Windows | `BLOCKCHAIN_DATA_PATH=C:/Users/Roman/blockchain_exports` |

> **Hinweis:** Relative Pfade (mit `..`) sind relativ zum `notebooks/` Ordner.

### 3. Spark-Konfiguration anpassen

```bash
# RAM für Spark Driver (je nach verfügbarem System-RAM)
SPARK_DRIVER_MEMORY=8g      # 8 GB, passe an dein System an

# Anzahl CPU-Cores (alle verfügbaren Cores nutzen)
SPARK_NUM_CORES=8

# Large Dataset Mode für schnellere Verarbeitung
LARGE_DATASET_MODE=true
```

**RAM-Empfehlungen:**

| System-RAM | Empfohlene Einstellung |
|------------|------------------------|
| 8 GB | `SPARK_DRIVER_MEMORY=4g` |
| 16 GB | `SPARK_DRIVER_MEMORY=8g` |
| 32 GB+ | `SPARK_DRIVER_MEMORY=16g` |

### 4. Experiment-Modus aktivieren (optional)

Um Performance-Experimente durchzuführen:

```bash
# Experiment-Modus aktivieren
EXPERIMENT_MODE=true

# CPU-Konfigurationen zum Testen (kommagetrennt)
EXPERIMENT_CPU_CONFIGS=2,4,8

# RAM-Konfigurationen zum Testen
EXPERIMENT_RAM_CONFIGS=4g,8g,12g

# Datenmengen als Bruchteile testen
EXPERIMENT_DATA_FRACTIONS=0.25,0.5,1.0
```

> ❗**Warnung:** Der Durchlauf im Experiment Modus kann sehr lange dauert (Referenz: Macbook Air M4, 6GB Dataset = 1,5h; älterer Windows PC = 4h+)

---

## Notebook ausführen

### Mit VS Code (empfohlen)

1. **Projekt in VS Code öffnen**
   ```bash
   code .
   ```

2. **Notebook öffnen**
   - Navigiere zu `notebooks/bitcoin_whale_explained_experiment_with_outputs_6gb.ipynb`
   - Klicke auf die Datei, um sie zu öffnen

3. **Outline für Navigation nutzen**
   - Links in der Seitenleiste: "Outline" aufklappen
   - Zeigt alle Markdown-Überschriften und Zellen im Notebook
   - Klicke auf einen Abschnitt, um direkt dorthin zu springen
   - Praktisch für große Notebooks mit vielen Zellen

4. **Kernel auswählen**
   - Oben rechts auf "Select Kernel" klicken
   - "Python Environments..." auswählen
   - Die erstellte Virtual Environment wählen (`.venv/bin/python`)

5. **Alle Zellen ausführen**
   - Oben in der Toolbar: "Run All" Button klicken
   - Oder: Menü → Run → Run All Cells
   - Oder Tastenkombination: `Shift+Enter` für Zelle für Zelle

6. **Kernel neu starten (falls nötig)**
   - Falls du die `.env` Datei geändert hast:
   - Oben in der Toolbar: "Restart" Button klicken
   - Dann erneut "Run All"

### Alternative: Jupyter Notebook (manuell)

Falls du lieber die klassische Jupyter-Oberfläche nutzt:

```bash
cd notebooks
jupyter notebook bitcoin_whale_explained_experiment_with_outputs_6gb.ipynb
```

Im Browser:
- **Kernel neu starten:** Menü → Kernel → Restart & Clear Output
- **Alle Zellen ausführen:** Menü → Cell → Run All

---

## Performance & Laufzeit

### Benchmark (6 GB Dataset, Experiment Mode)

**Hardware:** MacBook Air M4 (8 CPU-Cores, 16 GB RAM)

**Konfiguration:**
```bash
SPARK_DRIVER_MEMORY=20g
SPARK_NUM_CORES=8
EXPERIMENT_MODE=true
LARGE_DATASET_MODE=true
```

**Laufzeit:** Ca. **1,5 Stunden** (vollständige Pipeline mit Experimenten)

### Geschätzte Laufzeiten

| Dataset-Größe | Modus | Geschätzte Laufzeit |
|---------------|-------|---------------------|
| 1 GB | Normal | 5 Min |
| 6 GB | Normal | 15 Min |
| 6 GB | Experiment | **1,5 Std** |
| 50 GB+ | Normal | 4-6 Std |

---

## Pipeline-Schritte

Das Notebook führt folgende Schritte aus:

1. **Daten laden** – Bitcoin-Transaktionen aus JSON-Dateien einlesen
2. **Outputs extrahieren** – Nested JSON in flache Tabelle transformieren
3. **Inputs extrahieren** – Transaction-Inputs normalisieren
4. **UTXO-Set berechnen** – Aktive (unverbrauchte) Outputs identifizieren
5. **Entity Clustering** – Adressen gruppieren via Connected Components
6. **Whale Detection** – Entities mit >1000 BTC finden
7. **Visualisierung** – Balance-Verteilung, Timeline, Activity-Patterns

### Output-Dateien

Alle Ergebnisse werden im `OUTPUT_PATH` gespeichert:

```
output/
├── outputs.parquet              # Alle Transaction-Outputs
├── inputs.parquet               # Alle Transaction-Inputs
├── utxos.parquet                # Aktive UTXOs
├── entities.parquet             # Geclusterte Adressen
├── entity_balances.parquet      # Balancen pro Entity
├── whale_analysis.png           # Visualisierungen
└── experiments/                 # Experiment-Ergebnisse (falls aktiv)
    ├── cpu_scaling/
    ├── ram_scaling/
    └── data_scaling/
```

---

**Viel Erfolg beim Whale Hunting!** 🐋
