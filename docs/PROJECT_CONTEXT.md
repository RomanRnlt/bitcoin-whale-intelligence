# Bitcoin Whale Intelligence - Projekt Übersicht

**Master-Projekt:** Advanced Data Engineering (Wirtschaftsinformatik)
**Status:** Phase 1 abgeschlossen

## Projektziel

Identifikation von Bitcoin-Whales (Großinvestoren mit >1000 BTC) durch Graph-basiertes Entity Clustering der Blockchain-Daten.

**Problem:** 800M Bitcoin-Adressen verschleiern die wahren Besitzverhältnisse
**Lösung:** Common Input Ownership Heuristic + GraphFrames Connected Components
**Ergebnis:** 800M Adressen → ~250-300M Entities → Identifikation der größten Holder

## Tech Stack

- **Daten:** Google BigQuery Public Dataset (`bigquery-public-data.crypto_bitcoin`)
- **Processing:** Apache Spark (PySpark 3.4.1)
- **Graph-Analyse:** GraphFrames 0.6
- **Environment:** Jupyter Notebooks
- **Python:** 3.11+

## Kernalgorithmus: Common Input Ownership Heuristic

**Grundprinzip:**
Wenn eine Bitcoin-Transaction mehrere Input-Adressen verwendet (z.B. A, B, C), müssen alle diese Adressen zur selben Entity gehören.

**Warum?**
- Um eine Bitcoin-Transaction zu signieren, braucht man die Private Keys ALLER Input-Adressen
- Nur eine Person/Organisation kann alle diese Keys besitzen
- Dies ist keine Vermutung, sondern eine kryptographische Notwendigkeit

**Beispiel:**
```
Alice hat:
  Adresse A1: 0.5 BTC
  Adresse A2: 0.3 BTC

Alice will 0.7 BTC senden:
  → Muss A1 + A2 kombinieren (keine einzelne Adresse reicht)
  → Transaction verwendet A1 und A2 als Inputs
  → Beweis dass A1 und A2 zu Alice gehören
```

**Implementierung:**
1. Multi-Input Transactions aus BigQuery extrahieren
2. Address-Graph konstruieren (Edges = "verwendet in gleicher Transaction")
3. Connected Components Algorithmus (GraphFrames)
4. Jede Component = Eine Entity

**Einschränkungen:**
- Exchanges bündeln Auszahlungen → Filter bei >50 Inputs
- CoinJoin Privacy-Protokolle → Erkennung notwendig
- Adress-Wiederverwendung → kann zu Überclusterung führen
- Genauigkeit: ~85-95% (etabliert in der Forschung)

## Notebook-Workflow

### Notebook 01: Data Exploration [Abgeschlossen]

**Zweck:** Verständnis der Bitcoin-Datenstruktur und Validierung des UTXO-Modells.

**Was wird gemacht:**
- Exploration der BigQuery-Tabellen (blocks, transactions, inputs, outputs)
- Analyse des UTXO-Modells (Unspent Transaction Outputs)
- Identifikation von Multi-Input Transactions als Basis für Clustering
- Statistische Analyse der Input-Verteilung

**Warum wichtig:**
- Fundamentales Verständnis: Bitcoin nutzt UTXO-System statt Account-Balances
- Multi-Input Transactions sind der Schlüssel für Entity Resolution (~40% aller Transactions)
- Validierung der Datenqualität vor weiterer Verarbeitung
- Baseline-Statistiken für späteren Vergleich

**Key Findings:**
- 25-40% aller Transactions sind Multi-Input → verwendbar für Clustering
- Power-Law Verteilung bei Input Counts
- Balance-Invariante bestätigt (Input Value = Output Value + Fee)

**Output:** Keine Dateien, reine Exploration und Dokumentation

---

### Notebook 02: Entity Clustering [In Planung]

**Zweck:** Reduktion von 800M Adressen auf ~250-300M Entities durch Graph-Clustering.

**Was wird gemacht:**
1. Extraktion aller Multi-Input Transactions (input_count >= 2)
2. Konstruktion eines Address-Graphen:
   - Vertices: Bitcoin-Adressen
   - Edges: Adressen die zusammen als Input verwendet wurden
3. Connected Components Algorithmus (GraphFrames)
4. Mapping: Address → Entity-ID

**Warum wichtig:**
- Ohne Clustering sieht man nur Adressen, nicht die realen Besitzer
- Ein Whale mit 5000 BTC könnte über 1000 Adressen verteilt sein
- Graph-Algorithmus enthüllt diese Zusammenhänge
- Reduktion von 800M auf ~300M = 62% weniger Entitäten zu analysieren

**Technische Herausforderungen:**
- Graph mit 2+ Milliarden Edges
- GraphFrames Stack Overflow → Checkpoint-Strategie nötig
- Exchanges haben >50 Inputs → müssen gefiltert werden (sonst false positives)

**Output:** `data/entities.parquet` mit [address, entity_id] Mapping

---

### Notebook 03: Whale Detection [Geplant]

**Zweck:** Berechnung der Entity-Balances und Identifikation der größten Holder.

