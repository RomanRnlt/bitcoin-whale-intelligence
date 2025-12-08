# Bitcoin Whale Intelligence - Technischer Kontext

> Dokumentation fur Entwickler: Architektur, Tech Stack und Performance-Uberlegungen

---

## Tech Stack

### Ubersicht

```mermaid
flowchart TB
    subgraph data_layer["Datenschicht"]
        BTC[("Bitcoin Node")]
        BTCETL["bitcoin-etl"]
        JSON[("JSON Export")]
        BTC --> BTCETL --> JSON
    end

    subgraph processing["Verarbeitungsschicht"]
        SPARK["Apache Spark 3.5"]
        GF["GraphFrames 0.8.3"]
        PQ[("Parquet Files")]
    end

    subgraph analysis["Analyseschicht"]
        JUP["Jupyter Notebooks"]
        MPL["Matplotlib"]
        PD["Pandas"]
    end

    JSON --> SPARK
    SPARK --> PQ
    SPARK <--> GF
    PQ --> JUP
    JUP --> MPL & PD

    style data_layer fill:#e7f5ff,stroke:#1c7ed6
    style processing fill:#fff3bf,stroke:#fab005
    style analysis fill:#d3f9d8,stroke:#2f9e44
```

### Technologie-Begrundung

| Technologie | Zweck | Warum diese Wahl? |
|-------------|-------|-------------------|
| **Apache Spark** | Verteilte Datenverarbeitung | Skaliert auf Terabytes, SQL-API, Python-Bindings |
| **GraphFrames** | Graph-Algorithmen | Connected Components auf Milliarden Kanten |
| **Parquet** | Datenspeicherung | Kompression 70-90%, Column Pruning, Predicate Pushdown |
| **bitcoin-etl** | Datenexport | Standard-Tool, gepflegte Schemas |
| **Jupyter** | Interaktive Analyse | Visualisierung, iterative Entwicklung |

---

## Architektur im Detail

### Komponentendiagramm

```mermaid
flowchart TB
    subgraph external["Externe Datenquellen"]
        NODE[("Bitcoin<br/>Full Node<br/>~500 GB")]
    end

    subgraph etl_layer["ETL Layer"]
        EXPORT["bitcoin-etl<br/>export_all"]
        RAW[("blockchain_exports/<br/>JSON + Hive Partitions")]
    end

    subgraph spark_layer["Spark Processing Layer"]
        subgraph src["src/etl.py"]
            LOAD["load_transactions()<br/>load_blocks()"]
            EXPLODE["explode_outputs()<br/>explode_inputs()"]
            UTXO["compute_utxo_set()"]
            ENRICH["enrich_clustering_inputs()"]
        end

        SESSION["SparkSession<br/>driver_memory: 8g<br/>adaptive execution"]
    end

    subgraph storage["Storage Layer"]
        direction LR
        OUT[("outputs.parquet")]
        INP[("inputs.parquet")]
        UTXOS[("utxos.parquet")]
        ENTS[("entities.parquet")]
    end

    subgraph graph_layer["Graph Processing Layer"]
        VERTICES["Vertices DataFrame<br/>id: address"]
        EDGES["Edges DataFrame<br/>src, dst: addresses"]
        CC["connectedComponents()<br/>+ Checkpointing"]
    end

    NODE --> EXPORT --> RAW
    RAW --> SESSION --> LOAD
    LOAD --> EXPLODE --> OUT & INP
    OUT & INP --> UTXO --> UTXOS
    EXPLODE --> ENRICH --> VERTICES & EDGES
    VERTICES & EDGES --> CC --> ENTS

    style external fill:#868e96,color:#fff
    style spark_layer fill:#fff3bf,stroke:#fab005
    style graph_layer fill:#d3f9d8,stroke:#2f9e44
```

### Datenfluss im Detail

