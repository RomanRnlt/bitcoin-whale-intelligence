# Experiment-Guide: Ressourcen-Monitoring & Skalierungsanalyse

## Überblick

Das Notebook `bitcoin_whale_experiments.ipynb` wurde um **7 neue Abschnitte** (16-22) erweitert, die ein umfassendes Experiment-Framework für Ressourcen-Monitoring und Skalierungsanalyse bieten.

## Neue Abschnitte

### Abschnitt 16: Ressourcen-Monitoring & Skalierungsanalyse
**Zellen: 56-57**

- **ResourceMonitor-Klasse**: Überwacht CPU, RAM und Disk I/O während der Pipeline-Ausführung
- **Automatische Messung**: Context Manager für einfache Integration in bestehenden Code
- **Snapshot-basiert**: Sammelt Metriken in regelmäßigen Intervallen

**Verwendung:**
```python
monitor = ResourceMonitor(sample_interval=0.5)
monitor.start()

with monitor.measure_step("Daten laden"):
    df = load_transactions(spark, BLOCKCHAIN_DATA_PATH)

monitor.stop()
summary = monitor.get_step_summary()
```

### Abschnitt 17: Skalierungstest Framework
**Zellen: 58-59**

- **ScalingExperiment-Klasse**: Framework für systematische Skalierungstests
- **Block-basiertes Sampling**: Limitierung der Datenmenge nach Block-Nummer
- **Wiederholbare Tests**: Deterministische Ergebnisse durch feste Block-Auswahl

**Verwendung:**
```python
experiment = ScalingExperiment(spark, BLOCKCHAIN_DATA_PATH, OUTPUT_PATH)
result = experiment.run_single_test(test_name="full")
summary = experiment.get_summary_df()
```

### Abschnitt 18: Visualisierungen
**Zellen: 60-61**

Funktionen zur Darstellung der Ergebnisse:
- `plot_step_resources()`: Balkendiagramme für Dauer und RAM pro Schritt
- `plot_bottleneck_analysis()`: Heatmap der relativen Ressourcennutzung

**Features:**
- Matplotlib + Seaborn für professionelle Visualisierungen
- Automatische Farbcodierung
- Speichern als PNG für Dokumentation

### Abschnitt 19: Automatische Skalierungsempfehlungen
**Zellen: 62-63**

- **Bottleneck-Identifikation**: Analysiert welche Schritte limitierend sind
- **Empfehlungen**: Konkrete Vorschläge zur Optimierung (CPU, RAM, Disk)
- **Skalierungsprognose**: Hochrechnung für größere Datenmengen

**Verwendung:**
```python
print_scaling_report(experiment.results)
```

**Output:**
- Zusammenfassung aller durchgeführten Tests
- Bottleneck-Analyse mit Empfehlungen
- Konkrete Skalierungsempfehlungen für Produktivbetrieb

### Abschnitt 20: Fehlertoleranz und Recovery
**Zellen: 64-65**

- **Checkpoint-System**: Welche Zwischenergebnisse sind gespeichert?
- **Recovery-Anleitung**: Wie setzt man die Pipeline nach Absturz fort?
- **Prozess-Kill-Experimente**: Dokumentation für manuelle Tests

**Wichtig:**
- Im `local[*]` Modus gibt es begrenzte Fehlertoleranz
- Parquet-Checkpoints bleiben erhalten
- Recovery durch Laden der letzten Checkpoints möglich

### Abschnitt 21: Experimente ausführen
**Zellen: 66-69**

Vorkonfigurierte Zellen zum Ausführen der Experimente:
1. **Skalierungstest durchführen**: Führt einen vollständigen Test durch
2. **Visualisierungen erstellen**: Generiert alle Diagramme
3. **Skalierungsbericht ausgeben**: Zeigt Zusammenfassung und Empfehlungen

**Einfache Bedienung:**
- Einfach die Zellen nacheinander ausführen
- Automatische Speicherung der Plots in `images/`
- Interaktive Anzeige der Ergebnisse

### Abschnitt 22: Fazit der Experimente
**Zelle: 70**

