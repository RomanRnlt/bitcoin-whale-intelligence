# Bitcoin Whale Intelligence - Einfache Erklarung

> **Ziel**: Versteckte Bitcoin-Besitzer ("Wale") sichtbar machen, die ihr Vermogen auf viele Adressen verteilen.

---

## Das Problem: Wer besitzt wirklich die Bitcoin?

### Die Blockchain zeigt nur Adressen - keine Besitzer

```mermaid
flowchart LR
    subgraph blockchain["Was die Blockchain zeigt"]
        A1[Adresse 1<br/>5 BTC]
        A2[Adresse 2<br/>3 BTC]
        A3[Adresse 3<br/>7 BTC]
        A4[Adresse 4<br/>2 BTC]
        A5[Adresse 5<br/>8 BTC]
    end

    subgraph reality["Realitat - unsichtbar!"]
        P1((Person A<br/>15 BTC))
        P2((Person B<br/>10 BTC))
    end

    A1 -.-> P1
    A2 -.-> P1
    A3 -.-> P1
    A4 -.-> P2
    A5 -.-> P2

    style P1 fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style P2 fill:#4ecdc4,stroke:#087f5b,color:#fff
    style blockchain fill:#f8f9fa,stroke:#868e96
    style reality fill:#fff3bf,stroke:#fab005
```

### Das Wal-Problem visualisiert

```mermaid
pie showData
    title "Scheinbare Verteilung (800 Mio. Adressen)"
    "Kleine Besitzer" : 750
    "Mittlere Besitzer" : 45
    "Grosse Besitzer" : 5
```

```mermaid
pie showData
    title "Echte Verteilung nach Clustering"
    "Kleine Besitzer" : 400
    "Mittlere Besitzer" : 80
    "Wale (versteckt!)" : 20
```

---

## Wie funktioniert Bitcoin? Das UTXO-Modell

### Bank vs. Bitcoin: Ein fundamentaler Unterschied

```mermaid
flowchart TB
    subgraph bank["Traditionelle Bank"]
        direction TB
        K1[Konto: 100 EUR]
        K1 -->|"Zahle 30 EUR"| K2[Konto: 70 EUR]
        K2 -->|"Erhalte 50 EUR"| K3[Konto: 120 EUR]
    end

    subgraph bitcoin["Bitcoin UTXO-Modell"]
        direction TB
        M1[/"Munze: 0.5 BTC"/]
        M2[/"Munze: 0.3 BTC"/]
        M1 & M2 -->|"Kombinieren"| TX{Transaktion}
        TX -->|"An Bob"| M3[/"Neue Munze: 0.7 BTC"/]
        TX -->|"Wechselgeld"| M4[/"Neue Munze: 0.09 BTC"/]
        TX -->|"Gebuhr"| FEE[0.01 BTC an Miner]
    end

    style bank fill:#e7f5ff,stroke:#1c7ed6
    style bitcoin fill:#fff9db,stroke:#f59f00
    style TX fill:#ff8787,stroke:#c92a2a
```

### UTXO - Unspent Transaction Output

```mermaid
flowchart LR
    subgraph utxo_pool["UTXO Pool - Alle verfugbaren Munzen"]
        U1[/"UTXO 1<br/>0.5 BTC<br/>Adresse: abc..."/]
        U2[/"UTXO 2<br/>1.2 BTC<br/>Adresse: def..."/]
        U3[/"UTXO 3<br/>0.3 BTC<br/>Adresse: ghi..."/]
        U4[/"UTXO 4<br/>2.0 BTC<br/>Adresse: jkl..."/]
    end

    U1 -->|"ausgeben"| SPENT((Spent))
    U3 -->|"ausgeben"| SPENT

    style SPENT fill:#fa5252,stroke:#c92a2a,color:#fff
    style utxo_pool fill:#d3f9d8,stroke:#2f9e44
```

---

## Die Losung: Common Input Ownership Heuristic

### Der Trick: Wer kann mehrere Adressen gleichzeitig nutzen?

```mermaid
sequenceDiagram
    participant A1 as Adresse A1<br/>(0.5 BTC)
    participant A2 as Adresse A2<br/>(0.3 BTC)
    participant TX as Transaktion
    participant Bob as Bob

    Note over A1,A2: Alice besitzt beide Adressen

    A1->>TX: Input 1: 0.5 BTC
    A2->>TX: Input 2: 0.3 BTC

    Note over TX: Summe: 0.8 BTC

    TX->>Bob: Output: 0.7 BTC
    TX->>A1: Wechselgeld: 0.09 BTC
    TX-->>TX: Fee: 0.01 BTC

    Note over A1,A2: A1 und A2 mussen<br/>derselben Person gehoren!
```

### Warum funktioniert das?

```mermaid
flowchart TB
    subgraph key["Der Schlussel zur Erkenntnis"]
        Q[Frage: Wer kann eine<br/>Multi-Input TX signieren?]
        Q --> A[Antwort: Nur wer ALLE<br/>Private Keys besitzt]
        A --> C[Schlussfolgerung:<br/>Alle Input-Adressen<br/>gehoren EINER Person]
    end

    style Q fill:#e7f5ff,stroke:#1c7ed6
    style A fill:#fff3bf,stroke:#fab005
    style C fill:#d3f9d8,stroke:#2f9e44
```

