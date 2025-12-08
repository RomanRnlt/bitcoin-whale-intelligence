# Bitcoin Whale Intelligence - Notebook Workflow

> Ubersicht uber die Analyse-Pipeline: Notebooks, Status und Datenfluss

---

## Gesamtubersicht der Pipeline

```mermaid
flowchart TB
    subgraph done["Erledigt"]
        NB0["00_test_blockchair_loading<br/>Datentest"]
        NB1["01_entity_clustering<br/>Haupt-Pipeline"]
    end

    subgraph planned["Geplant"]
        NB2["02_whale_detection<br/>Balance-Analyse"]
        NB3["03_behavior_analysis<br/>Akkumulation/Distribution"]
        NB4["04_visualization<br/>Dashboard & Charts"]
    end

    NB0 --> NB1
    NB1 --> NB2
    NB2 --> NB3
    NB3 --> NB4

    style done fill:#51cf66,stroke:#2f9e44
    style planned fill:#868e96,color:#fff
```

---

## Status-Ubersicht

| Notebook | Status | Beschreibung |
|----------|--------|--------------|
| `00_test_blockchair_loading` | Erledigt | Testen der Blockchair-Datenstruktur |
| `01_entity_clustering` | Erledigt | Komplette Pipeline bis Entity-Mapping |
| `02_whale_detection` | Geplant | Balance pro Entity berechnen |
| `03_behavior_analysis` | Geplant | Akkumulation vs. Distribution |
| `04_visualization` | Geplant | Charts und Dashboard |

---

## Notebook 01: Entity Clustering (Fertig)

### Workflow-Diagramm

```mermaid
flowchart TB
    subgraph step1["Schritt 1: Setup"]
        S1A["Spark Session erstellen"]
        S1B["GraphFrames laden"]
        S1C["Pfade konfigurieren"]
        S1A --> S1B --> S1C
    end

    subgraph step2["Schritt 2: Daten laden"]
        S2A["load_transactions()"]
        S2B["load_blocks()"]
        S2C["Cache aktivieren"]
        S2A --> S2C
        S2B --> S2C
    end

    subgraph step3["Schritt 3: ETL"]
        S3A["explode_outputs()"]
        S3B["explode_inputs()"]
        S3C["Parquet speichern"]
        S3A --> S3C
        S3B --> S3C
    end

    subgraph step4["Schritt 4: UTXO"]
        S4A["compute_utxo_set()"]
        S4B["Parquet speichern"]
        S4A --> S4B
    end

    subgraph step5["Schritt 5: Clustering"]
        S5A["Multi-Input TXs filtern"]
        S5B["Adressen anreichern"]
        S5C["Graph erstellen"]
        S5D["Connected Components"]
        S5E["Entities speichern"]
        S5A --> S5B --> S5C --> S5D --> S5E
    end

    step1 --> step2 --> step3 --> step4 --> step5

    style step1 fill:#e7f5ff,stroke:#1c7ed6
    style step2 fill:#fff3bf,stroke:#fab005
    style step3 fill:#d3f9d8,stroke:#2f9e44
    style step4 fill:#ffe3e3,stroke:#fa5252
    style step5 fill:#e599f7,stroke:#9c36b5
```

### Input/Output Ubersicht

```mermaid
flowchart LR
    subgraph inputs["Inputs"]
        I1[("blockchain_exports/<br/>transactions/*.json")]
        I2[("blockchain_exports/<br/>blocks/*.json")]
    end

    subgraph processing["Verarbeitung"]
        P["01_entity_clustering.ipynb"]
    end

    subgraph outputs["Outputs"]
        O1[("data/outputs.parquet")]
        O2[("data/inputs.parquet")]
        O3[("data/utxos.parquet")]
        O4[("data/entities.parquet")]
    end

    I1 --> P
    I2 --> P
    P --> O1 & O2 & O3 & O4

    style inputs fill:#868e96,color:#fff
    style processing fill:#74c0fc,stroke:#1c7ed6
    style outputs fill:#51cf66,stroke:#2f9e44
```

