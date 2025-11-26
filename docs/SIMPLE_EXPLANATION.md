# Bitcoin Address Clustering - Einfache Erklärung

## Grundkonzepte

### 1. Bitcoin-Adresse = Briefkasten

Eine Bitcoin-Adresse ist wie ein Briefkasten, **in dem** Bitcoin liegt.

```
Beispiel einer Bitcoin-Adresse:
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

⚠️ WICHTIG: Dies ist eine einzelne Bitcoin-Adresse, KEINE "Wallet-Adresse"!
   Eine Person kann hunderte oder tausende solcher Adressen besitzen.
```

### 2. UTXO = Einzelne Münze

**UTXO (Unspent Transaction Output)** = Eine einzelne "Bitcoin-Münze"

```
Analogie: Geldbörse mit Geldscheinen

Deine Geldbörse (= Bitcoin-Adresse):
  • 1x 50€ Schein  (UTXO 1)
  • 1x 20€ Schein  (UTXO 2)
  • 1x 10€ Schein  (UTXO 3)
  ────────────────
  Total: 80€

→ EINE Adresse kann MEHRERE UTXOs enthalten
```

### 3. Wallet = Schlüsselbund für viele Adressen

Ein Wallet verwaltet viele Adressen:

```
Alice's Wallet:
  🔑 Adresse A1
  🔑 Adresse A2
  🔑 Adresse A3
  ...

1 Wallet = unbegrenzt viele Adressen
```

**Wann entstehen neue Adressen?**

Wallets **können** (sollten) neue Adressen erstellen:

1. **Beim Empfangen:** Moderne Wallets erstellen automatisch neue Adressen (Best Practice für Privacy)
   - ⚠️ In der Praxis: Börsen geben oft feste Adressen, Nutzer verwenden Adressen mehrfach
2. **Beim Senden:** Wechselgeld geht an automatisch erstellte neue Adresse
3. **Manuell:** Alice kann jederzeit neue Adressen erstellen

**Realität:** Nicht alle befolgen Best Practices - viele Adressen werden mehrfach verwendet!

**Warum hat Alice 3 Adressen?**

```
Timeline:
10. Dez: Wallet installiert → A1 erstellt, Bitcoin gekauft
15. Dez: Erneut Bitcoin kaufen → A2 erstellt (Privacy!)
         Mehrere Eingänge → A2 hat 3 UTXOs!
20. Dez: Bitcoin senden → A3 automatisch für Wechselgeld erstellt

→ Alice hat 1 Wallet, aber 3 Adressen mit insgesamt 5 UTXOs
```

---

## Das Problem

```
800 Millionen Bitcoin-Adressen existieren
        ↓
Wer besitzt sie?
        ↓
Alice könnte 1,000 Adressen haben
Börse X könnte 5,000,000 Adressen haben
        ↓
In der Blockchain steht NICHT, welche Adressen zusammengehören!
```

**Ziel:** Identifikation der echten Besitzer (Entities) durch Analyse der Blockchain-Daten.

---

## BigQuery Dataset Schema

```
bigquery-public-data.crypto_bitcoin

  blocks         → Metadaten (Zeitstempel)
    ↓
  transactions   → Überweisungen (input_count, output_count)
    ↓         ↘
  inputs       outputs
  (WER ZAHLT) (WER EMPFÄNGT)
```

### Wichtigste Tabelle: inputs

```
┌──────────────────┬───────┬──────────┬──────────┐
│ transaction_hash │ index │ address  │  value   │
├──────────────────┼───────┼──────────┼──────────┤
│  abc123...       │   0   │  A1      │ 50000000 │  ⎫ Zusammen
│  abc123...       │   1   │  A2      │ 30000000 │  ⎭ in tx abc123
└──────────────────┴───────┴──────────┴──────────┘
```

**Kernlogik:** Alle Adressen mit gleichem `transaction_hash` gehören zur selben Entity.

---

## Common Input Ownership Heuristic

### Das Grundprinzip

**Wenn eine Transaction mehrere Adressen als Inputs verwendet, gehören alle zur selben Entity.**

**Warum?** Um eine Bitcoin-Transaction zu signieren, braucht man die Private Keys ALLER Input-Adressen. Nur eine Person kann alle Keys haben.

### Warum passiert Multi-Input? (UTXO-Modell)