### Beispiel: Multi-Input Transaktion entlarven

```mermaid
flowchart LR
    subgraph inputs["Inputs der Transaktion"]
        I1["Adresse: 1ABC...<br/>0.5 BTC"]
        I2["Adresse: 1DEF...<br/>0.3 BTC"]
        I3["Adresse: 1GHI...<br/>0.2 BTC"]
    end

    subgraph tx["Transaktion TX123"]
        COMBINE((Kombinieren))
    end

    subgraph outputs["Outputs"]
        O1["An Bob<br/>0.9 BTC"]
        O2["Wechselgeld<br/>0.08 BTC"]
    end

    I1 --> COMBINE
    I2 --> COMBINE
    I3 --> COMBINE
    COMBINE --> O1
    COMBINE --> O2

    subgraph conclusion["Erkenntnis"]
        E["1ABC, 1DEF, 1GHI<br/>= EINE Entity!"]
    end

    COMBINE -.->|"beweist"| E

    style E fill:#ff8787,stroke:#c92a2a,color:#fff
    style COMBINE fill:#ffd43b,stroke:#f08c00
```

---

## Entity Clustering: Der Graph-Algorithmus

### Von Transaktionen zum Graphen

```mermaid
flowchart TB
    subgraph step1["Schritt 1: Transaktionen analysieren"]
        TX1["TX1: Inputs von A + B"]
        TX2["TX2: Inputs von B + C"]
        TX3["TX3: Inputs von D + E"]
    end

    subgraph step2["Schritt 2: Graph aufbauen"]
        A((A)) --- B((B))
        B --- C((C))
        D((D)) --- E((E))
    end

    subgraph step3["Schritt 3: Connected Components"]
        subgraph entity1["Entity 1"]
            A2((A))
            B2((B))
            C2((C))
        end
        subgraph entity2["Entity 2"]
            D2((D))
            E2((E))
        end
    end

    step1 --> step2 --> step3

    style entity1 fill:#e7f5ff,stroke:#1c7ed6
    style entity2 fill:#fff3bf,stroke:#fab005
```

### Transitive Verknupfung: Warum es funktioniert

```mermaid
graph LR
    subgraph tx1["Transaktion 1"]
        A1((A)) ---|"gemeinsamer Input"| B1((B))
    end

    subgraph tx2["Transaktion 2"]
        B2((B)) ---|"gemeinsamer Input"| C1((C))
    end

    subgraph tx3["Transaktion 3"]
        C2((C)) ---|"gemeinsamer Input"| D1((D))
    end

    subgraph result["Ergebnis: Eine Entity"]
        AR((A)) --- BR((B)) --- CR((C)) --- DR((D))
    end

    tx1 & tx2 & tx3 --> result

    style result fill:#d3f9d8,stroke:#2f9e44
```

### Konkretes Beispiel aus echten Daten

```mermaid
graph TB
    subgraph before["Vor dem Clustering"]
        A1["1ABC..."]
        A2["1DEF..."]
        A3["1GHI..."]
        A4["1JKL..."]
        A5["1MNO..."]

        A1 -->|"TX1"| A2
        A2 -->|"TX2"| A3
        A3 -->|"TX3"| A4
        A1 -->|"TX4"| A5
    end

    subgraph after["Nach dem Clustering"]
        E1[/"Entity 12345<br/>Adressen: 5<br/>Balance: 25 BTC"/]
    end

    before -->|"Connected<br/>Components"| after

    style E1 fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

---

## Die komplette Pipeline

### Von Rohdaten bis zur Whale Detection

```mermaid
flowchart TB
    subgraph input["1. Datenquelle"]
        BTC[("Bitcoin<br/>Full Node")]
        ETL["bitcoin-etl<br/>Export"]
        JSON[("JSON Dateien<br/>Hive-partitioniert")]

        BTC --> ETL --> JSON
    end

    subgraph transform["2. Transformation"]
        SPARK["Apache Spark"]
        JSON --> SPARK

        subgraph parquet["Parquet Dateien"]
            OUT[("outputs.parquet")]
            INP[("inputs.parquet")]
            UTXO[("utxos.parquet")]
        end

        SPARK --> OUT & INP
        OUT & INP --> UTXO
    end

    subgraph cluster["3. Entity Clustering"]
        MULTI["Multi-Input TXs<br/>filtern"]
        GRAPH["Graph aufbauen<br/>Knoten: Adressen<br/>Kanten: Co-Inputs"]
        CC["Connected<br/>Components"]
        ENT[("entities.parquet")]

        OUT --> MULTI --> GRAPH --> CC --> ENT
    end

    subgraph analysis["4. Whale Detection"]
        BAL["Entity Balances<br/>berechnen"]
        WHALE["Wale<br/>identifizieren"]
        VIS["Visualisierung"]

        UTXO & ENT --> BAL --> WHALE --> VIS
    end

    style input fill:#e7f5ff,stroke:#1c7ed6
    style transform fill:#fff3bf,stroke:#fab005
    style cluster fill:#d3f9d8,stroke:#2f9e44
    style analysis fill:#ffe3e3,stroke:#fa5252
