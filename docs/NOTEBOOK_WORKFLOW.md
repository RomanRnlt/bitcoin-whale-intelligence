# Notebook Workflow und Implementierungsplan

**Projekt:** Bitcoin Whale Intelligence - Entity Resolution und Whale Detection
**Status:** Phase 1 abgeschlossen, Phase 2 in Planung

---

## Übersicht: Notebook-Struktur

Das Projekt ist in 4 Haupt-Notebooks strukturiert, die sequenziell aufeinander aufbauen. Jedes Notebook hat einen klaren Input/Output und kann unabhängig ausgeführt werden, sobald die Voraussetzungen erfüllt sind.

```
┌─────────────────────────────────────────────────────────────┐
│  01_data_exploration.ipynb                      [Abgeschlossen]  │
│  └─> Verstehen der Datenstruktur und UTXO-Modell           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  02_entity_clustering.ipynb                     [Geplant] │
│  └─> GraphFrames Connected Components                      │
│      Output: data/entities.parquet                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  03_whale_detection.ipynb                       [Geplant] │
│  └─> Balance-Berechnung und Top-Entity-Identifikation      │
│      Output: data/whale_entities.parquet                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  04_whale_analysis.ipynb                        [Geplant] │
│  └─> Zeitreihen-Analyse und Behavioral Patterns            │
│      Output: Visualisierungen und Statistiken              │
└─────────────────────────────────────────────────────────────┘
```

---

## Detaillierte Notebook-Spezifikationen

### 01_data_exploration.ipynb ✅

**Status:** Abgeschlossen und reviewed

**Zweck:** Initiale Exploration der Bitcoin-Blockchain-Daten zur Validierung der Datenqualität und des UTXO-Modells.