Template für die Dokumentation der Ergebnisse:
- **Erkenntnisse-Tabelle**: Strukturierte Zusammenfassung
- **Screenshot-Platzhalter**: Zum Einfügen eigener Visualisierungen
- **Lessons Learned**: Reflexion über Skalierung, Fehlertoleranz und Optimierung

## Workflow für Experimente

### 1. Vorbereitung
```bash
# Stelle sicher dass das Notebook läuft
jupyter notebook bitcoin_whale_experiments.ipynb

# Führe die Zellen 1-55 aus (bisherige Pipeline)
```

### 2. Ressourcen-Monitoring testen
```python
# Zelle 56-57 ausführen
# ResourceMonitor-Klasse ist nun verfügbar
```

### 3. Skalierungstest durchführen
```python
# Zelle 58-59 ausführen (ScalingExperiment-Klasse)
# Zelle 67 ausführen (Test durchführen)
```

### 4. Ergebnisse visualisieren
```python
# Zelle 60-61 ausführen (Visualisierungsfunktionen)
# Zelle 68 ausführen (Plots erstellen)
```

### 5. Empfehlungen erhalten
```python
# Zelle 62-63 ausführen (Empfehlungsfunktionen)
# Zelle 69 ausführen (Bericht anzeigen)
```

### 6. Dokumentieren
- Screenshots der Visualisierungen erstellen
- Tabelle in Abschnitt 22 ausfüllen
- Lessons Learned eintragen

## Anpassungen für Ihre Umgebung

### Datenmengen anpassen
Wenn Ihr Dataset sehr groß oder klein ist, passen Sie die Testgrößen an:

```python
# In Zelle 67 (Experiment ausführen)
# Statt:
result = experiment.run_single_test(test_name="full")

# Für kleineres Dataset:
result = experiment.run_single_test(block_limit=100, test_name="first_100_blocks")

# Für mehrere Tests:
for fraction, name in [(0.1, "10%"), (0.5, "50%"), (1.0, "100%")]:
    limit = int(total_blocks * fraction) if fraction < 1.0 else None
    experiment.run_single_test(block_limit=limit, test_name=name)
```

### Sampling-Intervall anpassen
Für feinere oder grobere Messungen:

```python
# Feiner (alle 0.25 Sekunden)
monitor = ResourceMonitor(sample_interval=0.25)

# Grober (alle 2 Sekunden)
monitor = ResourceMonitor(sample_interval=2.0)
```

### Plots anpassen
Ändern Sie Farben, Größen oder Stile in den Visualisierungsfunktionen (Zelle 61).

## Screenshots erstellen

### macOS
1. **Gesamter Bildschirm**: `Cmd + Shift + 3`
2. **Bereich auswählen**: `Cmd + Shift + 4`
3. **Fenster**: `Cmd + Shift + 4`, dann `Leertaste`

Screenshots werden automatisch auf dem Desktop gespeichert.

### Windows
1. **Gesamter Bildschirm**: `Druck`
2. **Aktives Fenster**: `Alt + Druck`
3. **Snipping Tool**: `Win + Shift + S`

### Screenshots ins Notebook einfügen
1. Screenshot in `notebooks/images/` speichern
2. In Markdown-Zellen einfügen: `![Beschreibung](images/dateiname.png)`

## Prozess-Kill-Experimente

**WARNUNG:** Diese Experimente können den Jupyter-Kernel zum Absturz bringen!

### Vorbereitung
1. Stelle sicher dass Checkpoints aktiviert sind (Parquet-Dateien werden gespeichert)
2. Öffne Aktivitätsanzeige (macOS) oder Task Manager (Windows)

### Durchführung
1. Starte einen Skalierungstest
2. Während der Ausführung: Finde den Python/Java-Prozess
3. Beende den Prozess **gewaltsam**
4. Beobachte was im Jupyter-Notebook passiert

### Recovery testen
1. Kernel neu starten
2. Spark-Session neu initialisieren (Zelle 3)
3. Checkpoints laden (Zelle 65)
4. Pipeline ab dem nächsten Schritt fortsetzen

## Troubleshooting

### "ResourceMonitor gestartet" erscheint nicht
- Stelle sicher dass `psutil` installiert ist: `pip install psutil`

