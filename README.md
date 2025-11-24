# Bitcoin Whale Intelligence

Master-Projekt zur Identifikation von Bitcoin-Whales durch Entity Resolution auf der Blockchain.

**Modul:** Advanced Data Engineering
**Studiengang:** Wirtschaftsinformatik (Master)

## Inhaltsverzeichnis

- [Projektübersicht](#projektübersicht)
- [Notebook Workflow](#notebook-workflow)
  - [01 - Data Exploration](#01---data-exploration-abgeschlossen)
  - [02 - Entity Clustering](#02---entity-clustering-in-planung)
  - [03 - Whale Detection](#03---whale-detection-geplant)
  - [04 - Whale Analysis](#04---whale-analysis-geplant)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Dokumentation](#dokumentation)

---

## Projektübersicht

**Problem:** 800M Bitcoin-Adressen verschleiern wahre Besitzverhältnisse
**Lösung:** Graph-basiertes Clustering mit Common Input Ownership Heuristic
**Ziel:** Identifikation der größten Bitcoin-Holder (Whales mit >1000 BTC)

**Algorithmus:**
```
800M Adressen
  → Entity Clustering (GraphFrames Connected Components)
  → ~250-300M Entities
  → Balance-Berechnung (UTXO Aggregation)
  → Whale Detection & Behavioral Analysis
```

---

## Notebook Workflow

### 01 - Data Exploration [Abgeschlossen]

**Zweck:** Verständnis der Bitcoin-Datenstruktur und Validierung des UTXO-Modells

**Was wird gemacht:**
- Exploration der BigQuery-Tabellen (blocks, transactions, inputs, outputs)
- Analyse des UTXO-Modells (Unspent Transaction Outputs)
- Identifikation von Multi-Input Transactions als Basis für Clustering
- Statistische Analyse der Input-Verteilung

**Warum wichtig:**
- Bitcoin nutzt UTXO-System statt Account-Balances → muss verstanden werden
- Multi-Input Transactions sind der Schlüssel: ~40% aller Transactions
- Wenn Transaction mehrere Inputs nutzt → alle Adressen gehören zur selben Entity
- Validierung der Datenqualität vor weiterer Verarbeitung

**Output:** Keine Dateien, reine Exploration und Dokumentation

---

### 02 - Entity Clustering [In Planung]

**Zweck:** Reduktion von 800M Adressen auf ~250-300M Entities durch Graph-Clustering

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
- Common Input Ownership Heuristic: Mehrere Inputs = gleicher Owner

**Technische Herausforderungen:**
- Graph mit 2+ Milliarden Edges
- GraphFrames Stack Overflow → Checkpoint-Strategie nötig
- Exchanges haben >50 Inputs → müssen gefiltert werden (sonst false positives)

**Output:** `data/entities.parquet` mit [address, entity_id] Mapping

---

### 03 - Whale Detection [Geplant]

**Zweck:** Berechnung der Entity-Balances und Identifikation der größten Holder

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

**Output:**
- `data/entity_balances.parquet` - Alle Entity-Balances
- `data/whale_entities.parquet` - Top Whales mit Klassifikation

---

### 04 - Whale Analysis [Geplant]

**Zweck:** Zeitreihen-Analyse der Whale-Aktivitäten und Korrelation mit Marktbewegungen

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

**Output:**
- `data/whale_timeseries.parquet` - Zeitreihen pro Entity
- Visualisierungen: Correlation Plots, Flow Diagrams, Timeline Charts

---

## Roter Faden

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

---

## Tech Stack

- **Daten:** Google BigQuery Public Dataset (`bigquery-public-data.crypto_bitcoin`)
- **Processing:** Apache Spark (PySpark 3.4.1)
- **Graph-Analyse:** GraphFrames 0.6
- **Environment:** Jupyter Notebooks
- **Python:** 3.11+

---

## Quick Start

Siehe [SETUP.md](docs/SETUP.md) für vollständige Installationsanleitung.

```bash
source venv/bin/activate
export JAVA_HOME=$(/usr/libexec/java_home -v 11)  # macOS
jupyter notebook
```

---

## Dokumentation

- **[PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)** - Vollständiger Projekt-Kontext mit technischen Details
- **[SETUP.md](docs/SETUP.md)** - Setup-Anleitung (inkl. BigQuery)
- **[NOTEBOOK_WORKFLOW.md](docs/NOTEBOOK_WORKFLOW.md)** - Detaillierter Implementierungsplan
- **[requirements.txt](requirements.txt)** - Python Dependencies

---

Master-Projekt | Advanced Data Engineering | Wirtschaftsinformatik