```

### Detaillierter ETL-Prozess

```mermaid
flowchart LR
    subgraph raw["Rohdaten"]
        TX["transactions.json<br/>Nested Arrays"]
    end

    subgraph explode["Explode"]
        TX -->|"explode_outputs()"| OUTS["outputs.parquet<br/>1 Zeile pro Output"]
        TX -->|"explode_inputs()"| INPS["inputs.parquet<br/>1 Zeile pro Input"]
    end

    subgraph compute["Berechnung"]
        OUTS -->|"LEFT ANTI JOIN"| UTXOS["utxos.parquet"]
        INPS -->|"Spent-Referenzen"| UTXOS
    end

    style raw fill:#868e96,color:#fff
    style UTXOS fill:#51cf66,stroke:#2f9e44
```

---

## Statistiken aus dem Projekt

### Transaktionstypen

```mermaid
pie showData
    title "Input-Verteilung (H1 2011 Daten)"
    "Single-Input (81%)" : 287512
    "Multi-Input 2-5 (15%)" : 55869
    "Multi-Input 6-10 (3%)" : 7086
    "Multi-Input 11+ (1%)" : 4291
```

### UTXO vs. Spent Outputs

```mermaid
pie showData
    title "Output Status"
    "Spent (77%)" : 592040
    "Unspent/UTXO (23%)" : 177041
```

### Clustering-Ergebnis

```mermaid
flowchart LR
    subgraph before["Vorher"]
        ADDR["~150.000<br/>Adressen"]
    end

    subgraph process["Clustering"]
        ALGO{{"Connected<br/>Components"}}
    end

    subgraph after["Nachher"]
        ENT["~110.000<br/>Entities"]
    end

    ADDR --> ALGO --> ENT

    RED["Reduktion:<br/>~25%"]
    ALGO -.-> RED

    style ADDR fill:#ff8787,stroke:#c92a2a,color:#fff
    style ENT fill:#51cf66,stroke:#2f9e44,color:#fff
    style RED fill:#fff3bf,stroke:#fab005
```

---

## Erwartete Ergebnisse

### Entity-Grossen nach Clustering

```mermaid
flowchart TB
    subgraph sizes["Entity-Grossen Verteilung"]
        direction LR
        S1["1-2 Adressen<br/>~80%"]
        S2["3-10 Adressen<br/>~15%"]
        S3["11-100 Adressen<br/>~4%"]
        S4["100+ Adressen<br/>~1%"]
    end

    subgraph interpretation["Interpretation"]
        I1["Gelegenheits-<br/>nutzer"]
        I2["Aktive<br/>Trader"]
        I3["Services/<br/>Handler"]
        I4["Exchanges/<br/>Wale"]
    end

    S1 --> I1
    S2 --> I2
    S3 --> I3
    S4 --> I4

    style S4 fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style I4 fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

### Was wir uber Wale lernen konnen

```mermaid
flowchart TB
    subgraph whale["Identifizierter Wal"]
        W[/"Entity #12345<br/>5.000 Adressen<br/>10.000 BTC"/]
    end

    subgraph analysis["Mogliche Analysen"]
        A1["Akkumulation?<br/>Kauft Bitcoin zu"]
        A2["Distribution?<br/>Verkauft Bitcoin"]
        A3["Dormant?<br/>Halt nur"]
        A4["Exchange?<br/>Viele kleine TXs"]
    end

    subgraph insight["Erkenntnisse"]
        I1["Markt-Sentiment"]
        I2["Preis-Impact"]
        I3["Netzwerk-Gesundheit"]
    end

    W --> A1 & A2 & A3 & A4
    A1 & A2 & A3 & A4 --> I1 & I2 & I3

    style W fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style insight fill:#d3f9d8,stroke:#2f9e44
```

---

## Zusammenfassung

```mermaid
flowchart TB
    subgraph problem["Das Problem"]
        P["800 Mio. Adressen<br/>Wer besitzt sie?"]
    end

    subgraph trick["Der Trick"]
        T["Multi-Input Transaktionen<br/>verraten Besitzverhaltnisse"]
    end

    subgraph solution["Die Losung"]
        S["Graph-Algorithmus<br/>Connected Components"]
    end

    subgraph result["Das Ergebnis"]
        R["Entities statt Adressen<br/>Wale werden sichtbar"]
    end

    P -->|"Beobachtung"| T
    T -->|"Anwendung"| S
    S -->|"Erkenntnis"| R

    style problem fill:#ff8787,stroke:#c92a2a
    style trick fill:#fff3bf,stroke:#fab005
    style solution fill:#74c0fc,stroke:#1c7ed6
    style result fill:#8ce99a,stroke:#2f9e44
```