### "Keine Daten verfügbar" bei Visualisierungen
- Führe zuerst einen Skalierungstest aus (Zelle 67)
- Prüfe ob `experiment.results` gefüllt ist

### Plots werden nicht gespeichert
- Prüfe ob `notebooks/images/` existiert: `mkdir -p notebooks/images`
- Prüfe Schreibrechte im Verzeichnis

### Out of Memory beim Skalierungstest
- Reduziere `block_limit` für kleinere Tests
- Erhöhe `spark.driver.memory` in der Konfiguration
- Nutze `spark.catalog.clearCache()` zwischen Tests

## Erwartete Ergebnisse

### Beispiel-Output: Skalierungsbericht
```
======================================================================
SKALIERUNGSBERICHT
======================================================================

### 1. Durchgeführte Tests

Test  Transaktionen  Dauer     RAM Peak  Status
full  1,234,567      45.3s     2048 MB   ✓

### 2. Bottleneck-Analyse

Schritt                Anteil Gesamtzeit  RAM (MB)  CPU Avg  Bottleneck-Typ  Empfehlung
1. Daten laden         15.2%              512       85%      CPU-bound       Mehr CPU-Kerne
2. Outputs extrahieren 8.3%               768       45%      Ausgewogen      -
3. Inputs extrahieren  7.1%               892       42%      Ausgewogen      -
4. UTXO berechnen      69.4%              2048      92%      Zeit-intensiv   Parallelisierung prüfen

### 3. Konkrete Skalierungsempfehlungen

RAM:  Aktuell 2048 MB Peak
      Für 2x Daten: ~4096 MB empfohlen
      spark.driver.memory entsprechend erhöhen

CPU:  Mehr Partitionen bei CPU-bound Schritten
      spark.sql.shuffle.partitions = 200+
```

### Beispiel-Visualisierung: Ressourcenverbrauch
- Balkendiagramm zeigt dass "UTXO berechnen" 70% der Zeit benötigt
- RAM-Verbrauch steigt linear mit Datenmenge
- CPU-Auslastung bei >80% während rechenintensiven Schritten

## Weiterführende Experimente

### Multi-Test-Serie
Teste verschiedene Datenmengen um Skalierungsverhalten zu analysieren:
```python
fractions = [0.05, 0.10, 0.25, 0.50, 0.75, 1.0]
for frac in fractions:
    limit = int(total_blocks * frac)
    experiment.run_single_test(block_limit=limit, test_name=f"{int(frac*100)}%")
```

### Spark-Parameter-Tuning
Teste verschiedene Spark-Konfigurationen:
```python
configs = [
    {"spark.sql.shuffle.partitions": "50"},
    {"spark.sql.shuffle.partitions": "200"},
    {"spark.sql.shuffle.partitions": "500"},
]

for config in configs:
    for key, value in config.items():
        spark.conf.set(key, value)
    experiment.run_single_test(test_name=f"partitions_{value}")
```

### Checkpoint-Overhead messen
Teste wie viel Zeit das Speichern von Checkpoints kostet:
```python
# Mit Checkpoints
with monitor.measure_step("UTXO mit Checkpoint"):
    utxo_df = compute_utxo_set(outputs_df, inputs_df)
    utxo_df.write.mode("overwrite").parquet("utxo.parquet")

# Ohne Checkpoints
with monitor.measure_step("UTXO ohne Checkpoint"):
    utxo_df = compute_utxo_set(outputs_df, inputs_df)
    utxo_df.count()  # Force evaluation
```

## Zusammenfassung

Die neuen Experiment-Sektionen bieten:

✓ **Automatisches Ressourcen-Monitoring** während der Pipeline-Ausführung
✓ **Skalierungstests** mit verschiedenen Datenmengen
✓ **Professionelle Visualisierungen** der Ergebnisse
✓ **Automatische Empfehlungen** zur Optimierung
✓ **Recovery-Mechanismen** nach Prozess-Abstürzen
✓ **Vollständige Dokumentation** der Experimente

**Viel Erfolg bei Ihren Experimenten!**
