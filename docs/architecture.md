# Bitcoin Whale Intelligence - Pipeline-Architektur

> Dokumentation fuer Professor-Pitch: Wie wir versteckte Bitcoin-Wale finden

---

## Inhaltsverzeichnis

1. [Das Problem: Versteckte Wale](#1-das-problem-versteckte-wale)
2. [Bitcoin-Grundkonzepte](#2-bitcoin-grundkonzepte)
3. [Datenquelle: bitcoin-etl](#3-datenquelle-bitcoin-etl)
4. [Pipeline-Uebersicht](#4-pipeline-uebersicht)
5. [Schritt 1: Outputs extrahieren](#5-schritt-1-outputs-extrahieren)
6. [Schritt 2: Inputs extrahieren](#6-schritt-2-inputs-extrahieren)
7. [Schritt 3: UTXO-Set berechnen](#7-schritt-3-utxo-set-berechnen)
8. [Schritt 4a: Multi-Input Gruppierung](#8-schritt-4a-multi-input-gruppierung)
9. [Schritt 4b: Connected Components](#9-schritt-4b-connected-components)
10. [Schritt 5: Whale Detection](#10-schritt-5-whale-detection)
11. [Tech Stack und Begruendung](#11-tech-stack-und-begruendung)

---

## 1. Das Problem: Versteckte Wale

Ein Bitcoin-Wal kann sein Vermoegen auf viele Adressen verteilen. Auf der Blockchain sieht das aus wie viele kleine, unabhaengige Besitzer:

```mermaid
flowchart LR
    subgraph blockchain["Was die Blockchain zeigt"]
        A1["Adresse A<br/>500 BTC"]
        A2["Adresse B<br/>300 BTC"]
        A3["Adresse C<br/>200 BTC"]
        A4["Adresse D<br/>150 BTC"]
        A5["Adresse E<br/>100 BTC"]
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

| Ohne Analyse | Mit unserer Analyse |
|--------------|---------------------|
| 5 unabhaengige Adressen | 1 Entity (Person/Firma) |
| Groesster Besitz: 500 BTC | Tatsaechlicher Besitz: 1.250 BTC |
| Kein Wal erkennbar | **WAL identifiziert!** |

**Ziel:** Adressen zu Entities gruppieren und grosse Besitzer ("Whales") finden.

---

## 2. Bitcoin-Grundkonzepte

### 2.1 Das UTXO-Modell (Wie Bitcoin funktioniert)

Bitcoin funktioniert **NICHT** wie ein Bankkonto mit Kontostand. Stattdessen besitzt man "Muenzen" (UTXOs) verschiedener Groesse:

```mermaid
flowchart LR
    subgraph bank["Bankkonto (Account-Modell)"]
        K["Kontostand: 100 EUR<br/>─────────────────<br/>Ueberweisung: -30 EUR<br/>─────────────────<br/>Neuer Stand: 70 EUR"]
    end

    subgraph btc["Bitcoin (UTXO-Modell)"]
        U1["Muenze 1<br/>0.5 BTC"]
        U2["Muenze 2<br/>0.3 BTC"]
        TX["Transaktion"]
        O1["An Bob<br/>0.7 BTC"]
        O2["Wechselgeld<br/>0.09 BTC"]
        FEE["Gebuehr<br/>0.01 BTC"]

        U1 --> TX
        U2 --> TX
        TX --> O1
        TX --> O2
        TX -.-> FEE
    end

    style bank fill:#e3f2fd
    style btc fill:#c8e6c9
```

**Wichtig:** Muenzen (UTXOs) werden **vollstaendig** ausgegeben. Man bekommt Wechselgeld als neue Muenze zurueck.

| Begriff | Erklaerung |
|---------|-----------|
| **UTXO** | Unspent Transaction Output = Eine "Muenze" die noch nicht ausgegeben wurde |
| **Input** | Eine Muenze die in einer Transaktion ausgegeben wird |
| **Output** | Eine neue Muenze die durch eine Transaktion entsteht |

---

### 2.2 Adressen, Private Keys und Signaturen

```mermaid
flowchart TB
    subgraph keys["Schluesselpaar (pro Adresse)"]
        PK["Private Key<br/>─────────────────<br/>Geheimer Schluessel<br/>NUR Besitzer kennt ihn"]
        ADDR["Adresse<br/>─────────────────<br/>Oeffentlicher Briefkasten<br/>Jeder kann Bitcoin senden"]

        PK -->|"erzeugt"| ADDR
    end

    subgraph usage["Verwendung"]
        SEND["Bitcoin EMPFANGEN<br/>Adresse reicht"]
        SPEND["Bitcoin AUSGEBEN<br/>Private Key noetig!"]
    end

    ADDR --> SEND
    PK --> SPEND

    style PK fill:#ffcdd2
    style ADDR fill:#c8e6c9
```

**Das ist der Kern unserer Analyse:**

```mermaid
flowchart TB
    subgraph tx["Transaktion mit 2 Inputs"]
        I1["Input 1: 2 BTC<br/>von Adresse A<br/>─────────────<br/>Braucht Private Key A<br/>zum Signieren"]
        I2["Input 2: 3 BTC<br/>von Adresse B<br/>─────────────<br/>Braucht Private Key B<br/>zum Signieren"]
        O["Output: 4.99 BTC<br/>an Adresse C"]

        I1 --> O
        I2 --> O
    end

    subgraph conclusion["Schlussfolgerung"]
        C["Wer diese Transaktion erstellt,<br/>muss BEIDE Private Keys besitzen!<br/>─────────────────────────────<br/>Adresse A und B gehoeren<br/>zum SELBEN BESITZER"]
    end

    tx --> conclusion

    style conclusion fill:#fff9c4
```

**Das ist die "Common Input Ownership Heuristic"** - die Grundlage unseres Entity Clusterings.

---

### 2.3 Wichtig: Nur INPUTS werden gruppiert, nicht Outputs!

```mermaid
flowchart LR
    subgraph tx["Transaktion"]
        subgraph inputs["INPUTS = Absender"]
            IA["Adresse A"]
            IB["Adresse B"]
        end

        subgraph outputs["OUTPUTS = Empfaenger"]
            OC["Adresse C"]
            OD["Adresse D"]
        end

        IA --> TX2["TX"]
        IB --> TX2
        TX2 --> OC
        TX2 --> OD
    end

    subgraph result["Ergebnis"]
        R1["A + B = SELBER BESITZER<br/>(beide Keys zum Signieren noetig)"]
        R2["C + D = UNBEKANNT<br/>(koennen verschiedene Empfaenger sein)"]
    end

    inputs --> R1
    outputs --> R2

    style R1 fill:#c8e6c9
    style R2 fill:#ffcdd2
```

---

### 2.4 Warum eine Person viele Adressen hat

| Grund | Erklaerung |
|-------|-----------|
| **Wechselgeld** | Jede Transaktion erzeugt oft eine neue Adresse fuer Wechselgeld |
| **Privatsphaere** | Wallets generieren fuer jede Zahlung eine neue Empfangsadresse |
| **Organisation** | Boersen nutzen separate Adressen pro Kunde |

---

## 3. Datenquelle: bitcoin-etl

### 3.1 Woher kommen die Daten?

Wir nutzen [bitcoin-etl](https://github.com/blockchain-etl/bitcoin-etl), ein Tool das Blockchain-Daten von einem Bitcoin Full Node exportiert:

```mermaid
flowchart LR
    NODE["Bitcoin Full Node<br/>─────────────────<br/>Vollstaendige Blockchain"]
    ETL["bitcoin-etl<br/>─────────────────<br/>Export-Tool"]
    JSON["JSON-Dateien<br/>─────────────────<br/>Strukturierte Daten<br/>fuer Analyse"]

    NODE -->|"RPC API"| ETL
    ETL -->|"Export"| JSON

    style NODE fill:#ffcc80
    style ETL fill:#81d4fa
    style JSON fill:#c8e6c9
```

### 3.2 Verzeichnisstruktur der exportierten Daten

```
blockchain_exports/
└── YYYY-MM-DD_YYYY-MM-DD/          <- Zeitraum des Exports
    ├── blocks/
    │   └── date=YYYY-MM-DD/        <- Hive-Partitionierung nach Datum
    │       └── blocks_00000.json
    └── transactions/
        └── date=YYYY-MM-DD/
            └── transactions_00000.json   <- Das brauchen wir!
```

**Hive-Partitionierung:** Daten sind nach Datum in Ordner sortiert. Spark kann gezielt nur benoetigte Tage laden.

### 3.3 JSON-Struktur einer Transaktion

```json
{
  "hash": "f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16",
  "block_number": 170,
  "block_timestamp": 1231731025,
  "is_coinbase": false,

  "inputs": [
    {
      "index": 0,
      "spent_transaction_hash": "0437cd7f8525...",
      "spent_output_index": 0,
      "addresses": ["12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S"],
      "value": 5000000000
    }
  ],

  "outputs": [
    {
      "index": 0,
      "addresses": ["1Q2TWHE3GMdB6BZKafqwxXtWAWgFt5Jvm3"],
      "value": 1000000000,
      "type": "pubkeyhash"
    },
    {
      "index": 1,
      "addresses": ["12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S"],
      "value": 4000000000
    }
  ]
}
```

**Wichtige Felder:**

| Feld | Bedeutung |
|------|-----------|
| `hash` | Eindeutige ID der Transaktion |
| `inputs[].spent_transaction_hash` | Verweis auf vorherige TX (welche Muenze wird ausgegeben) |
| `inputs[].spent_output_index` | Welcher Output der vorherigen TX |
| `inputs[].addresses` | Wer signiert (= Absender) |
| `outputs[].addresses` | Wer empfaengt |
| `outputs[].value` | Betrag in Satoshi (1 BTC = 100.000.000 Satoshi) |

---

## 4. Pipeline-Uebersicht

```mermaid
flowchart TB
    subgraph source["1. Datenquelle"]
        RAW[("transactions/*.json<br/>Nested JSON Arrays")]
    end

    subgraph etl["2. ETL: Extract & Transform"]
        EO["Schritt 1: explode_outputs<br/>Nested zu Flach"]
        EI["Schritt 2: explode_inputs<br/>Nested zu Flach"]
    end

    subgraph storage["3. Zwischenspeicher"]
        OUT[("outputs.parquet")]
        INP[("inputs.parquet")]
    end

    subgraph processing["4. Verarbeitung"]
        UTXO["Schritt 3: UTXO berechnen<br/>LEFT ANTI JOIN"]
        MI["Schritt 4a: Multi-Input Gruppierung<br/>Kanten erstellen"]
        CC["Schritt 4b: Connected Components<br/>Transitive Verknuepfung"]
    end

    subgraph results["5. Ergebnisse"]
        UTXOP[("utxos.parquet")]
        ENT[("entities.parquet")]
    end

    subgraph final["6. Finale Analyse"]
        WHALE["Schritt 5: Whale Detection<br/>JOIN + SUM + Filter"]
        RESULT[("Gefundene Wale")]
    end

    RAW --> EO
    RAW --> EI
    EO --> OUT
    EI --> INP
    OUT --> UTXO
    INP --> UTXO
    INP --> MI
    MI --> CC
    UTXO --> UTXOP
    CC --> ENT
    UTXOP --> WHALE
    ENT --> WHALE
    WHALE --> RESULT

    style RAW fill:#e3f2fd
    style RESULT fill:#ff6b6b,color:#fff
```

---

## 5. Schritt 1: Outputs extrahieren

### Problem: Nested Arrays in JSON

Die Rohdaten haben **verschachtelte Arrays** - eine Transaktion enthaelt mehrere Outputs als Liste:

```mermaid
flowchart LR
    subgraph before["VORHER: 1 Zeile mit Array"]
        TX["tx_hash: abc123<br/>outputs: [idx:0 val:10BTC, idx:1 val:0.5BTC]"]
    end

    subgraph after["NACHHER: Mehrere flache Zeilen"]
        R1["tx_hash: abc123 | output_index: 0 | value: 10 BTC"]
        R2["tx_hash: abc123 | output_index: 1 | value: 0.5 BTC"]
    end

    before -->|"explode()"| after
```

### Warum diese Transformation?

| Problem mit Nested | Loesung mit Flach |
|-------------------|------------------|
| Kein GROUP BY moeglich | GROUP BY address funktioniert |
| Kein JOIN moeglich | JOIN ueber tx_hash + index |
| Schwer zu filtern | Einfache WHERE-Bedingungen |

---

## 6. Schritt 2: Inputs extrahieren

Gleiche Logik wie bei Outputs:

```mermaid
flowchart LR
    subgraph before["VORHER: Nested"]
        TX["inputs: [spent_tx: xyz, spent_idx: 0, ...]"]
    end

    subgraph after["NACHHER: Flach"]
        R1["tx_hash | spent_tx_hash | spent_output_index"]
        R2["abc123 | xyz789        | 0"]
    end

    before -->|"explode()"| after
```

**Wichtig:** Der Input enthaelt einen **Verweis auf einen vorherigen Output** (`spent_tx_hash` + `spent_output_index`). Das brauchen wir fuer die UTXO-Berechnung.

---

## 7. Schritt 3: UTXO-Set berechnen

### Was ist das UTXO-Set?

**Alle Outputs die NOCH NICHT ausgegeben wurden** = Alle "Muenzen" die noch existieren.

```mermaid
flowchart TB
    subgraph outputs["Alle Outputs"]
        O1["TX-100:0 -> 5 BTC"]
        O2["TX-100:1 -> 3 BTC"]
        O3["TX-200:0 -> 2 BTC"]
    end

    subgraph spent["Spent-Referenzen aus Inputs"]
        S1["TX-100:0 wurde ausgegeben"]
    end

    subgraph utxo["UTXO-Set (Ergebnis)"]
        U1["TX-100:1 -> 3 BTC"]
        U2["TX-200:0 -> 2 BTC"]
    end

    outputs -->|"LEFT ANTI JOIN<br/>(behalte was NICHT gematcht)"| utxo
    spent -->|"Match: TX-100:0"| O1

    style O1 fill:#ffcdd2
    style U1 fill:#c8e6c9
    style U2 fill:#c8e6c9
```

### Warum LEFT ANTI JOIN?

| JOIN-Typ | Ergebnis |
|----------|----------|
| INNER JOIN | Nur Matches -> Spent Outputs |
| LEFT JOIN | Alle + Matches -> Mit NULL-Markierung |
| **LEFT ANTI JOIN** | Nur was NICHT matcht -> **UTXOs!** |

---

## 8. Schritt 4a: Multi-Input Gruppierung

### Innerhalb jeder Transaktion: Kanten erstellen

Fuer jede Transaktion mit mehreren Inputs werden die Input-Adressen als **Kanten** verbunden:

```mermaid
flowchart TB
    subgraph tx1["TX-500: Inputs A, B"]
        A1["Adresse A"] --- B1["Adresse B"]
    end

    subgraph tx2["TX-600: Inputs B, C"]
        B2["Adresse B"] --- C2["Adresse C"]
    end

    subgraph tx3["TX-700: Inputs D, E"]
        D3["Adresse D"] --- E3["Adresse E"]
    end

    subgraph edges["Ergebnis: Kanten-Liste"]
        E1["A -- B"]
        E2["B -- C"]
        E3b["D -- E"]
    end

    tx1 --> E1
    tx2 --> E2
    tx3 --> E3b
```

**Warum nur Inputs?** Nur der Absender muss alle Private Keys besitzen. Outputs koennen an beliebige Empfaenger gehen.

---

## 9. Schritt 4b: Connected Components

### Ueber Transaktionen hinweg: Transitive Verknuepfung

Der Graph-Algorithmus findet alle **transitiv verbundenen** Adressen:

```mermaid
flowchart LR
    subgraph input["Input: Graph mit Kanten"]
        A((A)) --- B((B))
        B --- C((C))
        D((D)) --- E((E))
        F((F))
    end

    subgraph algo["Connected Components Algorithmus"]
        AL["Finde alle Knoten<br/>die direkt oder<br/>transitiv verbunden sind"]
    end

    subgraph output["Output: Entity-Zuordnung"]
        R1["Entity 1: A, B, C"]
        R2["Entity 2: D, E"]
        R3["Entity 3: F"]
    end

    input --> algo
    algo --> output

    style R1 fill:#c8e6c9
    style R2 fill:#bbdefb
    style R3 fill:#fff9c4
```

### Beispiel der transitiven Verknuepfung

```
TX-500: Inputs [A, B]     -> Kante: A -- B
TX-600: Inputs [B, C]     -> Kante: B -- C
────────────────────────────────────────────
Ergebnis: A -- B -- C     -> Entity 1: {A, B, C}

TX-700: Inputs [D, E]     -> Kante: D -- E
────────────────────────────────────────────
Ergebnis: D -- E          -> Entity 2: {D, E}
```

**A und C haben NIE zusammen eine Transaktion gemacht, aber ueber B sind sie transitiv verbunden!**

---

## 10. Schritt 5: Whale Detection

### Finale Berechnung

```mermaid
flowchart LR
    subgraph inputs["Inputs"]
        E[("entities.parquet<br/>Adresse -> Entity")]
        U[("utxos.parquet<br/>Adresse -> BTC")]
    end

    subgraph process["Verarbeitung"]
        J["JOIN<br/>auf Adresse"]
        G["GROUP BY Entity<br/>SUM(BTC)"]
        F["Filter<br/>grosse Entities"]
    end

    subgraph output["Output"]
        W[("Whale-Liste<br/>Entity | Total BTC")]
    end

    E --> J
    U --> J
    J --> G
    G --> F
    F --> W

    style W fill:#ff6b6b,color:#fff
```

### Beispielrechnung

```mermaid
flowchart TB
    subgraph utxos["UTXOs"]
        UA["A: 500 BTC"]
        UB["B: 300 BTC"]
        UC["C: 200 BTC"]
    end

    subgraph entities["Entities"]
        ENT["A, B, C -> Entity 1"]
    end

    subgraph result["Nach JOIN + GROUP BY"]
        R["Entity 1<br/>────────────<br/>3 Adressen<br/>1.000 BTC<br/>= WAL!"]
    end

    utxos --> ENT
    ENT --> result

    style R fill:#ff6b6b,color:#fff
```

---

## 11. Tech Stack und Begruendung

```mermaid
flowchart TB
    subgraph stack["Technologie-Stack"]
        SPARK["Apache Spark<br/>─────────────────<br/>Verteilte Verarbeitung"]
        GF["GraphFrames<br/>─────────────────<br/>Graph-Algorithmen"]
        PQ["Parquet<br/>─────────────────<br/>Spalten-Storage"]
        ETL["bitcoin-etl<br/>─────────────────<br/>Datenexport"]
    end

    subgraph why["Warum?"]
        W1["Millionen Transaktionen<br/>Einzelrechner zu langsam"]
        W2["Connected Components<br/>auf grossen Graphen"]
        W3["70-90% Kompression<br/>schnelles Spalten-Lesen"]
        W4["Standardisiertes Format<br/>von Bitcoin Full Node"]
    end

    SPARK --- W1
    GF --- W2
    PQ --- W3
    ETL --- W4
```

| Technologie | Zweck | Warum diese Wahl? |
|-------------|-------|-------------------|
| **Apache Spark** | Verteilte Datenverarbeitung | Skaliert auf Cluster, verarbeitet TB an Daten |
| **GraphFrames** | Graph-Algorithmen | Connected Components auf Millionen Knoten moeglich |
| **Parquet** | Datenspeicherung | 70-90% kleiner als JSON, spaltenbasiert = schnelle Abfragen |
| **bitcoin-etl** | Blockchain-Export | Open Source, gut dokumentiert, Industriestandard |

---

## Zusammenfassung

| Schritt | Was passiert | Ergebnis |
|---------|--------------|----------|
| 1. Outputs extrahieren | Nested -> Flach | outputs.parquet |
| 2. Inputs extrahieren | Nested -> Flach | inputs.parquet |
| 3. UTXO berechnen | LEFT ANTI JOIN | utxos.parquet |
| 4a. Multi-Input Gruppierung | Kanten pro TX | Graph-Kanten |
| 4b. Connected Components | Transitive Verknuepfung | entities.parquet |
| 5. Whale Detection | JOIN + SUM + Filter | Whale-Liste |
