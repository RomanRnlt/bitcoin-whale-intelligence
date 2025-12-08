# Bitcoin Whale Intelligence - Notebook Workflow

> Analyse-Pipeline: Notebooks, Status und Datenfluss

## Inhaltsverzeichnis

- [Pipeline-Uebersicht](#pipeline-uebersicht)
- [Notebook 01: Entity Clustering](#notebook-01-entity-clustering-fertig)
- [Notebook 02: Whale Detection](#notebook-02-whale-detection-geplant)
- [Notebook 03: Verhaltensanalyse](#notebook-03-verhaltensanalyse-geplant)

---

## Pipeline-Uebersicht

```mermaid
flowchart LR
    subgraph done["Fertig"]
        NB0["00_test_blockchair"]
        NB1["01_entity_clustering"]
    end

    subgraph planned["Geplant"]
        NB2["02_whale_detection"]
        NB3["03_behavior_analysis"]
    end

    NB0 --> NB1 --> NB2 --> NB3

    style done fill:#51cf66
    style planned fill:#868e96,color:#fff
```

| Notebook | Status | Output |
|----------|--------|--------|
| `00_test_blockchair_loading` | Fertig | Datenvalidierung |
| `01_entity_clustering` | Fertig | entities.parquet |
| `02_whale_detection` | Geplant | whale_entities.parquet |
| `03_behavior_analysis` | Geplant | behavior_metrics.parquet |

---

## Notebook 01: Entity Clustering (Fertig)

**Input**: `blockchair-downloader/` TSV-Dateien
**Output**: `outputs.parquet`, `inputs.parquet`, `utxos.parquet`, `entities.parquet`

```mermaid
flowchart TB
    LOAD["1. Daten laden"] --> ETL["2. Explode Outputs/Inputs"]
    ETL --> UTXO["3. UTXO berechnen"]
    ETL --> GRAPH["4. Graph aufbauen"]
    GRAPH --> CC["5. Connected Components"]
    CC --> SAVE["6. Entities speichern"]
```

**Metriken**: 382k TXs, 769k Outputs, ~150k Adressen -> ~110k Entities (25% Reduktion)

---

## Notebook 02: Whale Detection (Geplant)

**Input**: `entities.parquet`, `utxos.parquet`
**Output**: `entity_balances.parquet`, `whale_entities.parquet`

```mermaid
flowchart LR
    LOAD["Entities + UTXOs"] --> JOIN["Join"]
    JOIN --> AGG["SUM(value) pro Entity"]
    AGG --> CLASS{"Balance >= 1000 BTC?"}
    CLASS -->|Ja| WHALE["Whale"]
    CLASS -->|Nein| NORMAL["Normal"]
```

---

## Notebook 03: Verhaltensanalyse (Geplant)

**Input**: `entity_balances.parquet`, `whale_entities.parquet`
**Output**: `behavior_metrics.parquet`

```mermaid
flowchart LR
    TIME["Balance pro Zeitraum"] --> DELTA["Delta berechnen"]
    DELTA --> CLASS{"Delta?"}
    CLASS -->|Positiv| ACC["Akkumulation"]
    CLASS -->|Negativ| DIST["Distribution"]
    CLASS -->|~0| DORM["Dormant"]
```

**Ziel**: Erkennen ob Wale kaufen, verkaufen oder halten.
