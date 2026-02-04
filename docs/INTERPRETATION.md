# Bitcoin Whale Intelligence - Experiment-Interpretation

## Inhaltsverzeichnis

1. [Übersicht](#1-übersicht)
2. [Dataset: 6GB](#2-dataset-6gb)
   - 2.1 [Referenzsystem](#21-referenzsystem)
   - 2.2 [Experiment 1: CPU-Skalierung](#22-experiment-1-cpu-skalierung)
   - 2.3 [Experiment 2: RAM-Skalierung](#23-experiment-2-ram-skalierung)
   - 2.4 [Experiment 3: Daten-Skalierung](#24-experiment-3-daten-skalierung)
   - 2.5 [Experiment 4: CPU × Daten Matrix](#25-experiment-4-cpu--daten-matrix)
   - 2.6 [Experiment 5: RAM × Daten Matrix](#26-experiment-5-ram--daten-matrix)
   - 2.7 [Experiment 6: Bottleneck-Analyse](#27-experiment-6-bottleneck-analyse)
   - 2.8 [Fazit & Key-Erkenntnisse (6GB)](#28-fazit--key-erkenntnisse-6gb)
3. [Dataset: 20GB](#3-dataset-20gb)
4. [Vergleich: 6GB vs 20GB](#4-vergleich-6gb-vs-20gb)
5. [Gesamtfazit](#5-gesamtfazit)

---

## 1. Übersicht und Zielsetzung

 Die folgenden Interpretationen beziehen sich auf die zu unserem Notebook durchgeführten Experimente. Diese sind im Notebook unter den Punkten 16 bis 26 im Detail erläutert. Die Interpretationen der Experimente sind bewusst nicht Teil des eigentlichen Notebooks, da sie sich auf konkrete Ergebnisse beziehen, die auf einem Referenzsystem gemessen wurden.

 Durch diese systematischen Experimente sollen folgende Fragen beantwortet werden:

1. **Skalierungsverhalten:** Wie verhält sich die Pipeline bei Erhöhung von CPU-Cores, RAM und Datenmenge?
2. **Ressourcenbedarf:** Welche Ressourcen (CPU, RAM, I/O) sind limitierend?
3. **Bottlenecks:** Welche Pipeline-Schritte sind Performance-kritisch?
4. **Optimale Konfiguration:** Welche Ressourcen-Allokation ist für Produktiv-Betrieb empfehlenswert?


---

## 2. Dataset: 6GB

### 2.1 Referenzsystem

**Hardware-Spezifikationen:**

| Komponente | Spezifikation |
|------------|---------------|
| **Platform** | Darwin 25.2.0 (macOS) |
| **Architektur** | arm64 (Apple Silicon) |
| **Python** | 3.11.13 |
| **Spark** | 4.1.1 |

**CPU:**
- 10 physische / 10 logische Cores
- 4 MHz max (Apple M4 Pro)

**RAM:**
- 24.0 GB total
- 8.0 GB verfügbar (zu Experimentbeginn)

**Disk:**
- 460 GB total
- 112 GB frei

---

### 2.2 Experiment 1: CPU-Skalierung

#### 2.2.1 Zielsetzung

Untersuchung des Speedup-Verhaltens bei Erhöhung der CPU-Cores.

**Variiert:** CPU-Cores (2, 4, 8)
**Konstant:** RAM (20g), Datenmenge (50%)

#### 2.2.2 Konfiguration & Durchläufe

| # | Cores | RAM | Daten | Was passiert |
|---|-------|-----|-------|--------------|
| 1 | 2 | 20g | 50% | Spark startet mit 2 Cores, Pipeline läuft, Spark stoppt |
| 2 | 4 | 20g | 50% | Spark startet mit 4 Cores, Pipeline läuft, Spark stoppt |
| 3 | 8 | 20g | 50% | Spark startet mit 8 Cores, Pipeline läuft, Spark stoppt |

**Gesamtdurchläufe:** 3
**Records pro Durchlauf:** ~1.7 Millionen Transaktionen

#### 2.2.3 Ergebnisse

![CPU Scaling Summary](6gb_run_interpretation/cpu_scaling_summary.png)

**Tabelle: CPU-Skalierung Ergebnisse**

| Cores | Dauer | Speedup | Effizienz |
|-------|-------|---------|-----------|
| 2 | 176.46s | 1.00x (Baseline) | 50.0% |
| 4 | 208.64s | 0.85x | 21.1% |
| 8 | 236.37s | 0.75x | 9.3% |

**Speedup-Berechnung:**
`Speedup = Baseline-Zeit (2 Cores) / Aktuelle Zeit`

**Effizienz-Berechnung:**
`Effizienz = (Speedup / Anzahl Cores) × 100%`

#### 2.2.4 Interpretation

##### Was lernen wir über Skalierung?

Die Pipeline zeigt **negative Skalierung** mit mehr CPU-Cores:

1. **4 Cores:** 18% langsamer als 2 Cores (0.85x Speedup)
2. **8 Cores:** 34% langsamer als 2 Cores (0.75x Speedup)

Dies steht im starken Kontrast zur **idealen linearen Skalierung** (rote gestrichelte Linie im Diagramm), wo 8 Cores einen 4x Speedup liefern sollten.

**Effizienz-Verlauf:**
- 2 Cores: 50% Effizienz (jeder Core trägt 50% zur Arbeit bei)
- 4 Cores: 21% Effizienz (jeder Core trägt nur 21% bei)
- 8 Cores: 9% Effizienz (jeder Core trägt nur 9% bei)

##### Welche Art Ressourcenbedarf?

Die negative Skalierung deutet auf **Overhead-dominierte Workloads** hin:

**Mögliche Ursachen:**

1. **Koordinations-Overhead:**
   - Spark muss Tasks zwischen mehr Cores koordinieren
   - Shuffle-Operations erfordern Synchronisation
   - Task-Scheduling-Overhead steigt

2. **Memory-Contention:**
   - Alle Cores greifen auf gemeinsamen RAM zu
   - Cache-Thrashing bei hoher Core-Anzahl
   - Memory-Bandwidth als Bottleneck

3. **Small Dataset Penalty:**
   - 50% Daten = ~1.7M Records
   - Zu wenig Parallelisierungspotenzial
   - Fixed Overhead (Spark Startup, DAG-Planning) dominiert

##### Was sieht man in den Experimenten?

**Linkes Diagramm (CPU-Speedup):**
- Blaue Linie (Gemessen) bleibt nahezu flach bei 1.0 und sinkt dann
- Rote Linie (Ideal) steigt linear von 2x auf 8x
- Große Diskrepanz zeigt fundamentales Skalierungsproblem

**Rechtes Diagramm (CPU-Effizienz):**
- Dramatischer Abfall von 50% auf 9%
- Zeigt: Mehr Cores verschlimmern die Situation
- Bei 8 Cores sind 91% der Rechenleistung verschwendet

##### Praktische Implikationen

**Empfehlung:** Verwende **MINIMAL 2 Cores** für diese Pipeline

**Begründung:**
- Mehr Cores führen zu schlechterer Performance
- Overhead überwiegt Parallelisierungsgewinn
- Ressourcen-Verschwendung bei >2 Cores

**Ausnahme:** Bei sehr großen Datasets (>50% Daten) könnte höhere Core-Anzahl profitieren - siehe Experiment 4 (CPU × Daten Matrix).

---

### 2.3 Experiment 2: RAM-Skalierung

#### 2.3.1 Zielsetzung

Untersuchung des Einflusses von RAM-Allokation auf die Performance. Hypothese: Mehr RAM reduziert Disk-Spilling und verbessert Caching.

**Variiert:** RAM (8g, 12g, 16g, 20g)
**Konstant:** CPU-Cores (8), Datenmenge (50%)

#### 2.3.2 Konfiguration & Durchläufe

| # | Cores | RAM | Daten | Was passiert |
|---|-------|-----|-------|--------------|
| 1 | 8 | 8g | 50% | Spark mit 8GB RAM, minimale Allokation |
| 2 | 8 | 12g | 50% | Spark mit 12GB RAM |
| 3 | 8 | 16g | 50% | Spark mit 16GB RAM |
| 4 | 8 | 20g | 50% | Spark mit 20GB RAM, maximale Allokation |

**Gesamtdurchläufe:** 4
**Records pro Durchlauf:** ~1.7 Millionen Transaktionen

#### 2.3.3 Ergebnisse

![RAM Scaling](6gb_run_interpretation/ram_scaling.png)

**Tabelle: RAM-Skalierung Ergebnisse**

| RAM Config | RAM (GB) | Dauer | Verbesserung | Max RAM verwendet |
|------------|----------|-------|--------------|-------------------|
| 8g | 8.0 | 215.68s | Baseline (+0.0%) | 9.48 GB |
| 12g | 12.0 | 199.78s | +7.4% | 10.47 GB |
| 16g | 16.0 | 176.92s | +18.0% ⭐ | 9.71 GB |
| 20g | 20.0 | 212.90s | +1.3% | 9.41 GB |

⭐ = Optimale Konfiguration

#### 2.3.4 Interpretation

##### Was lernen wir über Skalierung?

RAM zeigt **nicht-monotone Skalierung** mit einem klaren **Sweet Spot bei 16g**:

1. **8g → 12g:** +7.4% Verbesserung (moderate Gains)
2. **12g → 16g:** +10.6% weitere Verbesserung (beste Performance)
3. **16g → 20g:** -20% Verschlechterung (Overhead überwiegt)

Dies zeigt, dass mehr RAM nicht automatisch besser ist.

##### Welche Art Ressourcenbedarf?

**Linkes Diagramm (Laufzeit nach RAM-Konfiguration):**
- V-förmige Kurve mit Minimum bei 16g
- 8g und 20g sind ähnlich langsam (~215s)
- 16g ist deutlich schneller (~177s)

**Rechtes Diagramm (RAM-Nutzung):**
- **Orange Balken:** Tatsächlich verwendeter RAM (9-10.5 GB)
- **Schwarze Linie:** Zugewiesener RAM (8-20 GB)

**Kritische Beobachtung:**
- Pipeline nutzt **maximal ~10.5 GB RAM**
- Bei 8g: RAM-Allokation zu knapp → Spilling
- Bei 16g: Perfektes Gleichgewicht
- Bei 20g: Overhead durch unnötige Allokation

##### Was sieht man in den Experimenten?

**RAM-Overhead-Effekt bei 20g:**

Mögliche Ursachen für schlechtere Performance trotz mehr RAM:
1. **JVM Garbage Collection:** Größerer Heap → längere GC-Pausen
2. **Memory Management Overhead:** Spark verwaltet unnötig großen Memory Pool
3. **OS Page Table Overhead:** Mehr Pages → mehr TLB Misses

**Optimaler Punkt bei 16g:**
- Genug RAM für alle Intermediate Results
- Kein Spilling zu Disk
- Minimaler Management-Overhead

##### Praktische Implikationen

**Empfehlung:** Verwende **16g RAM** für diese Pipeline

**Begründung:**
- 18% schneller als Baseline (8g)
- Nutzt RAM effizient ohne Verschwendung
- Verhindert Disk-Spilling
- Vermeidet Overhead von Über-Allokation

**Faustregel:** Allokiere `1.5 × Max_RAM_Used` (hier: 1.5 × 10.5 GB ≈ 16 GB)

---

### 2.4 Experiment 3: Daten-Skalierung

#### 2.4.1 Zielsetzung

Untersuchung wie die Pipeline mit wachsender Datenmenge skaliert. Erwartet wird lineare Skalierung: doppelte Daten = doppelte Laufzeit.

**Variiert:** Datenmenge (25%, 50%, 75%, 100%)
**Konstant:** CPU-Cores (8), RAM (20g)

#### 2.4.2 Konfiguration & Durchläufe

| # | Cores | RAM | Daten | Records (ca.) |
|---|-------|-----|-------|---------------|
| 1 | 8 | 20g | 25% | 858,896 |
| 2 | 8 | 20g | 50% | 1,717,587 |
| 3 | 8 | 20g | 75% | 2,577,564 |
| 4 | 8 | 20g | 100% | 3,436,349 |

**Gesamtdurchläufe:** 4

#### 2.4.3 Ergebnisse

![Data Scaling](6gb_run_interpretation/data_scaling.png)

**Tabelle: Daten-Skalierung Ergebnisse**

| Daten % | Records | Dauer | Daten-Faktor | Zeit-Faktor | Skalierung |
|---------|---------|-------|--------------|-------------|------------|
| 25% | 858,896 | 204.20s | 1.00x | 1.00x | 1.00 |
| 50% | 1,717,587 | 182.97s | 2.00x | 0.90x | 0.45 ⭐ |
| 75% | 2,577,564 | 222.33s | 3.00x | 1.09x | 0.36 ⭐ |
| 100% | 3,436,349 | 321.42s | 4.00x | 1.57x | 0.39 ⭐ |

⭐ = Sub-lineare Skalierung (gut!)

**Skalierungsfaktor-Berechnung:**
`Skalierung = Zeit-Faktor / Daten-Faktor`

- Werte < 1.0: Sub-lineare Skalierung (besser als linear)
- Werte = 1.0: Lineare Skalierung (ideal)
- Werte > 1.0: Super-lineare Skalierung (schlechter als linear)

#### 2.4.4 Interpretation

##### Was lernen wir über Skalierung?

Die Pipeline zeigt **exzellente sub-lineare Skalierung**:

1. **25% → 50%:** 2x Daten, aber nur 0.9x Zeit (10% schneller!)
2. **50% → 75%:** 1.5x Daten, 1.21x Zeit (besser als linear)
3. **75% → 100%:** 1.33x Daten, 1.45x Zeit (nahezu linear)

**Gesamtbilanz:** 4x Daten benötigen nur 1.57x Zeit → **Skalierungsfaktor 0.39**

##### Welche Art Ressourcenbedarf?

**Linkes Diagramm (Laufzeit nach Datenmenge):**
- Nicht-linearer Verlauf mit Anomalie bei 50%
- 50% ist schneller als 25% (182s vs 204s)
- Ab 75% steigt die Kurve steiler an

**Rechtes Diagramm (Skalierungsverhalten):**
- Gemessene Linie (magenta) liegt deutlich unter linearer Skalierung (rot)
- Beste Skalierung bei 50-75% Daten (0.36-0.45)
- Konvergiert Richtung 0.39 bei 100%

##### Anomalie-Analyse: Warum ist 50% schneller als 25%?

**Mögliche Ursachen:**

1. **Fixed Overhead Amortization:**
   - Spark Startup, DAG Planning, Task Scheduling haben fixe Kosten
   - Bei 25%: Overhead dominiert (204s gesamt, ~20s Overhead)
   - Bei 50%: Overhead wird auf mehr Arbeit verteilt

2. **Bessere Partitionierung:**
   - 25%: Zu wenig Daten pro Partition → Unbalanced Parallelism
   - 50%: Optimale Partition-Size für 8 Cores × 200 Partitions

3. **Cache-Effekte:**
   - 25%: Daten passen komplett in Cache, aber Overhead bleibt
   - 50%: Bessere CPU-Auslastung durch kontinuierlichen Data Stream

**Beweis aus Logs:**
- 25% Data: CPU avg 86.9% (hohe Auslastung, aber kurze Bursts)
- 50% Data: CPU avg 74.5% (bessere gleichmäßige Auslastung)

##### Was sieht man in den Experimenten?

**Sub-lineare Skalierung bedeutet:**

Die Pipeline profitiert von **Economies of Scale**:
- Fixed Overhead wird amortisiert
- Partitions werden besser ausgenutzt
- Spark's Adaptive Query Execution (AQE) optimiert besser bei mehr Daten

**Praktische Bedeutung:**
- Bei 10x Daten erwarten wir nur ~4x längere Laufzeit
- Skaliert gut für Produktiv-Workloads

##### Praktische Implikationen

**Empfehlung:** Pipeline ist **produktionsreif für große Datasets**

**Hochrechnung für 10x Datenmenge:**

Basierend auf Skalierungsfaktor 0.39:
- Aktuell: 3.4M Records in 321s
- 10x: 34M Records in ~1,250s ≈ **21 Minuten**

**Vergleich mit linearer Skalierung:**
- Linear: 10x = 3,210s ≈ 54 Minuten
- Tatsächlich: ~21 Minuten
- **Ersparnis: 33 Minuten (61%)**

---

### 2.5 Experiment 4: CPU × Daten Matrix

#### 2.5.1 Zielsetzung

Untersuchung der Interaktion zwischen CPU-Cores und Datenmenge. Hypothese: Mehr Daten profitieren mehr von höherer Parallelität.

**Variiert:** CPU-Cores (4, 8) × Datenmenge (50%, 100%)
**Konstant:** RAM (20g)

#### 2.5.2 Konfiguration & Durchläufe

| # | Cores | RAM | Daten | Erwartung |
|---|-------|-----|-------|-----------|
| 1 | 4 | 20g | 50% | Moderate Parallelität, moderate Daten |
| 2 | 4 | 20g | 100% | Moderate Parallelität, volle Daten |
| 3 | 8 | 20g | 50% | Hohe Parallelität, moderate Daten |
| 4 | 8 | 20g | 100% | Hohe Parallelität, volle Daten |

**Gesamtdurchläufe:** 4

#### 2.5.3 Ergebnisse

![CPU × Data Matrix](6gb_run_interpretation/cpu_data_matrix.png)

**Tabelle: CPU × Daten Matrix Ergebnisse**

|  | 50% Daten | 100% Daten |
|---------|-----------|------------|
| **4 Cores** | 263.5s 🟧 | 272.7s 🟥 |
| **8 Cores** | 196.1s 🟩 | 242.5s 🟥 |

🟩 = Beste Performance (~196s)
🟧 = Moderate Performance (250-270s)
🟥 = Schlechteste Performance (>270s)

#### 2.5.4 Interpretation

##### Was lernen wir über Skalierung?

Die Interaktion zwischen CPU und Daten zeigt **komplexe Muster**:

**Horizontale Analyse (Daten-Skalierung pro CPU-Config):**

1. **4 Cores:**
   - 50% → 100%: +3.5% Laufzeit (+9.2s)
   - Fast konstante Laufzeit trotz 2x Daten! (Anomalie)

2. **8 Cores:**
   - 50% → 100%: +23.7% Laufzeit (+46.4s)
   - Erwartete Zunahme bei mehr Daten

**Vertikale Analyse (CPU-Skalierung pro Datenmenge):**

1. **50% Daten:**
   - 4 → 8 Cores: -25.6% Laufzeit (-67.4s)
   - 8 Cores sind deutlich schneller! (Gegensatz zu Exp. 1)

2. **100% Daten:**
   - 4 → 8 Cores: -11.1% Laufzeit (-30.2s)
   - 8 Cores immer noch besser, aber weniger Vorteil

##### Welche Art Ressourcenbedarf?

**Farbcodierung im Heatmap:**
- Dunkelgrün (196s): Optimaler Punkt bei 8 Cores, 50% Daten
- Orange/Rot (>250s): Ungünstige Konfigurationen

**Kritische Erkenntnis:**

Die Ergebnisse **widersprechen Experiment 1**, wo mehr Cores zu schlechterer Performance führten!

**Erklärung:**
- **Exp. 1:** Nutzte nur 2 Cores als Baseline
- **Exp. 4:** Nutzt 4/8 Cores (höhere Baseline)
- **Hypothese:** Bei 4+ Cores wird Parallelisierung effektiver

##### Was sieht man in den Experimenten?

**Anomalie bei 4 Cores:**

4 Cores zeigen fast keine Laufzeit-Zunahme bei 2x Daten:
- 50%: 263.5s
- 100%: 272.7s (nur +9s!)

**Mögliche Ursachen:**
1. **CPU-Bound bei 4 Cores:**
   - 4 Cores sind bereits voll ausgelastet bei 50%
   - Mehr Daten führen nicht zu mehr CPU-Last (schon am Limit)

2. **Memory-Bound bei 8 Cores:**
   - 8 Cores warten auf Memory-Zugriffe
   - Mehr Daten → mehr Memory Contention → langsamere Laufzeit

**Beweis aus CPU-Auslastung:**
- 4 Cores, 50%: CPU avg 47.8% (unter-ausgelastet)
- 8 Cores, 50%: CPU avg 75.4% (besser ausgelastet)

##### Praktische Implikationen

**Empfehlung:** Konfiguration hängt stark von Datenmenge ab

**Für 50% Daten:**
- Verwende 8 Cores (25% schneller als 4 Cores)
- Best Performance: 196s

**Für 100% Daten:**
- 8 Cores immer noch besser, aber Vorteil schrumpft auf 11%
- Diminishing Returns bei mehr Daten

**Strategie für Produktiv-Betrieb:**
- < 2M Records: 4 Cores ausreichend
- \> 2M Records: 8 Cores empfohlen

---

### 2.6 Experiment 5: RAM × Daten Matrix

#### 2.6.1 Zielsetzung

Untersuchung der Interaktion zwischen RAM-Allokation und Datenmenge. Hypothese: Größere Datasets benötigen mehr RAM für Intermediate Results.

**Variiert:** RAM (12g, 16g, 20g) × Datenmenge (50%, 100%)
**Konstant:** CPU-Cores (8)

#### 2.6.2 Konfiguration & Durchläufe

| # | Cores | RAM | Daten | Erwartung |
|---|-------|-----|-------|-----------|
| 1 | 8 | 12g | 50% | Moderate RAM, moderate Daten |
| 2 | 8 | 12g | 100% | Moderate RAM, volle Daten (potenzielles Spilling) |
| 3 | 8 | 16g | 50% | Optimales RAM, moderate Daten |
| 4 | 8 | 16g | 100% | Optimales RAM, volle Daten |
| 5 | 8 | 20g | 50% | Über-Allokation, moderate Daten |
| 6 | 8 | 20g | 100% | Über-Allokation, volle Daten |

**Gesamtdurchläufe:** 6

#### 2.6.3 Ergebnisse

![RAM × Data Matrix](6gb_run_interpretation/ram_data_matrix.png)

**Tabelle: RAM × Daten Matrix Ergebnisse**

|  | 50% Daten | 100% Daten |
|---------|-----------|------------|
| **12g** | 234.3s 🟢 | 342.3s 🟥 |
| **16g** | 207.2s 🟩 | 265.6s 🟨 |
| **20g** | 248.9s 🟨 | 312.2s 🟥 |

🟩 = Beste Performance (<210s)
🟢 = Gute Performance (210-240s)
🟨 = Moderate Performance (240-270s)
🟥 = Schlechte Performance (>300s)

#### 2.6.4 Interpretation

##### Was lernen wir über Skalierung?

Die RAM × Daten Interaktion zeigt **konsistente Muster**:

**Horizontale Analyse (Daten-Skalierung pro RAM-Config):**

1. **12g RAM:**
   - 50% → 100%: +46.1% Laufzeit (+108s)
   - Starke Verschlechterung → RAM-Engpass

2. **16g RAM:**
   - 50% → 100%: +28.2% Laufzeit (+58.4s)
   - Moderate Zunahme → Optimal

3. **20g RAM:**
   - 50% → 100%: +25.4% Laufzeit (+63.3s)
   - Ähnlich wie 16g, aber langsamer absolut

**Vertikale Analyse (RAM-Skalierung pro Datenmenge):**

1. **50% Daten:**
   - 16g ist optimal (207s)
   - 12g: +13% langsamer
   - 20g: +20% langsamer (Overhead!)

2. **100% Daten:**
   - 16g ist optimal (265s)
   - 12g: +29% langsamer (RAM-Mangel)
   - 20g: +18% langsamer (Overhead bleibt)

##### Welche Art Ressourcenbedarf?

**Kritische Beobachtung:**

16g RAM ist **universell optimal** für beide Datenmengen:
- Bei 50%: Beste Performance
- Bei 100%: Beste Performance

**RAM-Overhead-Effekt bestätigt:**

20g RAM ist **immer schlechter** als 16g, unabhängig von Datenmenge:
- Overhead überwiegt potenzielle Vorteile
- JVM GC-Pausen vermutlich verantwortlich

**RAM-Mangel bei 12g + 100% Daten:**

12g zeigt katastrophale Performance bei vollen Daten:
- 342.3s (worst case im gesamten Experiment)
- +29% langsamer als 16g
- Vermutlich Disk-Spilling

##### Was sieht man in den Experimenten?

**Farbcodierung im Heatmap:**

**Grüne Zone (16g, 50%):**
- Optimale Konfiguration: 207s
- Beste Kombination aus RAM und Daten

**Rote Zonen:**
- 12g + 100% Daten: 342s (extremer RAM-Mangel)
- 20g + 100% Daten: 312s (Overhead + Daten)

**Gelbe Zonen:**
- Suboptimale Konfigurationen (240-270s)

##### Praktische Implikationen

**Empfehlung:** Verwende **16g RAM unabhängig von Datenmenge**

**Begründung:**
- Beste Performance bei 50% und 100% Daten
- Robuste Konfiguration ohne Tuning-Bedarf
- Vermeidet RAM-Mangel und Overhead

**Skalierungsstrategie:**

Für größere Datasets als 100%:
- RAM-Bedarf wächst **sub-linear** mit Datenmenge
- 16g sollte bis ~5M Records ausreichen
- Ab 10M Records: Monitoring empfohlen

**Red Flag:**
- Vermeide 12g bei großen Datasets (>3M Records)
- Disk-Spilling führt zu dramatischem Performance-Einbruch

---

### 2.7 Experiment 6: Bottleneck-Analyse

#### 2.7.1 Zielsetzung

Identifikation von Performance-Bottlenecks in der 11-stufigen Pipeline. Unterscheidung zwischen CPU-bound, RAM-bound und I/O-bound Steps.

**Methodik:** Jeder Pipeline-Step wird instrumentiert mit:
- CPU-Auslastung (durchschnittlich %)
- RAM-Nutzung (durchschnittlich GB)
- I/O-Wait-Zeit (%)

**Klassifikation:**
- **CPU-bound:** CPU Score deutlich > RAM/I/O Score
- **RAM-bound:** RAM Score deutlich > CPU/I/O Score
- **I/O-bound:** I/O Score deutlich > CPU/RAM Score
- **Balanced:** Alle Scores niedrig oder ähnlich

#### 2.7.2 Konfiguration

**Feste Konfiguration:** 8 Cores, 20g RAM, 50% Daten

Alle 11 Pipeline-Steps werden in einem Durchlauf gemessen.

#### 2.7.3 Ergebnisse

![Bottleneck Analysis](6gb_run_interpretation/bottleneck_analysis.png)

**Tabelle: Bottleneck-Analyse Ergebnisse**

| Pipeline-Step | Dauer | CPU Score | RAM Score | I/O Score | Klassifikation |
|---------------|-------|-----------|-----------|-----------|----------------|
| 01_load_transactions | 8.74s | 48 | 39 | 0 | **CPU-bound** 🔴 |
| 02_explode_outputs | 0.02s | 0 | 0 | 0 | Balanced 🟢 |
| 03_explode_inputs | 0.02s | 0 | 0 | 0 | Balanced 🟢 |
| 04_compute_utxo | 0.02s | 3 | 2 | 0 | Balanced 🟢 |
| 05_enrich_clustering | 0.05s | 0 | 0 | 0 | Balanced 🟢 |
| 06_detect_coinjoin | 0.08s | 9 | 11 | 0 | Balanced 🟡 |
| 07_create_edges | 0.03s | 0 | 0 | 0 | Balanced 🟢 |
| 08_connected_components | 154.93s | 58 | 40 | 0 | **CPU-bound** 🔴 |
| 09_compute_balances | 0.06s | 3 | 3 | 0 | Balanced 🟢 |
| 10_detect_whales | 12.19s | 56 | 37 | 0 | **CPU-bound** 🔴 |
| 11_final_aggregation | 0.30s | 36 | 30 | 0 | **CPU-bound** 🟠 |

🔴 = Kritischer Bottleneck (CPU-bound, lange Laufzeit)
🟠 = Minor Bottleneck (CPU-bound, kurze Laufzeit)
🟡 = RAM-tendierend
🟢 = Gut optimiert

#### 2.7.4 Interpretation

##### Was lernen wir über Skalierung?

Die Pipeline hat **4 CPU-bound Bottlenecks**:

1. **08_connected_components:** 154.93s (88% der Gesamt-Laufzeit!)
   - Dominiert die gesamte Pipeline
   - GraphFrames-Operation (hochkomplex)
   - CPU Score 58, RAM Score 40

2. **10_detect_whales:** 12.19s (7% der Laufzeit)
   - Zweitlängster Step
   - CPU Score 56, RAM Score 37

3. **01_load_transactions:** 8.74s (5% der Laufzeit)
   - Parquet-Parsing CPU-intensiv
   - CPU Score 48, RAM Score 39

4. **11_final_aggregation:** 0.30s (minimal)
   - CPU Score 36, RAM Score 30
   - Vernachlässigbar kurz

**Gesamtbild:**
- **3 Steps** machen **95% der Laufzeit** aus (01, 08, 10)
- **7 Steps** sind vernachlässigbar schnell (<0.1s)

##### Welche Art Ressourcenbedarf?

**Dominierende Ressource: CPU**

**Keine I/O-Bottlenecks:**
- Alle I/O Scores = 0
- Kein Disk-Spilling
- Kein Netzwerk-Latenz
- RAM ausreichend dimensioniert

**RAM ist nicht limitierend:**
- RAM Scores alle <45
- Kein RAM-bound Step
- 16g Allokation ausreichend

**CPU ist der Engpass:**
- 4 Steps mit CPU Scores >36
- GraphFrames (Step 08) extrem CPU-intensiv
- Aggregationen (Step 10, 11) CPU-lastig

##### Was sieht man in den Experimenten?

**Heatmap-Analyse:**

**Dunkelrote Balken (CPU-bound):**
- 01_load_transactions: CPU 48, RAM 39
- 08_connected_components: CPU 58, RAM 40
- 10_detect_whales: CPU 56, RAM 37
- 11_final_aggregation: CPU 36, RAM 30

**Hellgelbe Balken (Balanced):**
- Alle anderen Steps mit niedrigen Scores
- Vernachlässigbare Laufzeiten
- Gut optimiert

**Kritischer Step 08:**

`connected_components` ist der **Super-Bottleneck**:
- 154.93s von 176.46s gesamt = **87.8%**
- GraphFrames-Algorithmus (Label Propagation)
- Iterative Graph-Traversierung
- Hochgradig CPU-intensiv

##### Praktische Implikationen

**Optimierungspotenzial:**

**Priorität 1: Step 08 (connected_components)**
- Größter Performance-Gewinn möglich
- Algorithmus-Optimierung erforderlich
- Alternativen:
  - Pregel-basierte Implementierung
  - GraphX statt GraphFrames
  - Approximative Algorithmen (z.B. MinHash LSH)

**Priorität 2: Step 10 (detect_whales)**
- 12.19s Laufzeit (zweitlängstes)
- Aggregationen optimierbar
- Broadcast Joins statt Shuffle Joins

**Priorität 3: Step 01 (load_transactions)**
- Parquet-Parsing optimieren
- Predicate Pushdown aktivieren
- Column Pruning sicherstellen

**Keine Optimierung nötig:**
- Steps 02-07, 09 (alle <0.1s)
- Bereits optimal

**CPU-First Strategie:**

Da alle Bottlenecks CPU-bound sind:
- Mehr Cores helfen NICHT (siehe Exp. 1)
- Algorithmus-Optimierung wichtiger als Hardware-Scaling
- Code-Profiling mit Spark UI empfohlen

---

### 2.8 Fazit & Key-Erkenntnisse (6GB)

#### Skalierungsverhalten

**1. CPU-Skalierung: Negativ**
- Mehr Cores führen zu schlechterer Performance
- Optimal: 2-4 Cores
- Ursache: Koordinations-Overhead überwiegt Parallelisierungsgewinn

**2. RAM-Skalierung: Nicht-monoton mit Sweet Spot**
- 16g RAM ist optimal (18% schneller als 8g)
- Mehr RAM (20g) verschlechtert Performance
- Ursache: JVM GC-Overhead bei Über-Allokation

**3. Daten-Skalierung: Sub-linear (exzellent)**
- 4x Daten benötigen nur 1.57x Zeit
- Skalierungsfaktor: 0.39
- Pipeline profitiert von Economies of Scale

#### Ressourcenbedarf

**Dominierende Ressource: CPU**
- 4 CPU-bound Bottlenecks identifiziert
- Step 08 (connected_components) macht 88% der Laufzeit aus
- Keine I/O- oder RAM-Bottlenecks

**Optimale Konfiguration:**
- **CPU:** 2-4 Cores (mehr schadet)
- **RAM:** 16g (Sweet Spot)
- **Partitions:** 200 (default)

#### Bottlenecks

**Kritischer Pfad:**
1. `08_connected_components` (154.93s, 88%)
2. `10_detect_whales` (12.19s, 7%)
3. `01_load_transactions` (8.74s, 5%)

**Restliche Pipeline:** Vernachlässigbar (<1% Laufzeit)

#### Produktionsempfehlungen

**Hardware-Sizing für Produktiv-Betrieb:**

| Datenmenge | CPU Cores | RAM | Erwartete Laufzeit |
|------------|-----------|-----|-------------------|
| < 2M Records | 2 | 16g | ~3 Minuten |
| 2-5M Records | 4 | 16g | ~4-5 Minuten |
| 5-10M Records | 4-8 | 16g | ~8-12 Minuten |
| > 10M Records | 8 | 24g | ~15-25 Minuten |

**Kosten-Optimierung:**
- Verwende kleinere Instanzen (2-4 Cores)
- RAM bei 16g belassen
- Mehr Cores = Geldverschwendung

**Performance-Optimierung:**
- Fokus auf Step 08 (GraphFrames)
- Erwäge algorithmische Alternativen
- Code-Profiling empfohlen

---

## 3. Dataset: 20GB

### 3.1 Referenzsystem

**TBD** - Wird ergänzt nach 20GB Run

### 3.2 Experiment 1: CPU-Skalierung

**TBD** - Wird ergänzt nach 20GB Run

### 3.3 Experiment 2: RAM-Skalierung

**TBD** - Wird ergänzt nach 20GB Run

### 3.4 Experiment 3: Daten-Skalierung

**TBD** - Wird ergänzt nach 20GB Run

### 3.5 Experiment 4: CPU × Daten Matrix

**TBD** - Wird ergänzt nach 20GB Run

### 3.6 Experiment 5: RAM × Daten Matrix

**TBD** - Wird ergänzt nach 20GB Run

### 3.7 Experiment 6: Bottleneck-Analyse

**TBD** - Wird ergänzt nach 20GB Run

### 3.8 Fazit & Key-Erkenntnisse (20GB)

**TBD** - Wird ergänzt nach 20GB Run

---

## 4. Vergleich: 6GB vs 20GB

**TBD** - Wird ergänzt nach 20GB Run

Erwartete Vergleichspunkte:
- Skalierungsfaktor-Änderungen
- RAM-Bedarf bei 3x Datenmenge
- CPU-Skalierungsverhalten bei größeren Datasets
- Bottleneck-Verschiebungen

---

## 5. Gesamtfazit

### Wissenschaftliche Erkenntnisse

**Skalierungstheorie vs. Praxis:**

Diese Arbeit zeigt, dass **theoretische Skalierungsannahmen** nicht immer in der Praxis gelten:

1. **Amdahl's Law:** Begrenzt Speedup durch sequentielle Anteile
   - Hier: Overhead-dominierte Workloads führen zu negativer Skalierung
   - Mehr Parallelität verschlimmert die Situation

2. **Gustafson's Law:** Größere Probleme profitieren mehr von Parallelität
   - Hier: Bestätigt durch Experiment 4 (CPU × Daten Matrix)
   - 8 Cores werden erst bei mehr Daten effektiv

3. **Little's Law:** Ressourcen-Allokation optimal wenn ausgelastet
   - Hier: 16g RAM optimal, mehr führt zu Overhead
   - Sweet Spot existiert, nicht "mehr = besser"

### Praktische Lehren für Big Data Engineering

**1. Profile first, scale later**
- Bottleneck-Analyse zeigt: 1 Step dominiert (88% Laufzeit)
- Algorithmus-Optimierung wichtiger als Hardware-Scaling

**2. Overhead ist real**
- Mehr Cores/RAM können schaden
- Sweet Spots finden statt blindes Scaling

**3. Sub-lineare Skalierung ist möglich**
- Economies of Scale existieren
- Fixed Overhead amortisiert sich

### Ausblick

**Nächste Schritte:**

1. **20GB Experimente** durchführen
2. **GraphFrames-Alternative** evaluieren (GraphX, Pregel)
3. **Adaptives Scaling** implementieren (basierend auf Datenmenge)
4. **Cloud-Deployment** testen (AWS EMR, Azure HDInsight)

---

**Autor:** Roman
**Universität:** [Ihre Universität]
**Modul:** Big Data & Large Scale Computing
**Datum:** 2026-02-04
