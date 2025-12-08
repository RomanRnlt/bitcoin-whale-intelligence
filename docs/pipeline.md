# Bitcoin Whale Intelligence - Pipeline

## Inhaltsverzeichnis

1. [Gesamtueberblick: Vom Rohdaten zum Wal](#1-gesamtueberblick-vom-rohdaten-zum-wal)
2. [Notebook 00: Daten laden](#2-notebook-00-daten-laden)
3. [Notebook 01: Entity Clustering](#3-notebook-01-entity-clustering)
4. [Notebook 02: Whale Detection](#4-notebook-02-whale-detection-geplant)
5. [Notebook 03: Verhaltensanalyse](#5-notebook-03-verhaltensanalyse-geplant)

---

## 1. Gesamtueberblick: Vom Rohdaten zum Wal

Jedes Notebook ist ein Schritt naeher zum Ziel: **Wale identifizieren**.

```
Notebook 00       Notebook 01         Notebook 02         Notebook 03
Daten laden  -->  Entity Clustering  -->  Whale Detection  -->  Verhaltensanalyse
    |                   |                      |                      |
    v                   v                      v                      v
"Haben wir         "Welche Adressen      "Welche Entities     "Kauft oder
 valide Daten?"     gehoeren zusammen?"   sind Wale?"          verkauft der Wal?"
```

| Notebook | Status | WARUM dieser Schritt noetig ist |
|----------|--------|--------------------------------|
| `00_test_blockchair_loading` | Fertig | Ohne valide Daten kein Clustering moeglich |
| `01_entity_clustering` | Fertig | Ohne Entities keine Wal-Erkennung moeglich |
| `02_whale_detection` | Geplant | Ohne Balance-Berechnung keine Wal-Klassifikation |
| `03_behavior_analysis` | Geplant | Ohne Zeitreihen kein Kauf-/Verkauf-Signal |

---

## 2. Notebook 00: Daten laden

**Ziel**: Verifizieren, dass die Blockchair-Daten korrekt geladen werden.

**WARUM noetig?**
- Ohne korrekte Daten produziert Clustering falsche Ergebnisse
- TSV-Format kann Parsing-Fehler enthalten
- Schema-Validierung verhindert spaetere Fehler

**Input**: `blockchair-downloader/*.tsv`

**Output**: Validierungsbericht (keine Parquet-Dateien)

**Pruefungen**:
```
1. Koennen wir TSV-Dateien finden?          --> Pfad korrekt?
2. Ist das Schema wie erwartet?             --> Spalten vorhanden?
3. Gibt es NULL-Werte in kritischen Feldern? --> Datenqualitaet?
4. Sind die Werte plausibel?                --> tx_hash Format, value > 0?
```

---

## 3. Notebook 01: Entity Clustering

**Ziel**: Adressen zu Entities gruppieren via Common Input Ownership.

**WARUM noetig?**
- Ohne Clustering sehen wir nur Adressen, nicht Besitzer
- Ein Wal mit 100 Adressen waere unsichtbar
- Clustering ist DIE Grundlage fuer Whale Detection

**Input**: `blockchair-downloader/*.tsv`

**Output**:
| Datei | WARUM erstellt? |
|-------|-----------------|
| `outputs.parquet` | Brauchen Adressen fuer Graph-Knoten |
| `inputs.parquet` | Brauchen Multi-Input fuer Graph-Kanten |
| `utxos.parquet` | Brauchen fuer spaetere Balance-Berechnung |
| `entities.parquet` | Das Clustering-Ergebnis: Adresse -> Entity |

**Ablauf mit WARUM**:

```
Schritt 1: Transaktionen laden
           WARUM: Brauchen alle TXs um Multi-Input-Muster zu finden

Schritt 2: Outputs/Inputs explodieren
           WARUM: Ein TX hat mehrere Adressen, brauchen einzelne Zeilen

Schritt 3: Graph aufbauen (Adressen = Knoten, Multi-Input = Kanten)
           WARUM: Common Input Ownership ist eine Beziehung

Schritt 4: Connected Components ausfuehren
           WARUM: Transitive Verbindungen finden (A-B, B-C => A-B-C)

Schritt 5: Entities speichern
           WARUM: Wiederverwendbar fuer Whale Detection
```

**Metriken (Testdaten H1/2011)**:
```
Transaktionen:  382.000
Outputs:        769.000
Adressen:       ~150.000
Entities:       ~110.000
Reduktion:      25% (40.000 Adressen gruppiert)
```

---

## 4. Notebook 02: Whale Detection (Geplant)

**Ziel**: Entities mit >= 1000 BTC als Wale klassifizieren.

**WARUM noetig?**
- Clustering allein sagt nicht WER ein Wal ist
- Brauchen Balance pro Entity, nicht pro Adresse
- Erst jetzt sehen wir die "versteckten" Wale

**Input**: `entities.parquet`, `utxos.parquet`

**Output**: `entity_balances.parquet`, `whale_entities.parquet`

**Ablauf mit WARUM**:

```
Schritt 1: UTXOs laden
           WARUM: Nur unspent Outputs haben aktuellen Wert

Schritt 2: Entities laden
           WARUM: Brauchen Adresse -> Entity Mapping

Schritt 3: Join UTXO.address = Entity.address
           WARUM: Jedes UTXO bekommt seine Entity-ID

Schritt 4: GROUP BY entity_id, SUM(value)
           WARUM: Aggregiert Balance ueber alle Adressen einer Entity

Schritt 5: FILTER balance >= 1000 BTC
           WARUM: Nur die grossen Entities sind Wale
```

**Erwartetes Ergebnis**:
```
entity_id | address_count | total_balance_btc | is_whale
----------|---------------|-------------------|----------
42        | 47            | 5.230             | true
99        | 2             | 0.5               | false
```

**Was NICHT funktionieren wuerde**:
- Balance per Adresse berechnen: Verteilt auf viele Adressen
- Ohne UTXO: Wuerde spent Outputs doppelt zaehlen

---

## 5. Notebook 03: Verhaltensanalyse (Geplant)

**Ziel**: Erkennen ob Wale akkumulieren (kaufen) oder distribuieren (verkaufen).

**WARUM noetig?**
- Ein Wal der verkauft = potenzieller Preiseinbruch
- Ein Wal der kauft = potenzieller Preisanstieg
- Fruehwarnsystem fuer Marktbewegungen

**Input**: `whale_entities.parquet`, Transaktionen mit Zeitstempel

**Output**: `behavior_metrics.parquet`

**Ablauf mit WARUM**:

```
Schritt 1: Balance-Historie pro Entity berechnen
           WARUM: Brauchen Zeitreihe, nicht nur aktuellen Stand

Schritt 2: Delta zwischen Zeitraeumen berechnen
           WARUM: Veraenderung zeigt Kauf/Verkauf-Tendenz

Schritt 3: Verhalten klassifizieren
           WARUM: Kategorien erleichtern Analyse

   Delta > +10%:  "Akkumulation"  (Wal kauft)
   Delta < -10%:  "Distribution"  (Wal verkauft)
   -10% <= Delta <= +10%: "Dormant" (Wal haelt)
```

**Erwartetes Ergebnis**:
```
entity_id | balance_30d_ago | balance_now | delta_pct | behavior
----------|-----------------|-------------|-----------|----------
42        | 4.800 BTC       | 5.230 BTC   | +9%       | dormant
77        | 2.000 BTC       | 3.500 BTC   | +75%      | accumulating
88        | 8.000 BTC       | 2.000 BTC   | -75%      | distributing
```

---

## Zusammenfassung: Pipeline dient dem Ziel

```
ZIEL: Versteckte Wale finden und ihr Verhalten analysieren

Notebook 00:  Daten laden
              WEIL: Ohne valide Daten nichts moeglich

Notebook 01:  Entity Clustering
              WEIL: Adresse =/= Besitzer, muessen gruppieren

Notebook 02:  Whale Detection
              WEIL: Erst mit Entity-Balance sehen wir Wale

Notebook 03:  Verhaltensanalyse
              WEIL: Statische Balance sagt nicht ob kaufen/verkaufen
```