```
Problem: UTXOs müssen vollständig ausgegeben werden

Alice hat:
  A1: 0.5 BTC
  A2: 0.3 BTC

Alice will 0.7 BTC senden
  → A1 reicht nicht (nur 0.5)
  → MUSS A1 und A2 kombinieren!

Transaction:
  Inputs:  A1 (0.5) + A2 (0.3) = 0.8 BTC
  Outputs: 0.7 BTC an Empfänger
           0.09 BTC Wechselgeld
           0.01 BTC Fee

→ A1 und A2 werden ZUSAMMEN benutzt
→ Beide gehören zur gleichen Entity!
```

**Häufigkeit:** ~40% aller Bitcoin-Transaktionen sind Multi-Input.

---

## Entity Clustering: Schritt für Schritt

### Alice macht 2 Transaktionen

**Ausgangssituation:**
```
Alice's Wallet:
  A1: 1 UTXO (0.5 BTC)
  A2: 3 UTXOs (0.3, 0.25, 0.15 BTC)
  A3: 1 UTXO (0.2 BTC)
```

**Transaction 1 (1. Januar):**
```
Inputs:  A1 (0.5 BTC) + A2 (0.3 BTC)
         ↓
Erkenntnis: A1 und A2 gehören zusammen
```

**Transaction 2 (5. Januar):**
```
Inputs:  A2 (0.25 BTC) + A3 (0.2 BTC)
         ↓
Erkenntnis: A2 und A3 gehören zusammen
```

### Transitive Verbindung

**Der Knackpunkt:** A1 und A3 waren NIE zusammen in einer Transaction!

```
Beweis durch logische Schlussfolgerung:

Fakt 1: A1 und A2 gehören zusammen (aus tx_1)
Fakt 2: A2 und A3 gehören zusammen (aus tx_2)

A2 kann nur EINER Person gehören!
→ A1, A2 und A3 gehören ALLE zur gleichen Person (Alice)

Das ist die Transitive Eigenschaft:
Wenn A1 = A2 und A2 = A3, dann A1 = A3
```

### Graph-Darstellung

```
Einzelne Verbindungen:
  tx_1: A1 ←→ A2
  tx_2: A2 ←→ A3

Zusammengeführt:
  A1 ──── A2 ──── A3

  └─── Entity 1 ───┘
       (Alice)

A2 ist die "Brücke" die A1 und A3 verbindet!
```

### Connected Components Algorithmus

GraphFrames findet alle zusammenhängenden Gruppen:

```
Input:  Graph mit Adressen als Vertices, Co-Inputs als Edges
Output: entity_id pro Adresse

┌──────────┬────────────┐
│ address  │ entity_id  │
├──────────┼────────────┤
│  A1      │     1      │
│  A2      │     1      │
│  A3      │     1      │
└──────────┴────────────┘

→ Alle drei bekommen gleiche entity_id
→ data/entities.parquet
```

---

## Warum das funktioniert: 4 Gründe

**1. Technische Notwendigkeit (UTXO-Modell)**
- Bitcoin zwingt Nutzer, UTXOs zu kombinieren wenn einer nicht reicht
- Keine Wahl außer Multi-Input zu verwenden

**2. Kryptographische Signatur**
- Jeder Input braucht Private Key Signatur
- Nur wer alle Keys hat, kann die Transaction erstellen

**3. Häufigkeit**
- 40% aller Transaktionen sind Multi-Input
- Millionen Transaktionen pro Tag
- Genug Daten für Entity Resolution

**4. Transitive Verbindungen**
- Graph-Algorithmus findet direkte UND indirekte Verbindungen
- Über Zeit entstehen Ketten über 100+ Adressen

**→ Das ist keine Vermutung, sondern eine logische Konsequenz des Bitcoin-Protokolls.**

---

## Vollständiger Prozess

```
1. BigQuery inputs
   → Multi-Input-Transaktionen (input_count >= 2)

2. Graph-Konstruktion
   → Adressen die zusammen vorkommen = Edges

3. Connected Components
   → Findet alle zusammenhängenden Gruppen

4. Entity Mapping
   → data/entities.parquet (address → entity_id)

5. Balance-Berechnung
   → Summe aller UTXOs pro Entity

6. Whale Detection
   → Entities mit >= 1000 BTC
```

---

## Balance-Berechnung und Whale Detection

### Wie berechnet man den Kontostand einer Entity?

Erinnerung: Bitcoin hat **keine Kontostände**. Stattdessen gibt es UTXOs ("Münzen").

**Der Kontostand einer Entity = Summe aller ihrer unverbrauchten UTXOs**

### Schritt-für-Schritt Beispiel

**Ausgangssituation:**
```
Entity 1 (aus Clustering):
  Adressen: A1, A2, A3

Alle UTXOs in der Blockchain:
  A1: 0.5 BTC (unverbraucht)
  A1: 0.3 BTC (unverbraucht)
  A2: 1.2 BTC (unverbraucht)
  A3: 0.8 BTC (bereits ausgegeben - NICHT zählen!)
  A3: 2.5 BTC (unverbraucht)
```

