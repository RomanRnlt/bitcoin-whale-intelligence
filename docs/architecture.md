# Bitcoin Whale Intelligence - Architektur

> Wie wir versteckte Bitcoin-Wale finden

---

## Das Problem

```mermaid
flowchart LR
    subgraph Blockchain["Was die Blockchain zeigt"]
        A1[Adresse 1<br/>500 BTC]
        A2[Adresse 2<br/>300 BTC]
        A3[Adresse 3<br/>200 BTC]
        A4[Adresse 4<br/>50 BTC]
    end

    subgraph Reality["Realitaet (unsichtbar)"]
        E1[Entity A<br/>1000 BTC<br/>= WAL!]
        E2[Entity B<br/>50 BTC]
    end

    A1 -.-> E1
    A2 -.-> E1
    A3 -.-> E1
    A4 -.-> E2

    style E1 fill:#ff6b6b,color:#fff
    style E2 fill:#4ecdc4
```

**Das Problem:** Ein Wal kann sein Vermoegen auf hunderte Adressen verteilen. Ohne Clustering bleibt er unsichtbar.

---

## Die Loesung: Common Input Ownership

Wenn eine Transaktion mehrere Input-Adressen kombiniert, besitzt der Sender ALLE Private Keys:

```mermaid
sequenceDiagram
    participant A1 as Adresse A<br/>(0.5 BTC)
    participant A2 as Adresse B<br/>(0.3 BTC)
    participant TX as Transaktion
    participant Bob as Bob<br/>(empfaengt)

    Note over A1,A2: Alice besitzt beide Adressen

    A1->>TX: Input 1: 0.5 BTC
    A2->>TX: Input 2: 0.3 BTC
    TX->>Bob: Output: 0.7 BTC
    TX->>A1: Wechselgeld: 0.09 BTC

    Note over TX: Fee: 0.01 BTC

    rect rgb(255, 230, 230)
        Note over A1,A2: ERKENNTNIS: A und B<br/>gehoeren zusammen!
    end
```

**Warum das funktioniert:** Ohne alle Private Keys keine gueltige Signatur. Das Bitcoin-Protokoll erzwingt das.

---

## Entity Clustering als Graph

Multi-Input-Transaktionen bilden Kanten zwischen Adressen:

```mermaid
graph TB
    subgraph tx1["TX-100: Multi-Input"]
        A((A)) --- B((B))
    end

    subgraph tx2["TX-200: Multi-Input"]
        B2((B)) --- C((C))
    end

    subgraph tx3["TX-300: Multi-Input"]
        D((D)) --- E((E))
    end

    subgraph result["Connected Components Ergebnis"]
        subgraph entity1["Entity 1"]
            A1((A))
            B1((B))
            C1((C))
        end
        subgraph entity2["Entity 2"]
            D1((D))
            E1((E))
        end
    end

    A --> A1
    B --> B1
    B2 --> B1
    C --> C1
    D --> D1
    E --> E1

    style entity1 fill:#e8f5e9
    style entity2 fill:#fff3e0
```

**Transitive Verknuepfung:** A-B und B-C bedeutet A-B-C gehoeren zusammen.

---

## Die Pipeline

```mermaid
flowchart TB
    subgraph input["1. Daten laden"]
        RAW[("bitcoin-etl<br/>JSON Export")]
    end

    subgraph transform["2. Transformation"]
        RAW --> OUT[outputs.parquet]
        RAW --> INP[inputs.parquet]
    end

    subgraph utxo["3. UTXO berechnen"]
        OUT --> UTXO[utxos.parquet]
        INP --> UTXO
    end

    subgraph cluster["4. Entity Clustering"]
        INP --> GRAPH["Graph aufbauen<br/>(Multi-Input = Kanten)"]
        GRAPH --> CC["Connected<br/>Components"]
        CC --> ENT[entities.parquet]
    end

    subgraph whale["5. Whale Detection"]
        UTXO --> BAL["Balance<br/>pro Entity"]
        ENT --> BAL
        BAL --> WHALE[("Wale<br/>>= 1000 BTC")]
    end

    style RAW fill:#e3f2fd
    style WHALE fill:#ff6b6b,color:#fff
```

| Schritt | Output | Warum noetig? |
|---------|--------|---------------|
| 1. Laden | tx_df | Brauchen alle Transaktionen |
| 2. Transform | outputs/inputs.parquet | Parquet 10x schneller als JSON |
| 3. UTXO | utxos.parquet | Nur unspent = aktueller Wert |
| 4. Clustering | entities.parquet | Adressen zu Entities gruppieren |
| 5. Detection | whale_entities.parquet | Endlich Wale sichtbar! |

---

## Tech Stack

```mermaid
graph LR
    subgraph why["Warum diese Technologie?"]
        SPARK["Apache Spark"] --> |"900M+ TXs"| BIG["Zu gross fuer RAM"]
        GF["GraphFrames"] --> |"Milliarden Kanten"| GRAPH["Effizientes Clustering"]
        PARQUET["Parquet"] --> |"70-90% kleiner"| FAST["Schnelle Aggregation"]
    end
```

| Technologie | Zweck | Alternative (funktioniert NICHT) |
|-------------|-------|----------------------------------|
| Apache Spark | Verteilte Verarbeitung | Pandas (max 10M Zeilen) |
| GraphFrames | Connected Components | NetworkX (Single-Node) |
| Parquet | Spalten-Storage | CSV (keine Kompression) |

---

## Datenmodell

### entities.parquet
```
address         | entity_id
----------------|----------
1ABC...         | 42
1DEF...         | 42        <- Gleiche Entity
1GHI...         | 42        <- Gleiche Entity
1XYZ...         | 99        <- Andere Entity
```

### Whale Detection (Schritt 5)
```sql
SELECT entity_id,
       COUNT(address) as address_count,
       SUM(utxo.value) / 100000000 as balance_btc
FROM entities
JOIN utxos ON entities.address = utxos.address
GROUP BY entity_id
HAVING balance_btc >= 1000
```

---

## Projekt-Status

| Notebook | Status | Beschreibung |
|----------|--------|--------------|
| 01_entity_clustering | Fertig | Daten laden, UTXO, Clustering |
| 02_whale_detection | Geplant | Balance pro Entity |
| 03_behavior_analysis | Geplant | Akkumulation vs Distribution |

---

## Metriken (Testdaten H1/2011)

| Metrik | Wert |
|--------|------|
| Transaktionen | 382.000 |
| Outputs | 769.000 |
| Adressen im Graph | 147.907 |
| Entities | 109.000 |
| Reduktion | 26% |

Die 26% Reduktion zeigt: Viele Adressen konnten gruppiert werden. Bei neueren Daten (2015+) steigt die Rate auf 40-60%.
