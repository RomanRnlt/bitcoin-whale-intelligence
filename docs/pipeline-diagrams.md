# Bitcoin Whale Intelligence - Pipeline Diagramme

---

## Das Problem

```mermaid
flowchart LR
    subgraph blockchain["Blockchain"]
        A["Adresse A<br/>500 BTC"]
        B["Adresse B<br/>300 BTC"]
        C["Adresse C<br/>200 BTC"]
    end

    subgraph hidden["Versteckt"]
        W["1 Person<br/>1.000 BTC"]
    end

    A --> W
    B --> W
    C --> W

    style W fill:#ff6b6b,color:#fff
```

---

## Bitcoin: UTXO-Modell

```mermaid
flowchart LR
    subgraph inputs["Inputs (Muenzen ausgeben)"]
        I1["0.5 BTC"]
        I2["0.3 BTC"]
    end

    TX["Transaktion"]

    subgraph outputs["Outputs (Neue Muenzen)"]
        O1["0.7 BTC<br/>Empfaenger"]
        O2["0.09 BTC<br/>Wechselgeld"]
    end

    I1 --> TX
    I2 --> TX
    TX --> O1
    TX --> O2
```

---

## Private Key = Besitzbeweis

```mermaid
flowchart TB
    subgraph keys["Pro Adresse"]
        PK["Private Key<br/>Geheim"]
        ADDR["Adresse<br/>Oeffentlich"]
        PK -->|"erzeugt"| ADDR
    end

    subgraph actions["Aktionen"]
        REC["Empfangen<br/>Adresse reicht"]
        SEND["Ausgeben<br/>Private Key noetig"]
    end

    ADDR --> REC
    PK --> SEND

    style PK fill:#ffcdd2
    style ADDR fill:#c8e6c9
```

---

## Common Input Ownership Heuristic

```mermaid
flowchart TB
    subgraph tx["Transaktion"]
        I1["Input: Adresse A<br/>braucht Key A"]
        I2["Input: Adresse B<br/>braucht Key B"]
        O["Output"]
        I1 --> O
        I2 --> O
    end

    subgraph result["Ergebnis"]
        R["A + B<br/>= SELBER BESITZER"]
    end

    tx --> result
    style result fill:#fff9c4
```

---

## Inputs vs Outputs

```mermaid
flowchart LR
    subgraph inputs["INPUTS"]
        A["A"]
        B["B"]
    end

    TX["TX"]

    subgraph outputs["OUTPUTS"]
        C["C"]
        D["D"]
    end

    A --> TX
    B --> TX
    TX --> C
    TX --> D

    R1["A+B = Selber Besitzer"]
    R2["C+D = Unbekannt"]

    inputs -.-> R1
    outputs -.-> R2

    style R1 fill:#c8e6c9
    style R2 fill:#ffcdd2
```

---

## Datenquelle

```mermaid
flowchart LR
    NODE["Bitcoin<br/>Full Node"]
    ETL["bitcoin-etl"]
    JSON["JSON<br/>Dateien"]

    NODE --> ETL --> JSON

    style NODE fill:#ffcc80
    style JSON fill:#c8e6c9
```

---

## Pipeline Gesamtuebersicht

```mermaid
flowchart TB
    JSON[("JSON")]

    S1["Schritt 1<br/>Outputs extrahieren"]
    S2["Schritt 2<br/>Inputs extrahieren"]
    S3["Schritt 3<br/>UTXO berechnen"]
    S4a["Schritt 4a<br/>Multi-Input Gruppierung"]
    S4b["Schritt 4b<br/>Connected Components"]
    S5["Schritt 5<br/>Whale Detection"]

    OUT[("outputs")]
    INP[("inputs")]
    UTXO[("utxos")]
    ENT[("entities")]
    WHALE[("Wale")]

    JSON --> S1 --> OUT
    JSON --> S2 --> INP
    OUT --> S3
    INP --> S3
    S3 --> UTXO
    INP --> S4a --> S4b --> ENT
    UTXO --> S5
    ENT --> S5
    S5 --> WHALE

    style JSON fill:#e3f2fd
    style WHALE fill:#ff6b6b,color:#fff
```

---

## Schritt 1: Outputs extrahieren

```mermaid
flowchart LR
    subgraph before["Vorher: Nested"]
        N["tx: abc<br/>outputs: [0:10, 1:5]"]
    end

    subgraph after["Nachher: Flach"]
        F1["abc | 0 | 10"]
        F2["abc | 1 | 5"]
    end

    before -->|"explode"| after
```