**Balance-Berechnung:**
```
Entity 1 Balance = 0.5 + 0.3 + 1.2 + 2.5 = 4.5 BTC
                   └─A1─┘   A2    A3

A3 (0.8 BTC) wird NICHT gezählt, da bereits ausgegeben.
```

**Technisch:**
```sql
SELECT entity_id, SUM(utxo_value) as balance
FROM entities
  JOIN outputs ON entities.address = outputs.address
WHERE outputs.is_spent = FALSE
GROUP BY entity_id
```

### Was ist ein Whale?

**Definition:** Entity mit mindestens 1000 BTC

**Warum interessant?**
- 1000 BTC = ~50-100 Millionen USD (je nach Kurs)
- Whales können den Markt bewegen
- Große Verkäufe → Preissturz möglich
- Große Käufe → Preisanstieg möglich

### Vermögensverteilung in Bitcoin

Bitcoin hat eine **extreme Ungleichverteilung**:

```
Top 10,000 Entities (0.004% aller Entities)
  → kontrollieren ~80% aller Bitcoin

Gini-Coefficient: ~0.95-0.98
  (1.0 = maximale Ungleichheit, 0.0 = perfekte Gleichheit)

Zum Vergleich:
  - USA Vermögen: 0.85
  - Deutschland: 0.78
  - Bitcoin: 0.95+ (noch ungleicher!)
```

### Whale-Kategorien

Nach dem Clustering können Whales klassifiziert werden:

1. **Exchange (Börse):**
   - Sehr viele Adressen (>10,000)
   - Hohe Transaktionsfrequenz
   - Beispiel: Binance, Coinbase

2. **Mining Pool:**
   - Regelmäßige Coinbase-Transactions
   - Viele kleine Auszahlungen

3. **Institutional Fund:**
   - Große Beträge
   - Wenige Bewegungen
   - Beispiel: MicroStrategy, Grayscale

4. **Individual Whale:**
   - Mittlere Adressanzahl (100-1000)
   - Unregelmäßige Aktivität
   - "Hodler" oder frühe Bitcoin-Adopter

### Praktisches Beispiel

```
Nach Entity Clustering haben wir:
  Entity 42: 250 Adressen

Balance-Berechnung:
  Alle UTXOs der 250 Adressen summiert = 15,432 BTC

Klassifikation:
  ✓ >= 1000 BTC → WHALE

Kategorie-Analyse:
  - Viele Adressen (250)
  - Wenige Transaktionen pro Jahr
  - Keine Coinbase-Transactions
  → Wahrscheinlich: Individual Whale (Hodler)
```

---

## Whale-Verhalten über Zeit analysieren

Nachdem wir die Whales identifiziert haben, können wir ihr Verhalten beobachten:

### Was macht ein Whale?

**Zwei Hauptaktivitäten:**

1. **Accumulation (Akkumulieren/Sammeln):**
   - Whale kauft Bitcoin
   - Balance steigt über Zeit
   - Signal: Bullish (Glaube an Preisanstieg)

2. **Distribution (Verkaufen/Verteilen):**
   - Whale verkauft Bitcoin
   - Balance fällt über Zeit
   - Signal: Bearish (Erwartung von Preisfall oder Profit-Taking)

### Praktisches Beispiel

```
Entity 42 (Individual Whale):

Januar 2023:  15,432 BTC
Februar 2023: 15,890 BTC (+458)  → Accumulation
März 2023:    16,234 BTC (+344)  → Accumulation
April 2023:   14,123 BTC (-2111) → Distribution!

Interpretation:
  Jan-März: Whale kauft/sammelt
  April:    Whale verkauft großen Teil
            → Möglicher Grund: Gewinnmitnahme
```

### Exchange-Flow Analyse

**Wichtige Beobachtung:** Wohin bewegt der Whale seine Bitcoin?

**Zu Exchange:**
```
Whale sendet 1000 BTC → Binance
  → Wahrscheinlich: Will verkaufen
  → Signal: Bearish
```

**Von Exchange:**
```
Whale empfängt 500 BTC von Coinbase
  → Wahrscheinlich: Hat gekauft
  → Signal: Bullish
```

**Zu eigener Cold Wallet:**
```
Whale bewegt 5000 BTC zu neuer Adresse (keine Exchange)
  → Wahrscheinlich: Langfristige Aufbewahrung
  → Signal: Hodl (sehr bullish)
```