### Ergebnisse Notebook 01

```mermaid
flowchart TB
    subgraph metrics["Metriken"]
        M1["Transaktionen: 382.402"]
        M2["Blocks: 27.644"]
        M3["Outputs: 769.081"]
        M4["UTXOs: 177.041"]
        M5["Adressen: ~150.000"]
        M6["Entities: ~110.000"]
    end

    subgraph reduction["Reduktion"]
        R["~25% weniger<br/>'Besitzer' durch Clustering"]
    end

    M5 --> |"Clustering"| M6
    M6 --> R

    style metrics fill:#e7f5ff,stroke:#1c7ed6
    style reduction fill:#ff8787,stroke:#c92a2a
```

---

## Notebook 02: Whale Detection (Geplant)

### Geplanter Workflow

```mermaid
flowchart TB
    subgraph load["Daten laden"]
        L1["entities.parquet laden"]
        L2["utxos.parquet laden"]
    end

    subgraph join["Join"]
        J["Entity-ID zu jedem UTXO"]
    end

    subgraph aggregate["Aggregation"]
        A1["SUM(value) pro Entity"]
        A2["COUNT(utxos) pro Entity"]
        A3["COUNT(addresses) pro Entity"]
    end

    subgraph classify["Klassifikation"]
        C1{"Balance >= 1000 BTC?"}
        C2["Whale"]
        C3["Normal"]
        C1 -->|"Ja"| C2
        C1 -->|"Nein"| C3
    end

    subgraph output["Output"]
        O[("data/whale_entities.parquet")]
    end

    load --> join --> aggregate --> classify --> output

    style load fill:#e7f5ff,stroke:#1c7ed6
    style classify fill:#ff8787,stroke:#c92a2a
    style output fill:#51cf66,stroke:#2f9e44
```

### Geplante Inputs/Outputs

```mermaid
flowchart LR
    subgraph inputs["Inputs"]
        I1[("data/entities.parquet")]
        I2[("data/utxos.parquet")]
    end

    subgraph processing["Verarbeitung"]
        P["02_whale_detection.ipynb"]
    end

    subgraph outputs["Outputs"]
        O1[("data/entity_balances.parquet")]
        O2[("data/whale_entities.parquet")]
    end

    I1 --> P
    I2 --> P
    P --> O1 & O2

    style inputs fill:#868e96,color:#fff
    style processing fill:#74c0fc,stroke:#1c7ed6
    style outputs fill:#51cf66,stroke:#2f9e44
```

### Erwartete Analyse

```mermaid
pie showData
    title "Erwartete Whale-Verteilung"
    "Keine Wale (< 100 BTC)" : 95
    "Kleine Wale (100-1000 BTC)" : 4
    "Grosse Wale (> 1000 BTC)" : 1
```

---

## Notebook 03: Verhaltensanalyse (Geplant)

### Geplanter Workflow

```mermaid
flowchart TB
    subgraph timerange["Zeitraum-Analyse"]
        T1["Entity-Balance<br/>pro Woche/Monat"]
    end

    subgraph delta["Delta-Berechnung"]
        D1["Balance(t) - Balance(t-1)"]
    end

    subgraph classify["Klassifikation"]
        C1{"Delta > 0?"}
        C2["Akkumulation<br/>(kauft zu)"]
        C3["Distribution<br/>(verkauft)"]
        C4["Dormant<br/>(halt)"]

        C1 -->|"Positiv"| C2
        C1 -->|"Negativ"| C3
        C1 -->|"~0"| C4
    end

    subgraph pattern["Pattern Detection"]
        P1["Kontinuierliche Akkumulation"]
        P2["Plotzlicher Dump"]
        P3["Zyklisches Verhalten"]
    end

    timerange --> delta --> classify --> pattern

    style classify fill:#fff3bf,stroke:#fab005
    style pattern fill:#d3f9d8,stroke:#2f9e44
```

### Geplante Visualisierungen