**Was wird gemacht:**
1. UTXO-Aggregation: Alle unspent outputs pro Entity summieren
2. Balance-Berechnung in BTC (1 BTC = 100M Satoshis)
3. Whale-Filter: Entities mit >= 1000 BTC
4. Wealth Distribution Analyse (Gini-Coefficient, Lorenz Curve)
5. Entity-Klassifikation (Exchange, Miner, Fund, Hodler)

**Warum wichtig:**
- Zeigt die wahre Vermögensverteilung in Bitcoin
- Top 10,000 Entities kontrollieren ~80% aller Bitcoin (erwartet)
- Gini-Coefficient ~0.95-0.98 zeigt extreme Ungleichheit
- Klassifikation ermöglicht Unterscheidung Exchange vs. echter Whale

**Technischer Ansatz:**
```sql
-- Konzeptionell
SELECT entity_id, SUM(utxo_value) as balance
FROM entities JOIN utxos ON address
GROUP BY entity_id
HAVING balance >= 1000 BTC
ORDER BY balance DESC
```

**Output:**
- `data/entity_balances.parquet` - Alle Entity-Balances
- `data/whale_entities.parquet` - Top Whales mit Klassifikation

---

### Notebook 04: Whale Analysis [Geplant]

**Zweck:** Zeitreihen-Analyse der Whale-Aktivitäten und Korrelation mit Marktbewegungen.

**Was wird gemacht:**
1. Whale Transaction History über Zeit aggregieren
2. Accumulation vs. Distribution Phasen erkennen:
   - Accumulation: Whale kauft/sammelt (Balance steigt)
   - Distribution: Whale verkauft (Balance fällt)
3. Exchange-Flow Analyse:
   - Transfers zu Exchange = potenzielle Verkäufe
   - Transfers von Exchange = potenzielle Käufe
4. Dormant Whale Detection (>1 Jahr inaktiv)
5. Korrelation mit Bitcoin-Preis

**Warum wichtig:**
- "Smart Money" Movements: Whales bewegen oft Markt
- Früherkennung: Whale-Movements können Preisbewegungen vorausgehen
- Exchange-Flows als Leading Indicator für Sell-/Buy-Pressure
- Dormant Whale Awakening = hohes Markt-Impact Event

**Analyse-Methoden:**
- Moving Averages für Trend-Detection
- Correlation Analysis (Whale-Activity vs. Price)
- Lead/Lag Analysis (Wer bewegt sich zuerst?)
- Volume Profile (Wann akkumulieren Whales?)

**Output:**
- `data/whale_timeseries.parquet` - Zeitreihen pro Entity
- Visualisierungen: Correlation Plots, Flow Diagrams, Timeline Charts

---

## Roter Faden: Warum diese Reihenfolge?

```
1. Data Exploration
   ↓ Verstehen wie Bitcoin-Daten strukturiert sind

2. Entity Clustering
   ↓ Adressen zu echten Entities zusammenfassen

3. Whale Detection
   ↓ Größte Entities identifizieren und klassifizieren

4. Whale Analysis
   ↓ Verhalten der Whales über Zeit analysieren
```

Jedes Notebook baut auf dem vorherigen auf:
- Ohne (1) weiß man nicht wie man die Daten interpretiert
- Ohne (2) sieht man nur Adressen, nicht die realen Akteure
- Ohne (3) weiß man nicht wer die wichtigen Player sind
- (4) gibt dann die finalen Insights über Whale-Verhalten

## Big Data Justifikation

**Warum Spark notwendig ist:**
- 800M+ Transaktionen, 2B+ Graph Edges
- RDBMS würde bei Connected Components Out-of-Memory laufen
- Iterative Graph-Algorithmen brauchen In-Memory Processing
- Distributed Computing für Skalierbarkeit

**Performance-Erwartung:**
- Notebook 1: Wenige Minuten (nur Queries)
- Notebook 2: Mehrere Stunden (Graph-Processing)
- Notebook 3: ~1 Stunde (Aggregationen)
- Notebook 4: ~1 Stunde (Zeitreihen)

## Setup-Informationen

**Projekt starten:**
```bash
source venv/bin/activate
jupyter notebook
```

**Wichtige Dateien:**
- [SETUP.md](SETUP.md) - Setup-Anleitung
- [NOTEBOOK_WORKFLOW.md](NOTEBOOK_WORKFLOW.md) - Detaillierter Plan aller Notebooks

**Git:**
```bash
git pull                    # Vor Änderungen
git add .
git commit -m "message"
git push                    # Nach Änderungen
```

## Für Review/Presentation

Das Projekt demonstriert:
1. **Big Data Engineering:** Spark für skalierbare Verarbeitung
2. **Graph-Algorithmen:** Connected Components auf Milliarden Edges
3. **Data Analysis:** Von Rohdaten zu Insights
4. **Reproduzierbarkeit:** Jupyter Notebooks mit Dokumentation
5. **Akademischer Standard:** Literatur-Referenzen, Validierung

Die Notebooks können schrittweise durchlaufen werden und zeigen den kompletten Workflow von Rohdaten bis zu finalen Erkenntnissen über Bitcoin Whale-Verhalten.