**Grundkonzepte die verstanden werden müssen:**
- **Bitcoin-Adresse vs. Wallet:** Eine Adresse ist wie ein Briefkasten, ein Wallet verwaltet tausende Adressen
- **UTXO-Modell:** Bitcoin sind "Münzen" die vollständig ausgegeben werden (nicht teilbar wie Kontostände)
- **Multi-Input:** Wenn mehrere "Münzen" kombiniert werden → alle Adressen gehören zur selben Person
- **Entity:** Eine Person/Firma die viele Adressen besitzt (z.B. Alice's Wallet mit 1000 Adressen = 1 Entity)

**Input:**
- BigQuery Public Dataset: `bigquery-public-data.crypto_bitcoin`
- Stichprobenzeitraum: 1.-7. Januar 2023

**Durchgeführte Analysen:**
1. Schema-Analyse der 4 Haupttabellen (blocks, transactions, inputs, outputs)
2. UTXO-Modell-Verständnis mit praktischen Beispielen
3. Quantifizierung der Multi-Input-Transaktionen (~40% aller Transactions)
4. Statistische Baseline (Transaktionsvolumen, Input-Verteilung)
5. Balance-Validierung (Inputs = Outputs + Fee)

**Output:**
- Keine persistierten Dateien (reine Exploration)
- Dokumentation der Datenstruktur und Patterns

**Runtime:** ~5-10 Minuten (mit Demo-Daten)

**Key Findings:**
- 25-40% aller Transaktionen sind Multi-Input (verwendbar für Clustering)
- Power-Law-Verteilung bei Input-Counts
- Datenqualität ist hoch (keine fehlenden Werte)
- BigQuery Dataset ist vollständig und konsistent

---

### 02_entity_clustering.ipynb In Planung

**Status:** Nächster Schritt - Zu implementieren

**Zweck:** Implementierung des Entity-Clustering-Algorithmus mit GraphFrames zur Reduktion von ~800M Adressen auf ~250-300M Entities.

**Input:**
- BigQuery: Multi-Input Transactions (input_count >= 2)
- Zeitraum: Initial 1 Monat, dann Skalierung auf 1 Jahr
- Geschätztes Datenvolumen: ~40M Multi-Input Transactions/Jahr

**Zu implementierende Schritte:**

1. **Data Extraction**
   ```python
   - Multi-Input Transactions aus BigQuery extrahieren
   - Filter: input_count >= 2 AND input_count <= 50
   - Speichern als Parquet für Zwischencaching
   ```

2. **Graph Construction**
   ```python
   - Vertices: Alle Adressen aus Multi-Input Transactions
   - Edges: Paare von Adressen, die zusammen als Inputs verwendet wurden
   - GraphFrame erstellen (vertices_df, edges_df)
   ```

3. **Connected Components**
   ```python
   - GraphFrames.connectedComponents() ausführen
   - Jede Komponente = Eine Entity
   - Checkpoint-Strategie für große Graphs
   ```

4. **Entity Mapping**
   ```python
   - Address → Entity-ID Mapping erstellen
   - Validierung gegen bekannte Entities (Exchanges)
   - Statistiken: Cluster-Größen, Reduktionsrate
   ```

**Output:**
- `data/entities.parquet`: DataFrame mit Spalten [address, entity_id]
- `data/entity_stats.csv`: Cluster-Statistiken
- Visualisierung: Cluster-Size-Distribution

**Geschätzte Runtime:**
- 1 Monat Daten: ~30-45 Minuten
- 1 Jahr Daten: ~2-4 Stunden
- Full Blockchain: ~12-24 Stunden (optional)

**Technische Herausforderungen:**
- GraphFrames Stack Overflow → Checkpoint-Strategie
- Memory Management → Partitionierung
- Exchange Detection → Filter für >50 Inputs

**Methodische Limitationen (Common Input Ownership Heuristic):**
- **Exchanges:** Bündeln Auszahlungen mehrerer Nutzer in einer Transaction
  - Lösung: Filter bei input_count > 50
- **CoinJoin:** Privacy-Protokoll das absichtlich Transaktionen kombiniert
  - Erkennung: Typische Muster (gleiche Output-Beträge)
- **Adress-Wiederverwendung:** Börsen nutzen oft feste Empfangsadressen
  - Effekt: Kann zu überschätzten Entity-Größen führen
- **Temporale Aspekte:** Adressen könnten verkauft/übertragen worden sein
  - Clustering zeigt historische, nicht unbedingt aktuelle Besitzverhältnisse
- **Erwartete Genauigkeit:** 85-95% (laut Meiklejohn et al. 2013, Reid & Harrigan 2011)

**Erfolgsmetriken:**
- Reduktion von Adressen auf Entities: 60-70%
- Cluster-Größen folgen erwarteter Verteilung
- Bekannte Exchanges werden korrekt geclustert

---

### 03_whale_detection.ipynb Geplant

**Status:** Geplant - Nach Notebook 2

**Zweck:** Berechnung der Entity-Balances aus UTXOs und Identifikation der größten Entities (Whales).

**Input:**
- `data/entities.parquet` (aus Notebook 2)
- BigQuery: Outputs-Tabelle (alle UTXOs)
- Definition: Whale = Entity mit >1000 BTC

**Zu implementierende Schritte:**

1. **UTXO Aggregation**
   ```python
   - Alle UTXOs aus BigQuery laden
   - Join mit entities.parquet (Address → Entity-ID)
   - Aggregation: SUM(utxo_value) GROUP BY entity_id
   ```

2. **Whale Identification**
   ```python
   - Filter: entity_balance >= 1000 BTC
   - Ranking: Top 100, Top 1000, Top 10000 Entities
   - Kategorisierung nach Balance-Größe
   ```

3. **Entity Classification**
   ```python
   - Heuristiken für Entity-Typen:
     * Exchange (sehr viele Adressen, hohe Aktivität)
     * Miner (Coinbase-Transactions)
     * Whale Investor (wenige große Adressen)
     * Fund/Institution (bekannte Adressen)
   ```

4. **Wealth Distribution Analysis**
   ```python
   - Gini-Coefficient Berechnung
   - Lorenz-Curve Visualisierung
   - Top X% kontrollieren Y% Analyse
   ```

**Output:**
- `data/entity_balances.parquet`: [entity_id, balance_btc, address_count]
- `data/whale_entities.parquet`: Top-Entities mit >1000 BTC
- `data/entity_classification.parquet`: [entity_id, entity_type, confidence]

**Visualisierungen:**
- Balance Distribution (Histogram, log-scale)
- Lorenz Curve (Wealth Inequality)
- Top 100 Whales (Bar Chart)

**Geschätzte Runtime:** ~30-60 Minuten

**Erfolgsmetriken:**
- Gini-Coefficient ~0.95-0.98 (validiert mit Literatur)
- Top 10,000 Entities kontrollieren ~80% aller Bitcoin
- Bekannte Whales (MicroStrategy, etc.) korrekt identifiziert

---

### 04_whale_analysis.ipynb Geplant

**Status:** Geplant - Nach Notebook 3

**Zweck:** Zeitreihen-Analyse der Whale-Aktivitäten und Identifikation von Behavioral Patterns.

**Input:**
- `data/whale_entities.parquet` (aus Notebook 3)
- BigQuery: Transactions über Zeitverlauf
- Optional: Bitcoin-Preis-Daten (CoinGecko API)

**Zu implementierende Schritte:**

1. **Transaction History**
   ```python
   - Alle Transactions pro Whale-Entity extrahieren
   - Time-Series Features: Daily/Weekly Activity
   - Kategorisierung: Inbound vs. Outbound
   ```

2. **Accumulation/Distribution Detection**
   ```python
   - Moving Balance über Zeit
   - Accumulation Phase: Steigende Balance
   - Distribution Phase: Fallende Balance
   - Volume Spikes Detection
   ```

3. **Exchange Flow Analysis**
   ```python
   - Identifikation von Exchange-Adressen
   - Whale → Exchange Transfers (potenzielle Verkäufe)
   - Exchange → Whale Transfers (potenzielle Käufe)
   ```

4. **Correlation Analysis**
   ```python
   - Bitcoin-Preis vs. Whale-Aktivität
   - Lead/Lag-Analyse: Wer bewegt sich zuerst?
   - Statistical Significance Testing (p-values)
   ```

5. **Dormant Whale Detection**
   ```python
   - Entities ohne Bewegung >1 Jahr
   - "Awakening" Events (alte Coins bewegen sich)
   - Impact auf Markt
   ```

**Output:**
- `data/whale_timeseries.parquet`: Zeitreihen pro Entity
- `data/whale_patterns.parquet`: Detected Patterns (accumulation/distribution)
- Visualisierungen: Multiple Time-Series Charts

**Visualisierungen:**
- Whale Balance über Zeit (Top 10)
- Exchange Flows (Sankey Diagram)
- Correlation Matrix (Whale-Activity vs. Price)
- Dormant Whales Timeline

**Geschätzte Runtime:** ~30-45 Minuten

**Erfolgsmetriken:**
- Correlation Coefficient >0.5 (Whale-Flows vs. Price)
- Identifikation von 10+ Accumulation/Distribution Cycles
- Detection von Dormant Whale Awakenings

---

## Datenfluss zwischen Notebooks

```
BigQuery (Raw Data)
    │
    ├─> 01_data_exploration.ipynb
    │   └─> [Keine Outputs, nur Exploration]
    │
    └─> 02_entity_clustering.ipynb
        └─> data/entities.parquet
            │
            └─> 03_whale_detection.ipynb
                └─> data/whale_entities.parquet
                    │
                    └─> 04_whale_analysis.ipynb
                        └─> Visualisierungen & Reports
```

---

## Zeitplan und Abhängigkeiten

| Notebook | Status | Abhängigkeiten | Geschätzte Zeit | Priorität |
|----------|--------|---------------|-----------------|-----------|
| 01 Data Exploration | Abgeschlossen | Keine | Erledigt | - |
| 02 Entity Clustering | [In Planung] | BigQuery, GraphFrames | 1 Woche | Hoch |
| 03 Whale Detection | Geplant Geplant | Notebook 2 Output | 3-4 Tage | Hoch |
| 04 Whale Analysis | Geplant Geplant | Notebook 3 Output | 3-4 Tage | Mittel |

**Gesamtzeit:** ~2.5-3 Wochen für alle Notebooks

---

## Technische Voraussetzungen pro Notebook

### Notebook 2: Entity Clustering
- **RAM:** 8-16 GB (local mode)
- **Disk:** ~10 GB für Zwischendaten
- **Libraries:** GraphFrames, PySpark
- **BigQuery Quota:** ~50-100 GB Scan

### Notebook 3: Whale Detection
- **RAM:** 4-8 GB
- **Disk:** ~5 GB
- **Libraries:** PySpark
- **BigQuery Quota:** ~20-50 GB Scan

### Notebook 4: Whale Analysis
- **RAM:** 4-8 GB
- **Disk:** ~2 GB
- **Libraries:** PySpark, Pandas, Matplotlib
- **BigQuery Quota:** ~30-50 GB Scan (optional)

---

## Nächste Schritte (Meeting mit Prof)

### Zu besprechende Punkte:

1. **Notebook 1 Review:**
   - Ist die Exploration ausreichend?
   - Sind die Erklärungen verständlich?
   - Fehlt etwas Wichtiges?

2. **Notebook 2 Plan:**
   - Ist die GraphFrames-Strategie sinnvoll?
   - Zeitrahmen realistisch?
   - Soll mit 1 Monat oder 1 Jahr Daten gestartet werden?

3. **Scope-Diskussion:**
   - Sind 4 Notebooks ausreichend?
   - Soll ML-Komponente (Notebook 5) hinzugefügt werden?
   - Zeitrahmen für Gesamtprojekt?

4. **Technische Fragen:**
   - Exchange-Detection-Strategie validieren
   - Checkpoint-Strategie für GraphFrames besprechen
   - Validierungs-Metriken definieren

---

## Optionale Erweiterungen

Falls Zeit vorhanden:

### 05_machine_learning.ipynb (Optional)
- **Zweck:** ML-basierte Entity-Klassifikation und Verhaltensvorhersage
- **Input:** Outputs von Notebook 3+4
- **Methoden:** RandomForest, XGBoost für Entity-Typ-Klassifikation
- **Runtime:** ~1-2 Stunden

### 06_validation.ipynb (Optional)
- **Zweck:** Validierung gegen bekannte Ground-Truth-Daten
- **Input:** Chainalysis-Labels, WalletExplorer-Daten
- **Metriken:** Precision, Recall für Entity-Clustering

---

## Literatur-Referenzen

- **Meiklejohn et al. (2013):** "A Fistful of Bitcoins" - Common Input Ownership Heuristic
- **Reid & Harrigan (2011):** "An Analysis of Anonymity in the Bitcoin System"
- **Spagnuolo et al. (2014):** "BitIodine: Extracting Intelligence from the Bitcoin Network"

---

**Letzte Aktualisierung:** November 2024