```mermaid
flowchart TB
    subgraph charts["Geplante Charts"]
        CH1["Timeline: Whale Balance uber Zeit"]
        CH2["Heatmap: Aktivitat pro Woche"]
        CH3["Scatter: Balance vs. Aktivitat"]
        CH4["Bar: Top 10 Akkumulatoren"]
    end

    subgraph insights["Erkenntnisse"]
        IN1["Markt-Sentiment"]
        IN2["Vorhersage-Signale"]
        IN3["Netzwerk-Gesundheit"]
    end

    charts --> insights

    style charts fill:#e7f5ff,stroke:#1c7ed6
    style insights fill:#d3f9d8,stroke:#2f9e44
```

---

## Notebook 04: Visualization (Geplant)

### Geplante Dashboards

```mermaid
flowchart TB
    subgraph dash1["Dashboard 1: Whale Tracker"]
        D1A["Top 20 Wale"]
        D1B["Ihre Balances"]
        D1C["Letzte Aktivitat"]
    end

    subgraph dash2["Dashboard 2: Netzwerk-Ubersicht"]
        D2A["Entity-Verteilung"]
        D2B["Clustering-Metriken"]
        D2C["UTXO-Statistiken"]
    end

    subgraph dash3["Dashboard 3: Zeitreihen"]
        D3A["Whale-Balance-Entwicklung"]
        D3B["Akkumulation/Distribution"]
        D3C["Netzwerk-Wachstum"]
    end

    style dash1 fill:#ff8787,stroke:#c92a2a
    style dash2 fill:#74c0fc,stroke:#1c7ed6
    style dash3 fill:#51cf66,stroke:#2f9e44
```

---

## Datenfluss: Komplette Pipeline

```mermaid
flowchart TB
    subgraph source["Datenquelle"]
        BTC[("Bitcoin Node")]
        EXPORT["bitcoin-etl"]
        BTC --> EXPORT
    end

    subgraph nb01["Notebook 01"]
        LOAD["Laden"]
        ETL["ETL"]
        UTXO["UTXO"]
        CLUSTER["Clustering"]
        LOAD --> ETL --> UTXO --> CLUSTER
    end

    subgraph nb02["Notebook 02"]
        BALANCE["Balance"]
        WHALE["Whale Detection"]
        BALANCE --> WHALE
    end

    subgraph nb03["Notebook 03"]
        BEHAVIOR["Verhaltensanalyse"]
    end

    subgraph nb04["Notebook 04"]
        VIS["Visualisierung"]
    end

    subgraph outputs["Outputs"]
        O1[("outputs.parquet")]
        O2[("inputs.parquet")]
        O3[("utxos.parquet")]
        O4[("entities.parquet")]
        O5[("entity_balances.parquet")]
        O6[("whale_entities.parquet")]
        O7[("behavior_metrics.parquet")]
    end

    EXPORT --> nb01
    nb01 --> O1 & O2 & O3 & O4
    O3 & O4 --> nb02
    nb02 --> O5 & O6
    O5 & O6 --> nb03
    nb03 --> O7
    O4 & O5 & O6 & O7 --> nb04

    style source fill:#868e96,color:#fff
    style nb01 fill:#51cf66,stroke:#2f9e44
    style nb02 fill:#ffd43b,stroke:#f08c00
    style nb03 fill:#ffd43b,stroke:#f08c00
    style nb04 fill:#ffd43b,stroke:#f08c00
```

---

## Detaillierter Input/Output je Schritt

### Schritt-fur-Schritt Transformation

