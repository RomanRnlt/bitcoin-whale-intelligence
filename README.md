# Bitcoin Whale Intelligence

Ein Master-Projekt zur Identifikation versteckter Bitcoin-Wale durch Entity Clustering.

---

## Das Problem

**800 Millionen Bitcoin-Adressen** - aber wem gehoeren sie?

Ein Wal mit 5.000 BTC kann diese auf 1.000 Adressen verteilen. Ohne Analyse sieht das aus wie 1.000 kleine Besitzer. In Wirklichkeit ist es eine Person.

## Die Loesung

**Common Input Ownership Heuristic**: Wenn eine Transaktion mehrere Adressen als Inputs kombiniert, gehoeren diese derselben Person. Nur sie besitzt alle Private Keys.

```
TX-123: Input von A + B + C  -->  A, B, C = gleicher Besitzer
```

Ein Graph-Algorithmus findet dann alle verbundenen Adressen und gruppiert sie zu **Entities**.

## Features

- Entity Clustering mit Apache Spark + GraphFrames
- UTXO-Set Berechnung fuer aktuelle Balances
- Skalierbar auf die gesamte Bitcoin-Blockchain

## Quick Start

```bash
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./start_project.sh
```

Siehe [docs/setup.md](docs/setup.md) fuer Details zur Datenquelle.

## Projekt-Status

| Status | Komponente |
|--------|------------|
| Fertig | Entity Clustering (Connected Components) |
| Fertig | UTXO-Set Berechnung |
| Geplant | Whale Detection (Balance pro Entity) |
| Geplant | Verhaltensanalyse (Akkumulation/Distribution) |

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/architecture.md](docs/architecture.md) | Konzept, Pipeline, Mermaid-Diagramme |
| [docs/setup.md](docs/setup.md) | Installation, Datenexport |

## Projektstruktur

```
bitcoin-whale-intelligence/
├── notebooks/
│   └── 01_entity_clustering.ipynb    # Hauptanalyse
├── src/
│   └── etl.py                        # Spark ETL-Funktionen
├── data/                             # Generierte Parquet-Dateien
├── docs/                             # Dokumentation
└── start_project.sh                  # Startskript
```

## Tech Stack

| Technologie | Zweck |
|-------------|-------|
| Apache Spark | Verarbeitung von 900M+ Transaktionen |
| GraphFrames | Connected Components fuer Clustering |
| Parquet | Schnelles Spalten-Storage |
| bitcoin-etl | Datenexport vom Full Node |

---

*Master-Projekt | Advanced Data Engineering | Wirtschaftsinformatik*
