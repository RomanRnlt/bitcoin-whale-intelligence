# Bitcoin Whale Intelligence - Einfache Erklaerung

> **Ziel**: Versteckte Bitcoin-Besitzer ("Wale") sichtbar machen, die ihr Vermoegen auf viele Adressen verteilen.

## Inhaltsverzeichnis

- [Das Problem](#das-problem-wer-besitzt-wirklich-die-bitcoin)
- [Die Loesung: Common Input Ownership](#die-loesung-common-input-ownership-heuristic)
- [Entity Clustering](#entity-clustering-der-graph-algorithmus)
- [Die komplette Pipeline](#die-komplette-pipeline)
- [Projekt-Roadmap](#projekt-roadmap)

---

## Das Problem: Wer besitzt wirklich die Bitcoin?

Die Blockchain zeigt nur Adressen - keine Besitzer. Ein Wal kann sein Vermoegen auf hunderte Adressen verteilen.

```mermaid
flowchart LR
    subgraph blockchain["Was die Blockchain zeigt"]
        A1[Adresse 1<br/>5 BTC]
        A2[Adresse 2<br/>3 BTC]
        A3[Adresse 3<br/>7 BTC]
        A4[Adresse 4<br/>2 BTC]
        A5[Adresse 5<br/>8 BTC]
    end

    subgraph reality["Realitaet - unsichtbar!"]
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

---

## Die Loesung: Common Input Ownership Heuristic

**Kernidee**: Wer kann mehrere Adressen in EINER Transaktion als Input nutzen? Nur der Besitzer aller Private Keys!

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

Adressen werden zu Knoten, gemeinsame Inputs zu Kanten. Connected Components findet alle zusammengehoerenden Adressen.

```mermaid
flowchart TB
    subgraph step1["1. Transaktionen analysieren"]
        TX1["TX1: Inputs von A + B"]
        TX2["TX2: Inputs von B + C"]
        TX3["TX3: Inputs von D + E"]
    end

    subgraph step2["2. Graph aufbauen"]
        A((A)) --- B((B))
        B --- C((C))
        D((D)) --- E((E))
    end

    subgraph step3["3. Connected Components"]
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

**Ergebnis**: ~150.000 Adressen werden zu ~110.000 Entities (25% Reduktion).

---

## Die komplette Pipeline

```mermaid
flowchart TB
    subgraph input["1. Datenquelle"]
        JSON[("Blockchair TSV")]
    end

    subgraph transform["2. Transformation"]
        SPARK["Apache Spark"]
        OUT[("outputs.parquet")]
        INP[("inputs.parquet")]
        UTXO[("utxos.parquet")]
    end

    subgraph cluster["3. Entity Clustering"]
        GRAPH["Graph aufbauen"]
        CC["Connected Components"]
        ENT[("entities.parquet")]
    end

    subgraph analysis["4. Whale Detection"]
        BAL["Entity Balances"]
        WHALE["Wale identifizieren"]
    end

    subgraph behavior["5. Verhaltensanalyse"]
        ACC["Akkumulation/Distribution"]
    end

    JSON --> SPARK --> OUT & INP --> UTXO
    OUT --> GRAPH --> CC --> ENT
    UTXO & ENT --> BAL --> WHALE --> ACC

    style input fill:#e7f5ff,stroke:#1c7ed6
    style transform fill:#fff3bf,stroke:#fab005
    style cluster fill:#d3f9d8,stroke:#2f9e44
    style analysis fill:#ffe3e3,stroke:#fa5252
    style behavior fill:#e599f7,stroke:#9c36b5
```

---

## Projekt-Roadmap

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| **Entity Clustering** | Fertig | Adressen zu Entities gruppieren |
| **Whale Detection** | Geplant | Balance pro Entity, Top-Wale finden |
| **Verhaltensanalyse** | Geplant | Akkumulation vs. Distribution erkennen |

### Was wir ueber Wale lernen koennen

```mermaid
flowchart LR
    subgraph whale["Identifizierter Wal"]
        W[/"Entity #12345<br/>5.000 Adressen<br/>10.000 BTC"/]
    end

    subgraph analysis["Analysen"]
        A1["Akkumulation?"]
        A2["Distribution?"]
        A3["Dormant?"]
    end

    subgraph insight["Erkenntnisse"]
        I1["Markt-Sentiment"]
        I2["Preis-Impact"]
    end

    W --> A1 & A2 & A3 --> I1 & I2

    style W fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style insight fill:#d3f9d8,stroke:#2f9e44
```

---

## Zusammenfassung

```mermaid
flowchart LR
    P["800 Mio. Adressen"] -->|"Multi-Input Heuristik"| T["Graph-Analyse"]
    T -->|"Connected Components"| R["Entities + Wale sichtbar"]

    style P fill:#ff8787,stroke:#c92a2a
    style T fill:#74c0fc,stroke:#1c7ed6
    style R fill:#8ce99a,stroke:#2f9e44
```