```mermaid
flowchart LR
    subgraph s1["1. Load"]
        I1[("JSON")]
        O1["DataFrame"]
        I1 --> O1
    end

    subgraph s2["2. Explode"]
        I2["DataFrame<br/>nested"]
        O2["DataFrames<br/>flat"]
        I2 --> O2
    end

    subgraph s3["3. UTXO"]
        I3["outputs +<br/>inputs"]
        O3["utxos"]
        I3 --> O3
    end

    subgraph s4["4. Enrich"]
        I4["transactions +<br/>outputs"]
        O4["tx_hash,<br/>address"]
        I4 --> O4
    end

    subgraph s5["5. Graph"]
        I5["addresses"]
        O5["vertices +<br/>edges"]
        I5 --> O5
    end

    subgraph s6["6. CC"]
        I6["GraphFrame"]
        O6["entities"]
        I6 --> O6
    end

    s1 --> s2 --> s3
    s2 --> s4 --> s5 --> s6

    style s1 fill:#e7f5ff
    style s2 fill:#fff3bf
    style s3 fill:#d3f9d8
    style s4 fill:#ffe3e3
    style s5 fill:#e599f7
    style s6 fill:#74c0fc
```

### Datenvolumen pro Schritt

| Schritt | Input | Output | Volumen |
|---------|-------|--------|---------|
| Load | JSON | DataFrame | 382.402 TXs |
| Explode Outputs | 382k TXs | Flat Outputs | 769.081 Zeilen |
| Explode Inputs | 382k TXs | Flat Inputs | 632.295 Zeilen |
| UTXO | 769k + 632k | UTXOs | 177.041 Zeilen |
| Enrich | 382k + 769k | Clustering Inputs | 274.791 Zeilen |
| Graph | 57.606 TXs | Vertices + Edges | 147.907 + 400.872 |
| CC | Graph | Entities | ~110.000 Entities |

---

## Ausfuhrungs-Reihenfolge

```mermaid
sequenceDiagram
    participant User
    participant NB01 as 01_entity_clustering
    participant NB02 as 02_whale_detection
    participant NB03 as 03_behavior_analysis
    participant NB04 as 04_visualization

    User->>NB01: Ausfuhren
    activate NB01
    NB01-->>User: outputs.parquet
    NB01-->>User: inputs.parquet
    NB01-->>User: utxos.parquet
    NB01-->>User: entities.parquet
    deactivate NB01

    User->>NB02: Ausfuhren
    activate NB02
    Note over NB02: Ladt entities + utxos
    NB02-->>User: entity_balances.parquet
    NB02-->>User: whale_entities.parquet
    deactivate NB02

    User->>NB03: Ausfuhren
    activate NB03
    Note over NB03: Ladt balances + whales
    NB03-->>User: behavior_metrics.parquet
    deactivate NB03

    User->>NB04: Ausfuhren
    activate NB04
    Note over NB04: Ladt alle Outputs
    NB04-->>User: Charts & Dashboard
    deactivate NB04
```

---

## Checkliste

### Notebook 01 - Entity Clustering

- [x] Spark Session konfigurieren
- [x] Transaktionen laden (JSON)
- [x] Blocks laden (JSON)
- [x] Outputs explodieren
- [x] Inputs explodieren
- [x] Parquet speichern (outputs, inputs)
- [x] UTXO Set berechnen
- [x] Parquet speichern (utxos)
- [x] Multi-Input TXs filtern
- [x] Adressen anreichern
- [x] Graph aufbauen (Vertices, Edges)
- [x] Connected Components ausfuhren
- [x] Parquet speichern (entities)
- [x] Statistiken visualisieren

### Notebook 02 - Whale Detection (Geplant)

- [ ] Entities laden
- [ ] UTXOs laden
- [ ] Join: UTXO -> Entity
- [ ] Aggregation: Balance pro Entity
- [ ] Klassifikation: Whale ja/nein
- [ ] Top Whales identifizieren
- [ ] Parquet speichern

### Notebook 03 - Verhaltensanalyse (Geplant)

- [ ] Balance-Zeitreihen erstellen
- [ ] Delta berechnen
- [ ] Akkumulation/Distribution klassifizieren
- [ ] Pattern Detection
- [ ] Metriken speichern

### Notebook 04 - Visualization (Geplant)

- [ ] Alle Daten laden
- [ ] Dashboard: Whale Tracker
- [ ] Dashboard: Netzwerk-Ubersicht
- [ ] Dashboard: Zeitreihen
- [ ] Export: Charts