```mermaid
flowchart LR
    subgraph step1["1. JSON Laden"]
        direction TB
        RAW["transactions.json<br/>Nested Structure"]
        RAW --> |"spark.read.json()"| DF1["DataFrame<br/>382.402 TXs"]
    end

    subgraph step2["2. Explode"]
        direction TB
        DF1 --> EXPL["explode_outer()"]
        EXPL --> OUTS["outputs_df<br/>769.081 Zeilen"]
        EXPL --> INPS["inputs_df<br/>632.295 Zeilen"]
    end

    subgraph step3["3. UTXO"]
        direction TB
        OUTS --> JOIN["LEFT ANTI JOIN"]
        INPS --> |"spent refs"| JOIN
        JOIN --> UTXO["utxos_df<br/>177.041 UTXOs"]
    end

    subgraph step4["4. Clustering"]
        direction TB
        FILTER["filter:<br/>2 <= inputs <= 50<br/>!is_coinbase"]
        FILTER --> GRAPH["GraphFrame<br/>147.907 Vertices<br/>400.872 Edges"]
        GRAPH --> CC["Connected<br/>Components"]
        CC --> RESULT["entities_df<br/>~110.000 Entities"]
    end

    step1 --> step2 --> step3
    step2 --> step4

    style RAW fill:#868e96,color:#fff
    style RESULT fill:#51cf66,stroke:#2f9e44
```

---

## Datenmodell

### Schema-Ubersicht

```mermaid
erDiagram
    TRANSACTION {
        string hash PK
        long block_number
        long block_timestamp
        boolean is_coinbase
        int input_count
        int output_count
        long fee
    }

    OUTPUT {
        string tx_hash FK
        int output_index
        long value
        array addresses
        string output_type
    }

    INPUT {
        string tx_hash FK
        int input_index
        string spent_tx_hash FK
        int spent_output_index FK
        long value
    }

    UTXO {
        string tx_hash FK
        int output_index
        long value
        array addresses
    }

    ENTITY {
        string address PK
        long entity_id
    }

    TRANSACTION ||--o{ OUTPUT : "has"
    TRANSACTION ||--o{ INPUT : "has"
    INPUT }o--|| OUTPUT : "spends"
    OUTPUT ||--o| UTXO : "if unspent"
    OUTPUT }o--|| ENTITY : "belongs to"
```

### Physisches Datenmodell (Parquet)

```mermaid
flowchart TB
    subgraph outputs_parquet["outputs.parquet"]
        O1["tx_hash: string"]
        O2["block_number: long"]
        O3["block_timestamp: long"]
        O4["output_index: int"]
        O5["value: long (satoshi)"]
        O6["addresses: array<string>"]
        O7["output_type: string"]
    end

    subgraph inputs_parquet["inputs.parquet"]
        I1["tx_hash: string"]
        I2["block_number: long"]
        I3["input_index: int"]
        I4["spent_tx_hash: string"]
        I5["spent_output_index: int"]
        I6["value: long"]
    end

    subgraph utxos_parquet["utxos.parquet"]
        U1["tx_hash: string"]
        U2["output_index: int"]
        U3["value: long"]
        U4["addresses: array"]
    end

    subgraph entities_parquet["entities.parquet"]
        E1["address: string"]
        E2["entity_id: long"]
    end

    style outputs_parquet fill:#e7f5ff,stroke:#1c7ed6
    style inputs_parquet fill:#fff3bf,stroke:#fab005
    style utxos_parquet fill:#d3f9d8,stroke:#2f9e44
    style entities_parquet fill:#ffe3e3,stroke:#fa5252
```

---

## Algorithmen

### Common Input Ownership Heuristic

```mermaid
flowchart TB
    subgraph heuristic["Heuristik"]
        H1["Wenn eine TX mehrere<br/>Input-Adressen hat..."]
        H2["...muss der Absender<br/>alle Private Keys besitzen"]
        H3["...also gehoren alle<br/>Adressen derselben Entity"]
    end

    H1 --> H2 --> H3

    subgraph exception["Ausnahmen"]
        E1["CoinJoin<br/>(Privacy-Protokoll)"]
        E2["Exchange Consolidation<br/>(viele Kunden)"]
        E3["Mining Pool Payouts"]
    end

    subgraph filter["Filter-Strategie"]
        F1["max_inputs <= 50"]
        F2["Pattern Detection"]
        F3["Known Address Lists"]
    end

    H3 --> exception
    exception --> filter

    style heuristic fill:#d3f9d8,stroke:#2f9e44
    style exception fill:#ffe3e3,stroke:#fa5252
    style filter fill:#e7f5ff,stroke:#1c7ed6
```

### Connected Components Algorithmus

