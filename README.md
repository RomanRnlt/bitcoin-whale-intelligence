# Bitcoin Whale Intelligence

> Versteckte Bitcoin-Wale durch Entity Clustering aufspueren

---

## Das Problem: Versteckte Wale

Ein Bitcoin-Wal mit **5.000 BTC** kann sein Vermoegen auf hunderte Adressen verteilen. Auf der Blockchain sieht das aus wie viele kleine Besitzer:

```mermaid
flowchart LR
    subgraph blockchain["Was die Blockchain zeigt"]
        A1["1A1zP...fNa<br/>500 BTC"]
        A2["1BvBM...qhx<br/>300 BTC"]
        A3["1Feex...t4L<br/>200 BTC"]
        A4["12cbQ...xV8s<br/>150 BTC"]
        A5["1Q2TW...Wm8H<br/>100 BTC"]
    end

    subgraph reality["Die Realitaet"]
        W["EINE Person<br/>1.250 BTC<br/>= WAL!"]
    end

    A1 --> W
    A2 --> W
    A3 --> W
    A4 --> W
    A5 --> W

    style W fill:#ff6b6b,color:#fff
```

**Ohne Analyse:** 5 harmlose Adressen mit 100-500 BTC
**Mit Analyse:** 1 Wal mit 1.250 BTC!

---

## Die Loesung: Common Input Ownership

Wenn jemand eine Transaktion erstellt die **mehrere Adressen als Inputs** kombiniert, muss er alle Private Keys besitzen. Diese Adressen gehoeren also derselben Person!

```mermaid
flowchart TB
    subgraph tx["Transaktion TX-500"]
        I1["Input 1:<br/>2 BTC von 1A1zP...fNa"]
        I2["Input 2:<br/>3 BTC von 1BvBM...qhx"]
        O["Output:<br/>4.99 BTC an 1Feex...t4L"]

        I1 --> O
        I2 --> O
    end

    subgraph conclusion["Schlussfolgerung"]
        C["1A1zP...fNa und 1BvBM...qhx<br/>= SELBER BESITZER<br/>(beide Keys zum Signieren noetig)"]
    end

    tx --> conclusion

    style conclusion fill:#c8e6c9
```

---

## Pipeline-Uebersicht

```mermaid
flowchart TB
    RAW[("transactions/*.json<br/>bitcoin-etl Export<br/>382.000 TXs")]

    RAW --> EO["1. explode_outputs()<br/>Nested Array -> Zeilen"]
    RAW --> EI["2. explode_inputs()<br/>Nested Array -> Zeilen"]

    EO --> OUT[("outputs.parquet<br/>769.000 Zeilen")]
    EI --> INP[("inputs.parquet<br/>592.000 Zeilen")]

    OUT --> UTXO["3. UTXO berechnen<br/>LEFT ANTI JOIN"]
    INP --> UTXO
    UTXO --> UTXOP[("utxos.parquet<br/>177.000 aktive Outputs")]

    INP --> CC["4. Entity Clustering<br/>Connected Components"]
    CC --> ENT[("entities.parquet<br/>109.000 Entities")]

    UTXOP --> WHALE["5. Whale Detection<br/>JOIN + SUM + Filter"]
    ENT --> WHALE
    WHALE --> RESULT[("Gefundene Wale<br/>>= 1000 BTC")]

    style RAW fill:#e3f2fd
    style RESULT fill:#ff6b6b,color:#fff
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

| Status | Komponente | Beschreibung |
|--------|------------|--------------|
| Fertig | Daten laden | bitcoin-etl JSON einlesen |
| Fertig | explode_outputs() | Nested -> Flach |
| Fertig | explode_inputs() | Nested -> Flach |
| Fertig | UTXO-Set | Aktive Guthaben berechnen |
| Fertig | Entity Clustering | Connected Components |
| Geplant | Whale Detection | Balance pro Entity |

---

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/architecture.md](docs/architecture.md) | **Pipeline mit Mermaid-Diagrammen und Erklaerungen** |
| [docs/setup.md](docs/setup.md) | Installation und Konfiguration |

---

## Tech Stack

| Technologie | Zweck |
|-------------|-------|
| **Apache Spark** | Verteilte Verarbeitung (900M+ Transaktionen) |
| **GraphFrames** | Connected Components Algorithmus |
| **Parquet** | Spalten-Storage (70-90% Kompression) |
| **bitcoin-etl** | Bitcoin-Datenexport (JSON Format) |

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

| Schritt | Input | Output | Info |
|---------|-------|--------|------|
| Transaktionen | - | 382.000 | Rohdaten |
| Outputs | 382k TXs | 769.000 | explode() |
| Inputs | 382k TXs | 592.000 | explode() |
| **UTXOs** | 769k | **177.000** | 77% spent |
| **Entities** | 148k Adressen | **109.000** | 26% gruppiert |

**26% Reduktion:** Ueber ein Viertel aller Adressen gehoeren zu Mehrfach-Besitzern und konnten gruppiert werden!

---

*Master-Projekt - Advanced Data Engineering - Wirtschaftsinformatik*
