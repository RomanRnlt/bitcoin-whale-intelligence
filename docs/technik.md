# Bitcoin Whale Intelligence - Technik

## Inhaltsverzeichnis

1. [Warum dieser Tech Stack](#1-warum-dieser-tech-stack)
2. [Architektur: Vom TSV zum Wal](#2-architektur-vom-tsv-zum-wal)
3. [Datenmodell: Was speichern wir WARUM](#3-datenmodell-was-speichern-wir-warum)
4. [Algorithmen im Detail](#4-algorithmen-im-detail)
5. [Performance und Skalierung](#5-performance-und-skalierung)

---

## 1. Warum dieser Tech Stack

Jede Technologie erfuellt einen spezifischen Zweck fuer das Hauptziel (Wale finden):

| Technologie | Zweck | WARUM noetig? |
|-------------|-------|---------------|
| **Apache Spark** | Verteilte Verarbeitung | 900M+ Transaktionen passen nicht in RAM |
| **GraphFrames** | Connected Components | Milliarden Kanten effizient traversieren |
| **Parquet** | Spalten-Storage | 70-90% Kompression, schnelle Aggregationen |
| **Jupyter** | Interaktive Analyse | Explorative Wal-Suche mit sofortigem Feedback |

### Was NICHT funktionieren wuerde

- **Pandas**: Max ~10M Zeilen, Bitcoin hat 900M+ Transaktionen
- **NetworkX**: Single-Node, Graph passt nicht in RAM
- **CSV**: Keine Kompression, kein Column Pruning
- **SQL-Datenbank**: Zu langsam fuer Graph-Traversierung

---

## 2. Architektur: Vom TSV zum Wal

```
blockchair-downloader/          Rohdaten (TSV)
        |
        v
    [Spark ETL]                 Transformiert zu Parquet
        |
        +---> outputs.parquet   Alle Outputs mit Adressen
        +---> inputs.parquet    Alle Inputs mit Spent-Referenzen
        +---> utxos.parquet     Nur unspent = aktuelle Balances
        |
        v
    [GraphFrames]               Graph aus Multi-Input-Transaktionen
        |
        v
    entities.parquet            Adresse -> Entity-ID Mapping
        |
        v
    [Balance Join]              UTXO + Entity = Entity-Balance
        |
        v
    whale_entities.parquet      Entities mit >= 1000 BTC
```

### Warum diese Reihenfolge?

1. **TSV -> Parquet**: WEIL Parquet 10x schneller fuer Spark
2. **Outputs vor Inputs**: WEIL Inputs referenzieren Outputs
3. **UTXO vor Clustering**: WEIL Clustering unabhaengig laeuft
4. **Entity vor Balance**: WEIL Balance = SUM(UTXO) per Entity

---

## 3. Datenmodell: Was speichern wir WARUM

### outputs.parquet

**Zweck**: Alle jemals erstellten Bitcoin-Outputs

| Spalte | Typ | WARUM noetig? |
|--------|-----|---------------|
| `tx_hash` | string | Identifiziert die Transaktion |
| `output_index` | int | Position im Output-Array (0, 1, 2...) |
| `value` | long | Satoshi-Betrag fuer Balance-Berechnung |
| `addresses` | array | Empfaenger-Adressen fuer Clustering |
| `block_height` | int | Zeitliche Einordnung |

### inputs.parquet

**Zweck**: Alle Spending-Events (welcher Output wurde ausgegeben)

| Spalte | Typ | WARUM noetig? |
|--------|-----|---------------|
| `tx_hash` | string | Die ausgebende Transaktion |
| `spent_tx_hash` | string | Referenz zum urspruenglichen Output |
| `spent_output_index` | int | Welcher Output wurde spent |

**Zusammen ermoeglichen sie**: UTXO = Outputs MINUS Inputs

### entities.parquet

**Zweck**: Mapping von Adresse zu Entity-ID

| Spalte | Typ | WARUM noetig? |
|--------|-----|---------------|
| `address` | string | Die Bitcoin-Adresse (Primary Key) |
| `entity_id` | long | Vom Connected-Components-Algorithmus |

**Beispiel**:
```
address         | entity_id
----------------|----------
1ABC...         | 42
1DEF...         | 42        <- Gleiche Entity wie 1ABC
1GHI...         | 42        <- Gleiche Entity wie 1ABC
1XYZ...         | 99        <- Andere Entity
```

---

## 4. Algorithmen im Detail

### Common Input Ownership Heuristic

**Eingabe**: Transaktionen mit Multi-Input

**Logik**:
```python
# Fuer jede Transaktion mit >1 Input:
for tx in transactions.filter(input_count > 1):
    addresses = tx.inputs.map(i => i.address)
    # Alle Paare gehoeren zusammen:
    for (a1, a2) in combinations(addresses, 2):
        edges.add(a1, a2)
```

**Filter gegen False Positives**:
```python
# CoinJoin hat typisch >50 Inputs
.filter(input_count <= 50)
```

### Connected Components (GraphFrames)

**WARUM nicht selbst implementieren?**
- Spark GraphFrames nutzt optimierten Pregel-Algorithmus
- Automatisches Checkpointing gegen Lineage-Explosion
- Skaliert auf Milliarden Kanten

**Ablauf**:
1. Jede Adresse = Knoten mit eigener ID
2. Iterativ: Sende kleinste bekannte ID an Nachbarn
3. Konvergenz: Alle verbundenen Knoten haben gleiche ID

```
Iteration 1:  A(A)---B(B)---C(C)     D(D)---E(E)
Iteration 2:  A(A)---B(A)---C(B)     D(D)---E(D)
Iteration 3:  A(A)---B(A)---C(A)     D(D)---E(D)
Final:        Entity 1 = {A,B,C}    Entity 2 = {D,E}
```

---

## 5. Performance und Skalierung

### Benchmark-Werte

| Datenmenge | Transaktionen | Adressen | Clustering-Zeit |
|------------|---------------|----------|-----------------|
| Test (H1/2011) | 382k | 150k | ~2 Min |
| 1 Jahr (2015) | ~50M | ~20M | ~30 Min |
| Volle Blockchain | 900M+ | 800M+ | ~8h (Cluster) |

### Spark-Konfiguration

```python
spark.driver.memory = "8g"           # Fuer lokale Entwicklung
spark.sql.adaptive.enabled = True    # Dynamische Optimierung
spark.sql.shuffle.partitions = 200   # Parallelitaet
```

### Warum Checkpointing kritisch ist

Ohne Checkpointing:
```
connected_components() baut Lineage auf:
  Iteration 1 -> Iteration 2 -> ... -> Iteration 50
  = 50 verschachtelte Transformationen
  = StackOverflow bei Spark
```

Mit Checkpointing alle 5 Iterationen:
```
Iteration 1-5 -> [CHECKPOINT] -> Iteration 6-10 -> ...
Lineage wird unterbrochen, DAG bleibt klein
```

---

## Zusammenfassung: Technik dient dem Ziel

```
ZIEL: Wale finden (Entities mit >1000 BTC)
        |
        +-- Spark:       WEIL Daten zu gross fuer RAM
        +-- GraphFrames: WEIL Connected Components schnell sein muss
        +-- Parquet:     WEIL Aggregationen (SUM) schnell sein muessen
        +-- UTXO-Modell: WEIL nur unspent Outputs zaehlen
        +-- Checkpoints: WEIL Spark sonst abstuerzt
```