```mermaid
flowchart TB
    subgraph init["Initialisierung"]
        I1["Jeder Knoten erhalt<br/>eigene Component-ID"]
    end

    subgraph iterate["Iteration"]
        IT1["Sende eigene ID<br/>an Nachbarn"]
        IT2["Empfange IDs<br/>von Nachbarn"]
        IT3["Ubernehme kleinste ID"]
        IT4{"Anderungen?"}

        IT1 --> IT2 --> IT3 --> IT4
        IT4 -->|"Ja"| IT1
        IT4 -->|"Nein"| DONE["Fertig"]
    end

    subgraph checkpoint["Checkpointing"]
        CP["Alle N Iterationen:<br/>Zustand auf Disk speichern<br/>Lineage truncaten"]
    end

    init --> iterate
    iterate --> checkpoint
    checkpoint -->|"weiter"| iterate

    style checkpoint fill:#fff3bf,stroke:#fab005
```

### UTXO Set Berechnung

```mermaid
flowchart LR
    subgraph inputs["Alle Outputs"]
        ALL["outputs_df<br/>769.081 Zeilen"]
    end

    subgraph spent["Spent References"]
        REFS["inputs_df<br/>WHERE spent_tx_hash IS NOT NULL"]
    end

    subgraph join["LEFT ANTI JOIN"]
        J["outputs NOT IN spent_refs"]
    end

    subgraph result["UTXO Set"]
        UTXO["utxos_df<br/>177.041 Zeilen"]
    end

    ALL --> join
    REFS --> join
    join --> UTXO

    style UTXO fill:#51cf66,stroke:#2f9e44
```

---

## Performance-Uberlegungen

### Spark-Konfiguration

```mermaid
flowchart TB
    subgraph config["SparkSession Config"]
        C1["driver.memory: 8g"]
        C2["adaptive.enabled: true"]
        C3["adaptive.coalescePartitions: true"]
        C4["adaptive.skewJoin.enabled: true"]
        C5["shuffle.partitions: 200"]
    end

    subgraph benefit["Vorteile"]
        B1["Genug RAM fur Broadcasts"]
        B2["Dynamische Query-Optimierung"]
        B3["Weniger kleine Files"]
        B4["Bessere Skew-Handling"]
        B5["Parallelitat bei Joins"]
    end

    C1 --> B1
    C2 --> B2
    C3 --> B3
    C4 --> B4
    C5 --> B5

    style config fill:#e7f5ff,stroke:#1c7ed6
    style benefit fill:#d3f9d8,stroke:#2f9e44
```

### Bottlenecks und Losungen

```mermaid
flowchart TB
    subgraph bottleneck["Bottlenecks"]
        BN1["JSON Parsing<br/>langsam, kein Schema"]
        BN2["Shuffle bei Joins<br/>Netzwerk-intensiv"]
        BN3["Graph Iterations<br/>Lineage explodiert"]
        BN4["Skewed Data<br/>Wenige grosse Entities"]
    end

    subgraph solution["Losungen"]
        S1["Schema vorgeben<br/>Parquet speichern"]
        S2["Broadcast Joins<br/>Partitionierung"]
        S3["Checkpointing<br/>alle 2 Iterationen"]
        S4["Adaptive Skew Join<br/>Salting"]
    end

    BN1 --> S1
    BN2 --> S2
    BN3 --> S3
    BN4 --> S4

    style bottleneck fill:#ffe3e3,stroke:#fa5252
    style solution fill:#d3f9d8,stroke:#2f9e44
```

### Skalierungsverhalten

```mermaid
flowchart LR
    subgraph small["Testdaten (H1 2011)"]
        SM1["382k TXs"]
        SM2["769k Outputs"]
        SM3["~2 Min Clustering"]
    end

    subgraph medium["1 Jahr (2015)"]
        MD1["~50M TXs"]
        MD2["~100M Outputs"]
        MD3["~30 Min Clustering"]
    end

    subgraph full["Volle Blockchain"]
        FL1["900M+ TXs"]
        FL2["2B+ Outputs"]
        FL3["~8h auf Cluster"]
    end

    small -->|"x100"| medium -->|"x20"| full

    style small fill:#d3f9d8,stroke:#2f9e44
    style medium fill:#fff3bf,stroke:#fab005
    style full fill:#ffe3e3,stroke:#fa5252
```

---

## Codestruktur

### Modul-Ubersicht

