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
- [Roter Faden](#roter-faden)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Dokumentation](#dokumentation)

**Neu im Projekt?** Starte mit [SIMPLE_EXPLANATION.md](docs/SIMPLE_EXPLANATION.md) für eine verständliche Einführung.

---

## Projektübersicht

### Das Problem

**800 Millionen Bitcoin-Adressen existieren - aber wer besitzt sie wirklich?**

- **Bitcoin-Adresse:** Einzelner "Briefkasten" in dem Bitcoin liegt (z.B. `bc1q...`)
- **Wallet:** Software/Hardware die tausende solcher Adressen verwaltet
- **Entity:** Die tatsächliche Person/Firma dahinter

Das Problem: In der Blockchain ist **nicht sichtbar**, welche Adressen zur selben Person gehören.

**Beispiel:** Ein Whale mit 5000 BTC könnte diese über 1000 verschiedene Adressen verteilt haben. Ohne Analyse sieht man 1000 kleine Holder statt 1 großen Whale.

*Mehr Details: [SIMPLE_EXPLANATION.md - Grundkonzepte](docs/SIMPLE_EXPLANATION.md#grundkonzepte)*

### Die Lösung

**Kernidee:** Wenn eine Bitcoin-Transaction mehrere Adressen kombiniert, gehören alle zur selben Person.

**Warum?** Bitcoin funktioniert mit "Münzen" (UTXOs) statt Kontoständen:
- Jede "Münze" muss vollständig ausgegeben werden
- Wenn eine nicht reicht → mehrere kombinieren
- Um mehrere zu kombinieren → braucht man alle Private Keys
- **Nur eine Person kann alle Keys besitzen**

**Beispiel:**
```
Person X sendet 0.7 BTC, hat aber nur:
  Adresse A: 0.5 BTC
  Adresse B: 0.3 BTC

Muss beide kombinieren:
  Transaction Inputs: A (0.5) + B (0.3) = 0.8 BTC

→ Beweis: A und B gehören zur gleichen Person!
```

Der Graph-Algorithmus findet alle solche Verbindungen und gruppiert Adressen zu Entities.

*Mehr Details: [SIMPLE_EXPLANATION.md - Common Input Ownership](docs/SIMPLE_EXPLANATION.md#common-input-ownership-heuristic)*

### Das Ziel

Identifikation der größten Bitcoin-Holder (Whales mit >1000 BTC) durch Entschleierung der wahren Besitzverhältnisse.

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

Die folgende Übersicht zeigt die 4 Hauptnotebooks und deren Zweck. Für technische Details siehe [NOTEBOOK_WORKFLOW.md](docs/NOTEBOOK_WORKFLOW.md).

### 01 - Data Exploration [Abgeschlossen]

**Notebook:** [01_data_exploration.ipynb](notebooks/01_data_exploration.ipynb)

**Zweck:** Verständnis der Bitcoin-Datenstruktur und Validierung des UTXO-Modells

**Was wird gemacht:**
- Exploration der BigQuery-Tabellen (blocks, transactions, inputs, outputs)
- Analyse des UTXO-Modells (Unspent Transaction Outputs)
- Identifikation von Multi-Input Transactions als Basis für Clustering
- Statistische Analyse der Input-Verteilung

**Warum wichtig:**

Bitcoin nutzt **keine Kontostände wie ein Bankkonto**, sondern ein UTXO-System:
- UTXO = "Münze" die man vollständig ausgeben muss (wie ein 50€-Schein)
- Kein Teilbetrag möglich → wenn zu wenig, mehrere kombinieren
- **Multi-Input Transaction:** Mehrere "Münzen" von verschiedenen Adressen kombiniert
  - ~40% aller Bitcoin-Transactions sind Multi-Input
  - Dies ist der Schlüssel zum Entity-Clustering

**Kryptographischer Beweis:**
- Jede Adresse hat einen Private Key (wie ein Passwort)
- Um eine Transaction zu signieren: Private Keys ALLER Input-Adressen nötig
- Nur der Besitzer hat alle Keys → alle Adressen gehören ihm

Diese Analyse validiert:
- Datenqualität (Inputs = Outputs + Fee stimmt immer)
- Multi-Input-Ratio (~40% nutzbar für Clustering)
- Verteilungsmuster (typisch 1-2 Inputs, selten >10)

*Mehr Details: [SIMPLE_EXPLANATION.md - UTXO-Modell](docs/SIMPLE_EXPLANATION.md#2-utxo--einzelne-münze)*

**Output:** Keine Dateien, reine Exploration und Dokumentation

---

### 02 - Entity Clustering [In Planung]

**Notebook:** [02_entity_clustering.ipynb](notebooks/02_entity_clustering.ipynb) *(noch zu erstellen)*

**Zweck:** Reduktion von 800M Adressen auf ~250-300M Entities durch Graph-Clustering

**Was wird gemacht:**
1. Extraktion aller Multi-Input Transactions (input_count >= 2)
2. Konstruktion eines Address-Graphen:
   - Vertices: Bitcoin-Adressen
   - Edges: Adressen die zusammen als Input verwendet wurden
3. Connected Components Algorithmus (GraphFrames)
4. Mapping: Address → Entity-ID

**Warum wichtig:**

Ohne Clustering sieht man nur 800M einzelne Adressen:
- Unmöglich zu erkennen wer die großen Player sind
- Ein Whale mit 5000 BTC über 1000 Adressen verteilt = unsichtbar
- Statt dessen: 1000 kleine Adressen mit je ~5 BTC

**Mit Clustering:**
- 800M Adressen → ~250M Entities (62% Reduktion)
- Graph-Algorithmus findet verbundene Adressen
- **Transitive Verbindungen:** Wenn A+B zusammen UND B+C zusammen → dann A+B+C = gleiche Entity
- Enthüllt die wahren Besitzverhältnisse

**Praktisches Beispiel:**
```
Beobachtung über Zeit:
  Transaction 1: Adressen A + B kombiniert
  Transaction 2: Adressen B + C kombiniert

Graph-Clustering:
  A ←→ B ←→ C
  └─────────┘
   Entity 1

→ Obwohl A und C nie zusammen verwendet wurden,
  gehören alle drei zur selben Entity (über B verbunden)
```

**Technische Herausforderungen:**
- Graph mit 2+ Milliarden Edges
- GraphFrames Stack Overflow → Checkpoint-Strategie nötig
- Exchanges haben >50 Inputs → müssen gefiltert werden (sonst false positives)

**Methodische Einschränkungen:**
- **Exchanges:** Bündeln Auszahlungen mehrerer Nutzer → Filter bei >50 Inputs nötig
- **CoinJoin:** Privacy-Protokolle kombinieren Transaktionen → können Clustering erschweren
- **Adress-Wiederverwendung:** Börsen verwenden oft feste Adressen → kann zu Überclusterung führen
- **Temporale Dimension:** Clustering zeigt historische Zusammengehörigkeit (Adressen könnten verkauft worden sein)
- **Genauigkeit:** ~85-95% korrekte Zuordnungen (laut Forschungsliteratur)
- *Ausführliche Diskussion: [SIMPLE_EXPLANATION.md - Einschränkungen](docs/SIMPLE_EXPLANATION.md#einschränkungen)*

**Output:** `data/entities.parquet` mit [address, entity_id] Mapping

---

### 03 - Whale Detection [Geplant]

**Notebook:** [03_whale_detection.ipynb](notebooks/03_whale_detection.ipynb) *(noch zu erstellen)*

**Zweck:** Berechnung der Entity-Balances und Identifikation der größten Holder

**Was wird gemacht:**
1. UTXO-Aggregation: Alle unverbrauchten UTXOs pro Entity summieren
2. Balance-Berechnung: Kontostand = Summe aller unverbrauchten "Münzen"
3. Whale-Filter: Entities mit >= 1000 BTC (~50-100 Mio USD)
4. Wealth Distribution Analyse (Gini-Coefficient, Lorenz Curve)
5. Entity-Klassifikation: Exchange, Mining Pool, Fund, Individual Whale

**Warum wichtig:**

**Balance-Berechnung verständlich:**
```
Entity 42 hat (aus Clustering):
  250 Adressen (A1, A2, ..., A250)

Alle unverbrauchten UTXOs dieser Adressen:
  A1: 0.5 BTC + 0.3 BTC
  A2: 1.2 BTC
  A5: 2.5 BTC
  ...
  ────────────────────
  Total: 15,432 BTC

→ Entity 42 Balance = 15,432 BTC
→ >= 1000 BTC → WHALE
```

**Vermögensverteilung:**
- Bitcoin hat extreme Ungleichverteilung (Gini: 0.95-0.98)
- Top 10,000 Entities (~0.004%) kontrollieren ~80% aller Bitcoin
- Zum Vergleich: USA Vermögen hat Gini 0.85, Deutschland 0.78

**Whale-Klassifikation wichtig:**
- **Exchange:** >10,000 Adressen, hohe Frequenz (Binance, Coinbase)
- **Mining Pool:** Regelmäßige Coinbase-Transactions
- **Institutional Fund:** Große Beträge, wenig Bewegung (MicroStrategy)
- **Individual Whale:** 100-1000 Adressen, "Hodler"

Nur Individual Whales sind echte "Markt-Mover" - Exchanges halten Geld von Millionen Nutzern.

*Mehr Details: [SIMPLE_EXPLANATION.md - Balance & Whale Detection](docs/SIMPLE_EXPLANATION.md#balance-berechnung-und-whale-detection)*

**Output:**
- `data/entity_balances.parquet` - Alle Entity-Balances
- `data/whale_entities.parquet` - Top Whales mit Klassifikation

---

### 04 - Whale Analysis [Geplant]

**Notebook:** [04_whale_analysis.ipynb](notebooks/04_whale_analysis.ipynb) *(noch zu erstellen)*

**Zweck:** Zeitreihen-Analyse der Whale-Aktivitäten und Korrelation mit Marktbewegungen

**Was wird gemacht:**
1. Whale Transaction History über Zeit aggregieren
2. Accumulation vs. Distribution Phasen erkennen
3. Exchange-Flow Analyse (wohin fließt das Geld?)
4. Dormant Whale Detection (>1 Jahr inaktiv)
5. Lead/Lag-Analyse: Bewegen Whales den Markt oder folgen sie ihm?

**Warum wichtig:**

**Verhaltensmuster erkennen:**
```
Entity 42 (Individual Whale) über Zeit:

Januar 2023:  15,432 BTC
Februar 2023: 15,890 BTC (+458)  → Accumulation
März 2023:    16,234 BTC (+344)  → Accumulation
April 2023:   14,123 BTC (-2111) → Distribution!

Interpretation:
  Jan-März: Whale kauft (bullish Signal)
  April:    Whale verkauft großen Teil
            → Mögliche Gewinnmitnahme oder negative Erwartung
```

**Exchange-Flow als Signal:**
- **Zu Exchange:** Whale sendet 1000 BTC → Binance = wahrscheinlich Verkauf (bearish)
- **Von Exchange:** Whale empfängt 500 BTC von Coinbase = wahrscheinlich Kauf (bullish)
- **Zu Cold Wallet:** 5000 BTC zu neuer Adresse = Langzeit-Hodl (sehr bullish)

**Dormant Whale Awakening:**
```
Whale mit 10,000 BTC dormant seit 3 Jahren
  → Bewegt sich plötzlich
  → "Whale Awakening" Event
  → Oft großer Markt-Impact
  → Medien berichten → FOMO/Panik

Beispiel: Satoshi's ~1 Million BTC seit 2010 dormant
  → Wenn auch nur 1% sich bewegen → massiver Schock
```

**Forschungsfrage: Lead oder Lag?**
```
Szenario A (Lead):
  Tag 1: Whale kauft 1000 BTC
  Tag 2: Preis steigt +5%
  → Whale VOR Preisbewegung = "Smart Money"

Szenario B (Lag):
  Tag 1: Preis steigt +8%
  Tag 2: Whale kauft 500 BTC
  → Whale NACH Preisbewegung = FOMO auch bei Whales
```

**Praktischer Nutzen:**
- Frühindikatoren für Marktbewegungen
- Whale-Koordination erkennen (10 Whales senden gleichzeitig zu Exchanges)
- "Smart Money" Movements nachvollziehen

**Wichtig:** Dies ist Datenanalyse, keine Anlageberatung!

*Mehr Details: [SIMPLE_EXPLANATION.md - Whale-Verhalten](docs/SIMPLE_EXPLANATION.md#whale-verhalten-über-zeit-analysieren)*

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

- **[SIMPLE_EXPLANATION.md](docs/SIMPLE_EXPLANATION.md)** - **START HIER!** Einfache Erklärung für Einsteiger (Wallet vs. Adresse, UTXO, Entity Clustering)
- **[PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)** - Vollständiger Projekt-Kontext mit technischen Details
- **[SETUP.md](docs/SETUP.md)** - Setup-Anleitung (inkl. BigQuery)
- **[NOTEBOOK_WORKFLOW.md](docs/NOTEBOOK_WORKFLOW.md)** - Detaillierter Implementierungsplan
- **[requirements.txt](requirements.txt)** - Python Dependencies

---

Master-Projekt | Advanced Data Engineering | Wirtschaftsinformatik