---

## Schritt 2: Inputs extrahieren

```mermaid
flowchart LR
    subgraph before["Vorher: Nested"]
        N["tx: abc<br/>inputs: [spent:xyz:0]"]
    end

    subgraph after["Nachher: Flach"]
        F["abc | xyz | 0"]
    end

    before -->|"explode"| after
```

---

## Schritt 3: UTXO berechnen

```mermaid
flowchart TB
    subgraph all["Alle Outputs"]
        O1["TX-1:0"]
        O2["TX-1:1"]
        O3["TX-2:0"]
    end

    subgraph spent["Spent"]
        S["TX-1:0"]
    end

    subgraph utxo["UTXOs"]
        U1["TX-1:1"]
        U2["TX-2:0"]
    end

    all -->|"LEFT ANTI JOIN"| utxo
    spent -.->|"entfernt"| O1

    style O1 fill:#ffcdd2
    style U1 fill:#c8e6c9
    style U2 fill:#c8e6c9
```

---

## Schritt 4a: Multi-Input Gruppierung

```mermaid
flowchart TB
    subgraph txs["Transaktionen"]
        T1["TX-1: A, B"]
        T2["TX-2: B, C"]
        T3["TX-3: D, E"]
    end

    subgraph edges["Kanten"]
        E1["A -- B"]
        E2["B -- C"]
        E3["D -- E"]
    end

    T1 --> E1
    T2 --> E2
    T3 --> E3
```

---

## Schritt 4b: Connected Components

```mermaid
flowchart LR
    subgraph addressGraph["Graph"]
        A((A)) --- B((B))
        B --- C((C))
        D((D)) --- E((E))
        F((F))
    end

    subgraph entities["Entities"]
        E1["Entity 1<br/>A, B, C"]
        E2["Entity 2<br/>D, E"]
        E3["Entity 3<br/>F"]
    end

    addressGraph --> entities

    style E1 fill:#c8e6c9
    style E2 fill:#bbdefb
    style E3 fill:#fff9c4
```

---

## Transitive Verknuepfung

```mermaid
flowchart LR
    subgraph step1["TX-1"]
        A1((A)) --- B1((B))
    end

    subgraph step2["TX-2"]
        B2((B)) --- C2((C))
    end

    subgraph result["Ergebnis"]
        AR((A)) --- BR((B)) --- CR((C))
        R["Entity 1"]
    end

    step1 --> result
    step2 --> result

    style result fill:#c8e6c9
```

---

## Schritt 5: Whale Detection

```mermaid
flowchart LR
    ENT[("entities<br/>Addr->Entity")]
    UTXO[("utxos<br/>Addr->BTC")]

    JOIN["JOIN"]
    GROUP["GROUP BY<br/>SUM"]
    FILTER["Filter"]

    WHALE[("Wale")]

    ENT --> JOIN
    UTXO --> JOIN
    JOIN --> GROUP --> FILTER --> WHALE

    style WHALE fill:#ff6b6b,color:#fff
```

---

## Whale Beispiel

```mermaid
flowchart TB
    subgraph utxos["UTXOs"]
        A["A: 500"]
        B["B: 300"]
        C["C: 200"]
    end

    subgraph entity["Entity 1"]
        E["A + B + C"]
    end

    subgraph total["Summe"]
        T["1.000 BTC<br/>= WAL"]
    end

    utxos --> entity --> total

    style T fill:#ff6b6b,color:#fff
```

---

## Tech Stack

```mermaid
flowchart TB
    subgraph tech["Technologien"]
        SPARK["Spark<br/>Verteilung"]
        GF["GraphFrames<br/>Graphen"]
        PQ["Parquet<br/>Storage"]
        ETL["bitcoin-etl<br/>Export"]
    end

    subgraph why["Warum"]
        W1["Millionen TXs"]
        W2["Connected Components"]
        W3["Kompression"]
        W4["Standard-Format"]
    end

    SPARK --- W1
    GF --- W2
    PQ --- W3
    ETL --- W4
```

---

## Zusammenfassung

```mermaid
flowchart LR
    S1["1. Outputs<br/>explode"]
    S2["2. Inputs<br/>explode"]
    S3["3. UTXO<br/>LEFT ANTI JOIN"]
    S4a["4a. Kanten<br/>pro TX"]
    S4b["4b. Components<br/>transitiv"]
    S5["5. Whale<br/>JOIN+SUM"]

    S1 --> S3
    S2 --> S3
    S2 --> S4a --> S4b
    S3 --> S5
    S4b --> S5
```