```mermaid
flowchart TB
    subgraph notebooks["notebooks/"]
        NB1["01_entity_clustering.ipynb<br/>Hauptanalyse"]
        NB2["00_test_blockchair_loading.ipynb<br/>Datentest"]
    end

    subgraph src["src/"]
        ETL["etl.py"]
        subgraph functions["Funktionen"]
            F1["create_spark_session()"]
            F2["load_transactions()"]
            F3["load_blocks()"]
            F4["explode_outputs()"]
            F5["explode_inputs()"]
            F6["compute_utxo_set()"]
            F7["enrich_clustering_inputs()"]
        end
    end

    subgraph data["data/"]
        D1["outputs.parquet"]
        D2["inputs.parquet"]
        D3["utxos.parquet"]
        D4["entities.parquet"]
    end

    NB1 --> |"import"| ETL
    ETL --> functions
    functions --> |"write"| data

    style notebooks fill:#e7f5ff,stroke:#1c7ed6
    style src fill:#fff3bf,stroke:#fab005
    style data fill:#d3f9d8,stroke:#2f9e44
```

### Funktionsabhangigkeiten

```mermaid
flowchart TB
    CS["create_spark_session()"]

    CS --> LT["load_transactions()"]
    CS --> LB["load_blocks()"]

    LT --> EO["explode_outputs()"]
    LT --> EI["explode_inputs()"]

    EO --> CU["compute_utxo_set()"]
    EI --> CU

    LT --> EC["enrich_clustering_inputs()"]
    EO --> EC

    EC --> GF["GraphFrames<br/>connectedComponents()"]

    style CS fill:#74c0fc,stroke:#1c7ed6
    style GF fill:#ff8787,stroke:#c92a2a
```

---

## Deployment-Optionen

### Lokale Entwicklung

```mermaid
flowchart LR
    subgraph local["Lokales Setup"]
        JUP["Jupyter Lab"]
        SPARK["Spark Local[*]"]
        DATA["~10 GB Testdaten"]
    end

    JUP --> SPARK --> DATA

    style local fill:#d3f9d8,stroke:#2f9e44
```

### Cluster-Deployment (Produktiv)

```mermaid
flowchart TB
    subgraph cluster["Spark Cluster"]
        MASTER["Spark Master"]
        W1["Worker 1<br/>32 GB RAM"]
        W2["Worker 2<br/>32 GB RAM"]
        W3["Worker 3<br/>32 GB RAM"]
    end

    subgraph storage_cluster["Distributed Storage"]
        HDFS["HDFS / S3"]
    end

    subgraph orchestration["Orchestrierung"]
        AIRFLOW["Apache Airflow"]
    end

    AIRFLOW --> MASTER
    MASTER --> W1 & W2 & W3
    W1 & W2 & W3 <--> HDFS

    style cluster fill:#e7f5ff,stroke:#1c7ed6
    style storage_cluster fill:#fff3bf,stroke:#fab005
```

---

## Erweiterungsmoglichkeiten

### Geplante Features

```mermaid
flowchart TB
    subgraph current["Aktuell implementiert"]
        C1["Entity Clustering"]
        C2["UTXO Berechnung"]
    end

    subgraph planned["Geplant"]
        P1["Whale Detection<br/>Balance pro Entity"]
        P2["Verhaltensanalyse<br/>Akkumulation/Distribution"]
        P3["Time Series<br/>Entity-Wachstum"]
    end

    subgraph future["Zukunft"]
        F1["Exchange Detection"]
        F2["Anomalie-Erkennung"]
        F3["Real-time Streaming"]
    end

    current --> planned --> future

    style current fill:#51cf66,stroke:#2f9e44
    style planned fill:#ffd43b,stroke:#f08c00
    style future fill:#868e96,color:#fff
```

### Integration mit anderen Systemen

```mermaid
flowchart TB
    subgraph core["Bitcoin Whale Intelligence"]
        ENTITIES["entities.parquet"]
        UTXOS["utxos.parquet"]
    end

    subgraph integrations["Mogliche Integrationen"]
        CHAIN["Chainalysis<br/>Labeled Addresses"]
        PRICE["Price APIs<br/>Coingecko, etc."]
        GRAPH["Neo4j<br/>Graph Visualization"]
        DASH["Dashboard<br/>Grafana/Superset"]
    end

    ENTITIES --> CHAIN
    ENTITIES --> GRAPH
    UTXOS --> PRICE
    ENTITIES & UTXOS --> DASH

    style core fill:#d3f9d8,stroke:#2f9e44
    style integrations fill:#e7f5ff,stroke:#1c7ed6
```
