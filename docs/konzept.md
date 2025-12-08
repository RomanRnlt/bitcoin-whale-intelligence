# Bitcoin Whale Intelligence - Konzept

## Inhaltsverzeichnis

1. [Das Ziel: Wale identifizieren](#1-das-ziel-wale-identifizieren)
2. [Das Problem: Adressen verstecken Besitzer](#2-das-problem-adressen-verstecken-besitzer)
3. [Die Loesung: Common Input Ownership](#3-die-loesung-common-input-ownership)
4. [Die Pipeline: Warum jeder Schritt noetig ist](#4-die-pipeline-warum-jeder-schritt-noetig-ist)
5. [Ergebnis: Was wir ueber Wale lernen](#5-ergebnis-was-wir-ueber-wale-lernen)

---

## 1. Das Ziel: Wale identifizieren

**Wale** sind Bitcoin-Besitzer mit grossen Mengen BTC (typisch: >1.000 BTC). Sie beeinflussen den Markt - wenn ein Wal verkauft, faellt der Preis. Wir wollen:

- Wale finden, auch wenn sie sich verstecken
- Ihr Verhalten analysieren (kaufen, verkaufen, halten)
- Fruehwarnsignale fuer Marktbewegungen erkennen

---

## 2. Das Problem: Adressen verstecken Besitzer

Die Blockchain zeigt nur **Adressen** - nicht **Besitzer**. Ein Wal kann sein Vermoegen auf hunderte Adressen verteilen:

```
Was die Blockchain zeigt:          Realitaet (unsichtbar):

  Adresse 1:  500 BTC                Person A besitzt:
  Adresse 2:  300 BTC      --->      - Adresse 1, 2, 3
  Adresse 3:  200 BTC                - Summe: 1.000 BTC (= WAL!)
  Adresse 4:   50 BTC      --->      Person B: Adresse 4, 5
  Adresse 5:   30 BTC                - Summe: 80 BTC (kein Wal)
```

**Das Problem**: Wenn wir nur einzelne Adressen zaehlen, finden wir diesen Wal nicht!

**Was NICHT funktioniert**:
- Adressen einzeln analysieren (verteilt auf zu viele)
- IP-Adressen tracken (Tor, VPN)
- KYC-Daten nutzen (nicht oeffentlich)

---

## 3. Die Loesung: Common Input Ownership

### Die Kernidee

Um Bitcoin zu senden, muss man den **Private Key** besitzen. Wenn eine Transaktion mehrere Input-Adressen kombiniert, besitzt der Sender ALLE diese Keys:

```
Transaktion TX-123:
  INPUTS (werden kombiniert):       OUTPUT:
  - Adresse A: 0.5 BTC    \
  - Adresse B: 0.3 BTC     >--->    An Bob: 0.9 BTC
  - Adresse C: 0.2 BTC    /

  ERKENNTNIS: Adressen A, B, C gehoeren EINER Person!
              (Nur sie hat alle 3 Private Keys)
```

### Warum das funktioniert

1. **Kryptographisch bewiesen**: Ohne Private Key keine Signatur moeglich
2. **Nicht faelschbar**: Bitcoin-Protokoll erzwingt gueltige Signaturen
3. **Historisch sichtbar**: Alle Transaktionen seit 2009 sind oeffentlich

### Was NICHT gruppiert wird

- **CoinJoin-Transaktionen**: Mehrere Personen kombinieren absichtlich (gefiltert via `max_inputs <= 50`)
- **Exchange-Wallets**: Zentralisierte Verwahrung (separate Erkennung geplant)

---

## 4. Die Pipeline: Warum jeder Schritt noetig ist

Jeder Schritt baut auf dem vorherigen auf:

### Schritt 1: Daten laden (ETL)

**WARUM**: Wir brauchen alle Transaktionen, um Multi-Input-Muster zu finden.

- Blockchair TSV-Dateien enthalten alle Bitcoin-Transaktionen
- Spark ermoeglicht Verarbeitung von Milliarden Zeilen

### Schritt 2: Outputs und Inputs explodieren

**WARUM**: Eine Transaktion hat mehrere Inputs/Outputs. Wir brauchen jede Adresse einzeln.

```
Vorher: TX-123 -> [Addr-A, Addr-B, Addr-C]  (Array)
Nachher:
  TX-123 -> Addr-A
  TX-123 -> Addr-B
  TX-123 -> Addr-C
```

### Schritt 3: UTXO-Set berechnen

**WARUM**: Nur unspent Outputs haben einen aktuellen Wert. Spent = weg.

```
Output erstellt:     TX-100, Output 0, 5 BTC an Addr-A  (UTXO)
Spaeter ausgegeben:  TX-200 nutzt TX-100:0 als Input   (kein UTXO mehr)
```

Ohne UTXO wuerden wir Balances doppelt zaehlen!

### Schritt 4: Graph aufbauen

**WARUM**: Common Input Ownership ist eine **Beziehung** zwischen Adressen. Beziehungen = Graph.

```
TX-100: Input von A + B    -->   A---B
TX-200: Input von B + C    -->   B---C
TX-300: Input von D + E    -->   D---E

Graph:  A---B---C     D---E
        (Entity 1)   (Entity 2)
```

### Schritt 5: Connected Components

**WARUM**: Transitiv verbundene Adressen gehoeren zusammen.

- A kennt B, B kennt C --> A, B, C sind EINE Entity
- GraphFrames findet alle Zusammenhangskomponenten effizient

### Schritt 6: Entity-Balances berechnen

**WARUM**: Erst JETZT koennen wir Wale finden!

```
Entity 1 (Adressen A, B, C):
  UTXO von A: 500 BTC
  UTXO von B: 300 BTC
  UTXO von C: 200 BTC
  SUMME: 1.000 BTC --> WAL!
```

---

## 5. Ergebnis: Was wir ueber Wale lernen

Nach dem Clustering wissen wir:

| Metrik | Wert (Testdaten H1/2011) |
|--------|--------------------------|
| Adressen | ~150.000 |
| Entities | ~110.000 |
| Reduktion | 25% (Adressen gruppiert) |

### Konkrete Analysen

1. **Wal-Ranking**: Top 100 Entities nach Balance
2. **Akkumulation**: Kauft der Wal mehr? (Balance steigt)
3. **Distribution**: Verkauft der Wal? (Balance sinkt)
4. **Dormant**: Wal bewegt sich nicht (potentieller HODLer)

---

## Zusammenfassung: Der rote Faden

```
ZIEL:     Versteckte Wale finden
            |
PROBLEM:  Adressen =/= Besitzer (Wal verteilt auf 100+ Adressen)
            |
LOESUNG:  Common Input Ownership (Multi-Input = gleicher Besitzer)
            |
SCHRITTE: 1. Daten laden      (WEIL: Brauchen alle Transaktionen)
          2. Explodieren      (WEIL: Brauchen einzelne Adressen)
          3. UTXO berechnen   (WEIL: Nur unspent = aktueller Wert)
          4. Graph bauen      (WEIL: Beziehungen abbilden)
          5. Clustering       (WEIL: Zusammenhaenge finden)
          6. Balance          (WEIL: Jetzt erst Wale sichtbar!)
```
