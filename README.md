# Bitcoin Whale Intelligence

> Versteckte Bitcoin-Wale durch Entity Clustering identifizieren

---

## Das Problem

Ein Wal mit **5.000 BTC** kann diese auf 1.000 Adressen verteilen. Ohne Analyse sieht das aus wie 1.000 kleine Besitzer.

```
Blockchain zeigt:          Realitaet:
Adresse A: 500 BTC    ─┐
Adresse B: 300 BTC    ─┼──>  Entity X: 1.000 BTC (WAL!)
Adresse C: 200 BTC    ─┘
```

## Die Loesung: Common Input Ownership

Wenn eine Transaktion mehrere Adressen als Inputs kombiniert, gehoeren diese derselben Person - nur sie besitzt alle Private Keys.

```
TX-123: Input von A + Input von B  -->  A und B = gleicher Besitzer
```

---

## Pipeline-Uebersicht

```
bitcoin-etl JSON
       |
       v
+------------------+     +------------------+
| explode_outputs  | --> | outputs.parquet  |
+------------------+     +------------------+
       |                         |
       v                         v
+------------------+     +------------------+
| explode_inputs   | --> | inputs.parquet   |
+------------------+     +------------------+
       |                         |
       v                         v
+------------------+     +------------------+
| compute_utxo_set | --> | utxos.parquet    |
+------------------+     +------------------+
       |
       v
+------------------+     +------------------+
| Graph + CC       | --> | entities.parquet |
+------------------+     +------------------+
       |
       v
  WHALE DETECTION
```

---

## Quick Start

```bash
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
./start_project.sh
```

Siehe [docs/setup.md](docs/setup.md) fuer Details.

---

## Projekt-Status

| Status | Komponente |
|--------|------------|
| Fertig | Daten laden (bitcoin-etl JSON) |
| Fertig | Transformation (explode) |
| Fertig | UTXO-Set Berechnung |
| Fertig | Entity Clustering (Connected Components) |
| Geplant | Whale Detection (Balance pro Entity) |
| Geplant | Verhaltensanalyse |

---

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/architecture.md](docs/architecture.md) | Pipeline mit VORHER/NACHHER Beispielen |
| [docs/setup.md](docs/setup.md) | Installation, Konfiguration |

---

## Tech Stack

| Technologie | Zweck |
|-------------|-------|
| Apache Spark | Verteilte Verarbeitung (900M+ TXs) |
| GraphFrames | Connected Components Algorithmus |
| Parquet | Spalten-Storage (70-90% Kompression) |
| bitcoin-etl | Datenexport vom Full Node |

---

## Projektstruktur

```
bitcoin-whale-intelligence/
├── notebooks/
│   └── 01_entity_clustering.ipynb   # Hauptanalyse
├── src/
│   └── etl.py                       # Spark ETL-Funktionen
├── data/                            # Generierte Parquet-Dateien
├── docs/
│   ├── architecture.md              # Pipeline-Dokumentation
│   └── setup.md                     # Setup-Anleitung
└── start_project.sh                 # Startskript
```

---

## Metriken (H1/2011 Testdaten)

| Metrik | Wert |
|--------|------|
| Transaktionen | 382.000 |
| Outputs | 769.000 |
| UTXOs | 177.000 |
| Adressen im Graph | 148.000 |
| Entities | 109.000 |
| **Reduktion** | **26%** |

---

*Master-Projekt - Advanced Data Engineering - Wirtschaftsinformatik*