### Dormant Whales (Schlafende Whales)

**Definition:** Whale der >1 Jahr keine Transaktionen gemacht hat

**Warum interessant?**

```
Dormant Whale mit 10,000 BTC bewegt sich nach 3 Jahren:
  → "Whale Awakening"
  → Oft großer Markt-Impact
  → Medien berichten darüber
  → Kann Panik oder FOMO auslösen
```

**Beispiel aus der Praxis:**
- Satoshi's Wallets (~1 Million BTC) sind seit 2010 dormant
- Wenn sich auch nur 1% bewegen würde → massiver Markt-Schock

### Korrelation mit Bitcoin-Preis

**Forschungsfrage:** Bewegen Whales den Markt oder folgen sie dem Markt?

**Zwei Szenarien:**

**Szenario A: Whales führen (Lead)**
```
Tag 1: Whale akkumuliert 1000 BTC
Tag 2: Bitcoin-Preis steigt +5%
Tag 3: Preis steigt weiter +3%

→ Whale-Aktivität VOR Preisbewegung
→ "Smart Money" - Whale weiß etwas?
```

**Szenario B: Whales folgen (Lag)**
```
Tag 1: Bitcoin-Preis steigt +8%
Tag 2: Whale akkumuliert 500 BTC
Tag 3: Weitere Whales kaufen auch

→ Whale reagiert AUF Preisbewegung
→ FOMO auch bei großen Playern
```

**Lead/Lag-Analyse:**
```
Berechnung:
  Korrelation(Whale-Käufe[t], Preis[t+1])

Wenn positiv:
  → Whale-Käufe heute → Preis steigt morgen
  → Whales haben Vorhersagekraft

Wenn neutral:
  → Keine Beziehung
  → Whales sind nicht "smarter" als Markt
```

### Praktische Anwendung

**Was ein Trader daraus lernen kann:**

```
Beobachtung:
  10 große Individual Whales senden gleichzeitig
  insgesamt 15,000 BTC zu Exchanges

Interpretation:
  → Koordinierte Verkaufsbereitschaft
  → Möglicher Preisdruck
  → Vorsicht geboten

Aktion:
  → Abwarten oder Stop-Loss setzen
  → Auf Preisfall vorbereitet sein
```

**Wichtiger Hinweis:** Dies ist KEINE Anlageberatung, sondern Datenanalyse!

### Visualisierungen

Im Notebook 04 werden erstellt:

1. **Zeitreihen-Plots:**
   - Whale-Balance über Zeit
   - Preiskorrelation

2. **Flow-Diagramme:**
   - Bitcoin-Flüsse zwischen Whales und Exchanges
   - Sankey-Diagramme

3. **Heatmaps:**
   - Whale-Aktivität nach Wochentag/Monat
   - Muster erkennen

4. **Correlation Matrices:**
   - Whale-Bewegungen vs. Preis
   - Lead/Lag-Beziehungen

---

## Statistiken

Basierend auf Analyse vom 1. Januar 2023:

```
Tägliche Transaktionen:        ~300,000
Davon Multi-Input (>= 2):      ~120,000 (40%)

Erwartete Reduktion:
  Adressen vorher:  ~800,000,000
  Entities nachher: ~250,000,000 - 300,000,000
  Reduktion:        62-70%
```

---

## Einschränkungen

Die Heuristic hat bekannte Ausnahmen:

1. **Exchanges:** Bündeln Auszahlungen mehrerer Nutzer (>50 Inputs)
   - Filterung: Transaktionen mit `input_count > 50` werden separat behandelt
2. **CoinJoin:** Privacy-Protokolle kombinieren absichtlich Transaktionen verschiedener Nutzer
3. **Mining-Pools:** Pool-Auszahlungen an verschiedene Miner
4. **Adress-Wiederverwendung:** Manche Adressen werden oft wiederverwendet (Börsen, Spenden)
   - Kann zu überschätzten Entity-Größen führen
5. **Temporale Dimension:** Adressen die früher zusammengehörten, könnten verkauft worden sein
   - Clustering zeigt historische Zusammengehörigkeit, nicht aktuelle Besitzverhältnisse

**Genauigkeit:** Die Methode liefert ~85-95% korrekte Zuordnungen (laut Forschung)

---

## Zusammenfassung

```
800M Adressen
    → Entity Clustering (GraphFrames Connected Components)
    → ~250M Entities
    → Balance-Berechnung
    → Whale Detection (>1000 BTC)
```

**Ergebnis:** Identifikation der größten Bitcoin-Holder durch Entschleierung der echten Besitzverhältnisse.
