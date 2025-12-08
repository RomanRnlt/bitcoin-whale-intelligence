# Bitcoin Whale Intelligence - Technischer Kontext

> Architektur, Tech Stack und Datenmodell fuer Entwickler

## Inhaltsverzeichnis

- [Tech Stack](#tech-stack)
- [Architektur](#architektur)
- [Datenmodell](#datenmodell)
- [Algorithmen](#algorithmen)
- [Performance](#performance)
- [Roadmap](#roadmap)

---

## Tech Stack

```mermaid
flowchart LR
    subgraph data["Daten"]
        TSV["Blockchair TSV"]
    end

    subgraph processing["Verarbeitung"]
        SPARK["Spark 3.5"]
        GF["GraphFrames"]
    end

    subgraph storage["Speicher"]
        PQ["Parquet"]
    end

    subgraph analysis["Analyse"]
        JUP["Jupyter"]
    end

    TSV --> SPARK <--> GF
    SPARK --> PQ --> JUP
```

| Technologie | Zweck |
|-------------|-------|
| **Apache Spark** | Verteilte Verarbeitung, skaliert auf TB |
| **GraphFrames** | Connected Components auf Mrd. Kanten |
| **Parquet** | Kompression 70-90%, Column Pruning |
| **Jupyter** | Interaktive Analyse |

---

## Architektur

```mermaid
flowchart TB
    subgraph etl["ETL Layer"]
        RAW[("blockchair-downloader/<br/>TSV Files")]
    end

    subgraph spark["Spark Layer - src/etl.py"]
        LOAD["load_transactions()"]
        EXPLODE["explode_outputs()<br/>explode_inputs()"]
        UTXO["compute_utxo_set()"]
        ENRICH["enrich_clustering_inputs()"]
    end

    subgraph storage["Storage"]
        OUT[("outputs.parquet")]
        INP[("inputs.parquet")]
        UTXOS[("utxos.parquet")]
        ENTS[("entities.parquet")]
    end

    subgraph graph["Graph Layer"]
        CC["connectedComponents()"]
    end

    RAW --> LOAD --> EXPLODE
    EXPLODE --> OUT & INP
    OUT & INP --> UTXO --> UTXOS
    EXPLODE --> ENRICH --> CC --> ENTS
```

---

## Datenmodell

```mermaid
erDiagram
    TRANSACTION ||--o{ OUTPUT : "has"
    TRANSACTION ||--o{ INPUT : "has"
    INPUT }o--|| OUTPUT : "spends"
    OUTPUT ||--o| UTXO : "if unspent"
    OUTPUT }o--|| ENTITY : "belongs to"

    OUTPUT {
        string tx_hash
        int output_index
        long value
        array addresses
    }

    INPUT {
        string tx_hash
        string spent_tx_hash
        int spent_output_index
    }

    ENTITY {
        string address PK
        long entity_id
    }
```

**Parquet-Dateien**:
- `outputs.parquet` - Alle TX-Outputs mit Adressen
- `inputs.parquet` - Alle TX-Inputs mit Spent-Referenzen
- `utxos.parquet` - Unspent Outputs (Balance-Grundlage)
- `entities.parquet` - Adresse -> Entity-ID Mapping

---

## Algorithmen

### Common Input Ownership Heuristic

```
Wenn TX mehrere Input-Adressen hat
  -> Absender besitzt alle Private Keys
  -> Alle Adressen gehoeren einer Entity
```

**Ausnahmen**: CoinJoin, Exchange Consolidation (gefiltert via `max_inputs <= 50`)

### Connected Components

1. Jeder Knoten (Adresse) erhaelt eigene Component-ID
2. Iterativ: Sende ID an Nachbarn, uebernehme kleinste
3. Wiederhole bis Konvergenz
4. **Checkpointing** alle N Iterationen gegen Lineage-Explosion

---

## Performance

| Datenmenge | Transaktionen | Clustering-Zeit |
|------------|---------------|-----------------|
| Testdaten (H1 2011) | 382k | ~2 Min |
| 1 Jahr (2015) | ~50M | ~30 Min |
| Volle Blockchain | 900M+ | ~8h auf Cluster |

**Spark-Config**:
- `driver.memory: 8g`
- `adaptive.enabled: true`
- `shuffle.partitions: 200`

---

## Roadmap

```mermaid
flowchart LR
    subgraph done["Fertig"]
        C1["Entity Clustering"]
    end

    subgraph planned["Geplant"]
        P1["Whale Detection"]
        P2["Verhaltensanalyse"]
    end

    subgraph future["Zukunft"]
        F1["Exchange Detection"]
        F2["Real-time Streaming"]
    end

    done --> planned --> future

    style done fill:#51cf66
    style planned fill:#ffd43b
    style future fill:#868e96,color:#fff
```

| Phase | Beschreibung |
|-------|--------------|
| **Entity Clustering** | Adressen gruppieren via Multi-Input Heuristik |
| **Whale Detection** | Balance pro Entity, Top-Wale identifizieren |
| **Verhaltensanalyse** | Akkumulation vs. Distribution Patterns |
| **Exchange Detection** | Bekannte Exchanges erkennen und taggen |
