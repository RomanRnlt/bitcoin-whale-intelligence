# Bitcoin Whale Intelligence

Master-Projekt zur Identifikation von Bitcoin-Whales durch Entity Resolution auf der Blockchain.

**Modul:** Advanced Data Engineering
**Studiengang:** Wirtschaftsinformatik (Master)

## Inhaltsverzeichnis

- [Projektübersicht](#projektübersicht)
- [Datenquelle](#datenquelle)
- [Notebook: Entity Clustering](#notebook-entity-clustering)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Projektstruktur](#projektstruktur)

**Neu im Projekt?** Starte mit [SIMPLE_EXPLANATION.md](docs/SIMPLE_EXPLANATION.md) für eine verständliche Einführung.

---

## Projektübersicht

### Das Problem

**800 Millionen Bitcoin-Adressen existieren - aber wer besitzt sie wirklich?**

| Konzept | Beschreibung | In Blockchain sichtbar? |
|---------|--------------|-------------------------|
| **Adresse** | Einzelner "Briefkasten" (z.B. `bc1q...`) | Ja |
| **Wallet** | Software die tausende Adressen verwaltet | Nein |
| **Entity** | Die tatsächliche Person/Firma dahinter | Nein |

**Beispiel:** Ein Whale mit 5000 BTC könnte diese über 1000 verschiedene Adressen verteilt haben. Ohne Analyse sieht man 1000 kleine Holder statt 1 großen Whale.

### Die Lösung: Common Input Ownership Heuristic

**Kernidee:** Wenn eine Bitcoin-Transaction mehrere Adressen als Inputs kombiniert, gehören alle zur selben Person.

**Warum?** Bitcoin funktioniert mit "Münzen" (UTXOs) statt Kontoständen:
- Jede "Münze" muss vollständig ausgegeben werden
- Wenn eine nicht reicht → mehrere kombinieren
- Um mehrere zu kombinieren → braucht man alle Private Keys
- **Nur eine Person kann alle Keys besitzen**

```
Person X sendet 0.7 BTC, hat aber nur:
  Adresse A: 0.5 BTC
  Adresse B: 0.3 BTC

Muss beide kombinieren:
  Transaction Inputs: A (0.5) + B (0.3) = 0.8 BTC

→ Beweis: A und B gehören zur gleichen Person!
```

### Pipeline

```
Bitcoin-ETL JSON Export
      │
      ▼ Spark ETL
      │
      ├──► outputs.parquet  (alle Outputs)
      ├──► inputs.parquet   (alle Inputs mit Spent-Referenzen)
      └──► utxos.parquet    (Unspent Transaction Outputs)
                │
                ▼ GraphFrames Connected Components
                │
                └──► entities.parquet (address → entity_id Mapping)
```

---

## Datenquelle

Die Blockchain-Daten werden mit [bitcoin-etl](https://github.com/blockchain-etl/bitcoin-etl) von einem Bitcoin Full Node exportiert:

```bash
bitcoinetl export_all \
    --provider-uri http://user:pass@localhost:8332 \
    --start 2011-01-01 --end 2011-06-01 \
    --output-dir /path/to/blockchain_exports
```

### Datenstruktur

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

**Format:** Hive-partitionierte, zeilenbasierte JSON (JSONL)

**Besonderheit:** Transaktionen enthalten **nested Arrays** für inputs und outputs:

```json
{
  "hash": "abc123...",
  "input_count": 3,
  "inputs": [
    {"spent_transaction_hash": "...", "spent_output_index": 0, "addresses": [...]},
    ...
  ],
  "outputs": [
    {"index": 0, "value": 50000000, "addresses": ["bc1q..."]},
    ...
  ]
}
```

---

## Notebook: Entity Clustering

**Notebook:** [01_entity_clustering.ipynb](notebooks/01_entity_clustering.ipynb)

Ein einzelnes Notebook das die komplette Pipeline abdeckt:

### 1. Daten laden
- Bitcoin-ETL JSON Daten mit Spark laden
- Hive-Partitionen automatisch erkennen

### 2. ETL zu Parquet
- Nested JSON → flache Parquet-Tabellen
- 10x schnelleres Lesen bei wiederholten Analysen

### 3. UTXO Set berechnen
- Alle Outputs MINUS ausgegebene Outputs
- Ergebnis: Alle "Münzen" die noch existieren

### 4. Multi-Input Analyse
- Transaktionen mit ≥2 Inputs identifizieren
- Diese zeigen Adress-Zusammengehörigkeit
- Filter: 2-50 Inputs (>50 = wahrscheinlich Exchange)

### 5. Entity Clustering
- Graph aufbauen: Adressen = Knoten, gemeinsame Inputs = Kanten
- GraphFrames Connected Components Algorithmus
- Ergebnis: Jede Adresse bekommt eine entity_id

### Output-Dateien

```
data/
├── outputs.parquet     # Alle Transaction Outputs
├── inputs.parquet      # Alle Inputs mit Spent-Referenzen
├── utxos.parquet       # Unspent Transaction Outputs
└── entities.parquet    # address → entity_id Mapping
```

---

## Tech Stack

| Komponente | Technologie |
|------------|-------------|
| **Processing** | Apache Spark (PySpark) |
| **Graph-Analyse** | GraphFrames |
| **Datenformat** | Parquet (optimiert) |
| **Environment** | Jupyter Notebooks |
| **Python** | 3.11+ |
| **Java** | 11+ (für Spark) |

### Abhängigkeiten

```bash
pip install pyspark graphframes pandas matplotlib seaborn
```

---

## Quick Start

### 1. Voraussetzungen

- Python 3.11+
- Java 11+ (für Spark)
- Bitcoin-ETL exportierte Daten

### 2. Repository klonen

```bash
git clone https://github.com/your-username/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Projekt starten

```bash
./start_project.sh
```

### 5. Notebook öffnen

In Jupyter: `notebooks/01_entity_clustering.ipynb`

**Wichtig:** Pfad zu den Daten anpassen:

```python
BLOCKCHAIN_DATA_PATH = "/path/to/blockchain_exports"
```

---

## Projektstruktur

```
bitcoin-whale-intelligence/
├── notebooks/
│   └── 01_entity_clustering.ipynb  # Haupt-Notebook
├── src/
│   ├── __init__.py
│   └── etl.py                      # ETL-Funktionen
├── data/                           # Generierte Parquet-Dateien
├── docs/
│   ├── SIMPLE_EXPLANATION.md       # Einführung für Einsteiger
│   ├── PROJECT_CONTEXT.md          # Projekt-Details
│   └── ...
├── requirements.txt
├── start_project.sh
└── README.md
```

### src/etl.py

Kernfunktionen:

| Funktion | Beschreibung |
|----------|--------------|
| `create_spark_session()` | Optimierte Spark-Session erstellen |
| `load_transactions()` | Bitcoin-ETL JSON laden |
| `load_blocks()` | Block-Daten laden |
| `explode_outputs()` | Nested → Flat für Outputs |
| `explode_inputs()` | Nested → Flat für Inputs |
| `compute_utxo_set()` | UTXO Set berechnen |
| `enrich_clustering_inputs()` | Multi-Input TXs für Clustering vorbereiten |

---

## Nächste Schritte (geplant)

Mit dem Entity-Mapping (`entities.parquet`) können weitere Analysen durchgeführt werden:

- **Whale Detection**: Entity-Balances berechnen, Entities mit ≥1000 BTC identifizieren
- **Verhaltensanalyse**: Akkumulation vs. Distribution über Zeit tracken
- **Exchange-Identifikation**: Entities mit ungewöhnlichen Mustern klassifizieren

---

Master-Projekt | Advanced Data Engineering | Wirtschaftsinformatik
