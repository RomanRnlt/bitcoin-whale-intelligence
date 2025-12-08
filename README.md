# Bitcoin Whale Intelligence

Ein Master-Projekt im Modul Advanced Data Engineering, das untersucht, wer wirklich hinter Bitcoin-Adressen steckt und versteckte "Wale" sichtbar macht.

---

## Was ist Bitcoin Whale Intelligence?

Bitcoin Whale Intelligence ist ein Datenanalyse-Projekt, das große Bitcoin-Besitzer ("Wale") identifiziert. Das Besondere: Diese Wale verstecken sich oft hinter hunderten oder tausenden von Adressen. Unser Ziel ist es, diese Adressen zusammenzuführen und zu zeigen, wer wirklich wie viel Bitcoin besitzt.

---

## Das Problem

**800 Millionen Bitcoin-Adressen existieren auf der Blockchain - aber wer besitzt sie wirklich?**

Die Blockchain zeigt nur einzelne Adressen und deren Transaktionen. Was man nicht sieht:

- **Wem die Adressen gehören**: Eine Adresse ist nur eine Zeichenkette, kein Name
- **Welche Adressen zusammengehören**: Eine Person kann beliebig viele Adressen haben
- **Wie viel jemand wirklich besitzt**: Die Summe ist über viele Adressen verteilt

**Ein Beispiel:** Stellen Sie sich einen Wal vor, der 5.000 Bitcoin besitzt. Diese 5.000 Bitcoin könnten auf 1.000 verschiedene Adressen verteilt sein, jede mit nur 5 Bitcoin. Ohne Analyse sieht das aus wie 1.000 kleine Besitzer. In Wirklichkeit ist es eine einzige Person.

---

## Die Lösung: Wem gehören diese Adressen?

Es gibt einen Trick, um herauszufinden, welche Adressen derselben Person gehören. Er basiert auf der Funktionsweise von Bitcoin.

### Wie Bitcoin funktioniert

Bitcoin funktioniert nicht mit Kontoständen wie eine Bank. Stattdessen gibt es "Münzen" (sogenannte UTXOs). Wenn Sie Bitcoin erhalten, bekommen Sie eine Münze mit einem bestimmten Wert. Diese Münze können Sie später ausgeben.

**Der Schlüssel:** Wenn eine Münze nicht reicht, müssen Sie mehrere kombinieren. Und genau da liegt der Hinweis.

### Das Beispiel mit Alice

Alice möchte 0,7 Bitcoin an Bob senden. Sie hat aber:

- Adresse A: eine Münze mit 0,5 BTC
- Adresse B: eine Münze mit 0,3 BTC

Keine der beiden reicht aus. Also kombiniert Alice beide Münzen in einer Transaktion: 0,5 + 0,3 = 0,8 BTC. Sie sendet 0,7 an Bob und bekommt 0,1 als Wechselgeld zurück.

**Was das verrät:** Um beide Münzen zu kombinieren, braucht Alice Zugang zu beiden Adressen. Sie muss also beide besitzen. Diese Transaktion beweist: Adresse A und Adresse B gehören derselben Person.

### Der Graph-Algorithmus

Wir nutzen diese Erkenntnis systematisch:

1. Wir suchen alle Transaktionen, bei denen mehrere Münzen kombiniert wurden
2. Alle Adressen in so einer Transaktion verbinden wir als "zusammengehörig"
3. Ein Graph-Algorithmus findet dann alle Verbindungen und bildet Gruppen (sogenannte "Entities")

Am Ende hat jede Adresse eine Entity-ID. Alle Adressen mit der gleichen ID gehören wahrscheinlich derselben Person oder Organisation.

---

## Was das Projekt macht

Die Analyse-Pipeline besteht aus mehreren Schritten:

### 1. Daten laden

Bitcoin-Blockchain-Daten werden von einem Bitcoin Full Node exportiert. Diese Rohdaten enthalten alle Transaktionen mit allen Details.

### 2. Transformation

Die Rohdaten liegen als JSON vor. Wir wandeln sie in das Parquet-Format um. Das ist ein optimiertes Datenformat, das die Analyse deutlich beschleunigt.

### 3. UTXO Set berechnen

UTXO steht für "Unspent Transaction Output" - also Münzen, die noch nicht ausgegeben wurden. Wir berechnen, welche Münzen aktuell existieren und welchen Wert sie haben.

### 4. Entity Clustering

Der Kernschritt: Wir analysieren alle Transaktionen mit mehreren Eingaben und gruppieren die beteiligten Adressen. Ein Graph-Algorithmus (Connected Components) findet alle zusammengehörigen Adressen.

### 5. Whale Detection (geplant)

Mit den Entity-Gruppen können wir berechnen, wie viel Bitcoin jede Entity besitzt. Entities mit mehr als 1.000 Bitcoin sind potenzielle Wale.

### 6. Verhaltensanalyse (geplant)

Wie verhalten sich die Wale? Kaufen sie gerade zu (Akkumulation) oder verkaufen sie (Distribution)? Diese Informationen können wertvolle Einblicke liefern.

---

## Aktueller Stand

| Status | Schritt |
|--------|---------|
| Erledigt | Daten laden und transformieren |
| Erledigt | UTXO Set Berechnung |
| Erledigt | Entity Clustering mit Graph-Algorithmus |
| Offen | Whale Detection (Balance pro Entity) |
| Offen | Verhaltensanalyse |

---

## Technologie

Das Projekt nutzt bewährte Big-Data-Technologien:

- **Apache Spark**: Ermöglicht die Verarbeitung riesiger Datenmengen, die nicht in den Arbeitsspeicher eines einzelnen Computers passen
- **GraphFrames**: Eine Erweiterung für Spark, die Graph-Algorithmen auf großen Datenmengen ausführen kann
- **Parquet**: Ein spaltenbasiertes Dateiformat, das Daten komprimiert speichert und schnelles Lesen ermöglicht

---

## Projektstruktur

```
bitcoin-whale-intelligence/
├── notebooks/                    # Jupyter Notebooks mit der Analyse
│   └── 01_entity_clustering.ipynb
├── src/                          # Wiederverwendbare Funktionen
│   └── etl.py
├── data/                         # Generierte Datensätze
│   ├── outputs.parquet
│   ├── inputs.parquet
│   └── utxos.parquet
├── docs/                         # Dokumentation
└── start_project.sh              # Startskript
```

**notebooks/**: Hier findet die eigentliche Analyse statt. Das Hauptnotebook führt durch alle Schritte der Pipeline.

**src/**: Enthält Funktionen, die von den Notebooks verwendet werden. Einmal geschrieben, mehrfach nutzbar.

**data/**: Die verarbeiteten Datensätze werden hier als Parquet-Dateien gespeichert.

**docs/**: Zusätzliche Dokumentation für tiefere Einblicke in das Projekt.

---

## Bisherige Ergebnisse

Mit dem Entity Clustering konnten bereits beeindruckende Ergebnisse erzielt werden:

- **Millionen von Transaktionen** wurden verarbeitet
- **Adressen wurden zu Entities gruppiert**: Aus hunderttausenden einzelnen Adressen wurden deutlich weniger Entities
- **Signifikante Reduktion**: Die Anzahl der "Besitzer" reduzierte sich um einen erheblichen Prozentsatz, was zeigt, dass viele Adressen zusammengehören

Diese Ergebnisse bestätigen die Funktionsweise der Common Input Ownership Heuristik und bilden die Grundlage für die geplante Whale Detection.

---

*Master-Projekt | Advanced Data Engineering | Wirtschaftsinformatik*
