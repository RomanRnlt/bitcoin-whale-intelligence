# Experiment-Guide: Ressourcen-Skalierung & Performance-Analyse

## Überblick

Dieses Dokument beschreibt die **Skalierungsexperimente** für die Bitcoin Whale Intelligence Pipeline. Die Experimente beantworten drei zentrale Fragen:

1. **CPU-Skalierung**: Bringen 4 CPUs doppelt so viel wie 2? Wie verhält sich der Speedup?
2. **RAM-Skalierung**: Wird die Pipeline schneller/stabiler mit mehr Arbeitsspeicher?
3. **Daten-Skalierung**: Wie steigt der Ressourcenbedarf mit wachsender Datenmenge?
4. **Kombinierte Analyse**: CPU × Datenmenge, RAM × Datenmenge (2D-Heatmaps)

Das Notebook `bitcoin_whale_explained_experiment.ipynb` wird um **10 neue Abschnitte** (16-25) erweitert.

---

## Zentrale Experiment-Konfiguration

### Das Problem: Hardcoded Werte im Code

Aktuell sind CPU und RAM an verschiedenen Stellen versteckt:
- `DRIVER_MEMORY = "8g"` - existiert, aber nur für RAM
- CPU-Cores werden automatisch ermittelt und sind nicht konfigurierbar
- `get_optimal_partitions()` nutzt System-Werte direkt

### Die Lösung: Konfiguration via `.env` Datei

**Neue Datei: `notebooks/.env.experiment`**

```bash
# ═══════════════════════════════════════════════════════════════════════════════
#                    EXPERIMENT-KONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# === EXPERIMENT AKTIVIEREN ===
EXPERIMENT_MODE=true        # true = Experimente ausführen, false = normale Pipeline

# === Ressourcen für normale Pipeline (wenn EXPERIMENT_MODE=false) ===
SPARK_NUM_CORES=4           # Anzahl CPU-Cores für Spark (1, 2, 4, 8, oder leer für alle)
SPARK_DRIVER_MEMORY=4g      # RAM für Spark Driver (1g, 2g, 4g, 8g)

# === Experiment-Konfiguration (wenn EXPERIMENT_MODE=true) ===
EXPERIMENT_CPU_CONFIGS=1,2,4,8      # Welche Core-Anzahlen testen
EXPERIMENT_RAM_CONFIGS=1g,2g,4g,8g  # Welche RAM-Größen testen
EXPERIMENT_DATA_FRACTIONS=0.25,0.5,1.0  # Welche Datenmengen testen (0.25=25%)

# === Experiment-Einstellungen ===
EXPERIMENT_REPETITIONS=1    # Wiederholungen pro Test (1 = schnell, 3 = statistisch besser)
```

**Im Notebook: `.env` laden und Experiment-Mode prüfen (Abschnitt 3)**

```python
from dotenv import load_dotenv
import os
import platform
import psutil

# .env.experiment laden
load_dotenv(".env.experiment")

# === Experiment-Mode Flag ===
EXPERIMENT_MODE = os.getenv("EXPERIMENT_MODE", "false").lower() == "true"

# === Konfiguration laden ===
if EXPERIMENT_MODE:
    # Experiment-Konfigurationen (werden iteriert)
    EXPERIMENT_CPU_CONFIGS = [int(x) for x in os.getenv("EXPERIMENT_CPU_CONFIGS", "1,2,4,8").split(",")]
    EXPERIMENT_RAM_CONFIGS = os.getenv("EXPERIMENT_RAM_CONFIGS", "1g,2g,4g,8g").split(",")
    EXPERIMENT_DATA_FRACTIONS = [float(x) for x in os.getenv("EXPERIMENT_DATA_FRACTIONS", "0.25,0.5,1.0").split(",")]
    EXPERIMENT_REPETITIONS = int(os.getenv("EXPERIMENT_REPETITIONS", "1"))

    print("🧪 EXPERIMENT-MODE AKTIVIERT")
    print(f"   CPU-Configs: {EXPERIMENT_CPU_CONFIGS}")
    print(f"   RAM-Configs: {EXPERIMENT_RAM_CONFIGS}")
    print(f"   Daten-Configs: {[f'{x*100:.0f}%' for x in EXPERIMENT_DATA_FRACTIONS]}")
else:
    # Normale Pipeline-Konfiguration
    NUM_CORES = int(os.getenv("SPARK_NUM_CORES")) if os.getenv("SPARK_NUM_CORES") else None
    DRIVER_MEMORY = os.getenv("SPARK_DRIVER_MEMORY", "4g")
    print(f"📊 Normale Pipeline: {NUM_CORES or 'alle'} Cores, {DRIVER_MEMORY} RAM")
```

**Referenzsystem automatisch erfassen:**

```python
def get_system_info() -> dict:
    """Erfasst Hardware-Informationen des aktuellen Systems."""
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_model": platform.processor(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "python_version": platform.python_version(),
        "spark_version": spark.version if 'spark' in dir() else "N/A",
    }

# Beispiel-Output:
# {
#     "hostname": "Romans-MacBook-Pro",
#     "os": "Darwin 23.1.0",
#     "cpu_model": "Apple M1 Pro",
#     "cpu_cores_physical": 8,
#     "cpu_cores_logical": 8,
#     "ram_total_gb": 16.0,
#     "python_version": "3.11.5",
#     "spark_version": "3.5.0"
# }
```

**Im Report wird das Referenzsystem dokumentiert:**

```markdown
## Referenzsystem

| Eigenschaft | Wert |
|-------------|------|
| Hostname | Romans-MacBook-Pro |
| Betriebssystem | Darwin 23.1.0 (macOS Sonoma) |
| CPU | Apple M1 Pro |
| CPU Cores (physisch) | 8 |
| CPU Cores (logisch) | 8 |
| RAM Total | 16.0 GB |
| Python | 3.11.5 |
| Spark | 3.5.0 |
| Experiment-Datum | 2024-01-15 14:32:00 |
```

**Vorteile der `.env` Lösung:**
- Notebook muss nicht geändert werden
- Verschiedene Konfigurationen durch Kopieren der `.env` Datei
- Kann versioniert werden (z.B. `.env.experiment.4cores`, `.env.experiment.8cores`)
- Standard-Pattern in der Entwicklung

### Code-Änderungen erforderlich

**1. `get_optimal_partitions()` erweitern:**

```python
def get_optimal_partitions(num_cores: int | None = None, memory_gb: float | None = None) -> int:
    """Berechnet optimale Partition-Anzahl.

    Args:
        num_cores: Anzahl Cores (None = System-Wert)
        memory_gb: RAM in GB (None = System-Wert)
    """
    cores = num_cores or os.cpu_count() or 4
    ram = memory_gb or (psutil.virtual_memory().total / (1024**3))

    base_partitions = cores * 2
    memory_factor = max(1, int(ram / 4))
    return min(base_partitions * memory_factor, 200)
```

**2. `create_spark_session()` erweitern:**

```python
def create_spark_session(
    app_name: str = "Bitcoin Whale Intelligence",
    driver_memory: str = "4g",
    num_cores: int | None = None,  # NEU: None = alle Cores
    *,
    enable_graphframes: bool = True,
    suppress_logs: bool = True,
) -> SparkSession:
    """Erstellt Spark Session mit konfigurierbaren Ressourcen."""

    # Cores bestimmen
    if num_cores is None:
        cores = os.cpu_count() or 4
        workers = min(cores, 8)
    else:
        workers = num_cores

    # Partitionen basierend auf konfigurierten Werten
    memory_gb = int(driver_memory.rstrip('g'))
    optimal_partitions = get_optimal_partitions(workers, memory_gb)

    builder = (
        SparkSession.builder.appName(app_name)
        .master(f"local[{workers}]")  # Konfigurierbar!
        .config("spark.driver.memory", driver_memory)
        # ... rest bleibt gleich
    )
```

**3. Spark-Initialisierung anpassen:**

```python
# Spark initialisieren mit konfigurierten Werten
spark = create_spark_session(
    app_name="Bitcoin Whale Analysis",
    driver_memory=DRIVER_MEMORY,
    num_cores=NUM_CORES,  # NEU!
    enable_graphframes=True
)
```

### Datenmenge für CPU/RAM-Experimente

**Empfehlung: Mittlere Datenmenge (50%) oder festes Block-Limit**

| Experiment-Typ | Empfohlene Datenmenge | Begründung |
|----------------|----------------------|-------------|
| CPU-Skalierung | 50% oder ~500 Blöcke | Groß genug für messbare Unterschiede, schnell genug für 3x Wiederholungen |
| RAM-Skalierung | 50% oder ~500 Blöcke | Gleiche Begründung |
| Daten-Skalierung | 10%, 25%, 50%, 75%, 100% | Volle Bandbreite testen |
| Kombiniert (CPU×Daten) | 25%, 50%, 100% × 2,4,8 Cores | Reduzierte Matrix für praktikable Laufzeit |

**Warum 50%?**
- Bei 100%: Ein Test dauert z.B. 5 Minuten → 4 CPU-Configs × 3 Wiederholungen = 60 Minuten nur für CPU-Test
- Bei 50%: Ein Test dauert ~2.5 Minuten → 4 CPU-Configs × 3 Wiederholungen = 30 Minuten
- 50% ist repräsentativ genug um Skalierungsverhalten zu zeigen

---

## Wissenschaftliche Fragestellungen

### Frage 1: CPU-Skalierung (Horizontale Skalierung)
> "Bringen 4 CPUs doppelt so viel wie 2?"

**Hypothese**: Bei datenparallelen Operationen (wie Spark sie durchführt) erwarten wir nahezu linearen Speedup bis zur Sättigung durch I/O oder Synchronisation.

**Metriken**:
- **Speedup**: S(n) = T(1) / T(n) - Wie viel schneller ist n Cores vs. 1 Core?
- **Effizienz**: E(n) = S(n) / n - Wie gut wird jeder zusätzliche Core genutzt?
- **Amdahl's Law**: Theoretisches Maximum basierend auf parallelisierbarem Anteil

### Frage 2: RAM-Skalierung (Vertikale Skalierung)
> "Wird alles schneller mit 2x mehr RAM?"

**Hypothese**: Mehr RAM reduziert Disk-Spilling und ermöglicht größere In-Memory-Operationen, aber der Effekt ist nicht linear.

**Metriken**:
- **Spill-to-Disk**: Wie oft muss Spark auf Festplatte ausweichen?
- **GC-Overhead**: Garbage Collection Pausen bei verschiedenen Heap-Größen
- **Durchsatz**: Transaktionen pro Sekunde bei verschiedenen RAM-Konfigurationen

### Frage 3: Daten-Skalierung
> "Wie steigt der Ressourcenbedarf mit wachsender Datenmenge?"

**Hypothese**: Die meisten Operationen skalieren O(n), aber Joins und Aggregationen können O(n log n) oder schlechter sein.

**Metriken**:
- **Laufzeit vs. Datenmenge**: Linear, superlinear oder sublinear?
- **RAM-Peak vs. Datenmenge**: Wie wächst der Speicherbedarf?
- **CPU-Auslastung**: Bleibt sie konstant oder ändert sie sich?

---

## Experiment-Design

### Experiment-Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXPERIMENT-MATRIX                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXPERIMENT 1: CPU-Skalierung (fixe Datenmenge, fixes RAM)                  │
│  ┌──────────┬──────────┬──────────┬──────────┐                              │
│  │ 1 Core   │ 2 Cores  │ 4 Cores  │ 8 Cores  │  → Speedup-Kurve            │
│  └──────────┴──────────┴──────────┴──────────┘                              │
│                                                                             │
│  EXPERIMENT 2: RAM-Skalierung (fixe Datenmenge, fixe CPUs)                  │
│  ┌──────────┬──────────┬──────────┬──────────┐                              │
│  │ 1 GB     │ 2 GB     │ 4 GB     │ 8 GB     │  → RAM-Impact-Kurve         │
│  └──────────┴──────────┴──────────┴──────────┘                              │
│                                                                             │
│  EXPERIMENT 3: Daten-Skalierung (fixe Ressourcen)                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐                   │
│  │ 10%      │ 25%      │ 50%      │ 75%      │ 100%     │  → Skalierungs-  │
│  │ Daten    │ Daten    │ Daten    │ Daten    │ Daten    │    verhalten     │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Kontrollierte Variablen

| Experiment | Variiert | Konstant |
|------------|----------|----------|
| CPU-Skalierung | Anzahl Cores (1, 2, 4, 8) | RAM (4GB), Datenmenge (100%) |
| RAM-Skalierung | Heap-Größe (1, 2, 4, 8 GB) | Cores (4), Datenmenge (100%) |
| Daten-Skalierung | Datenmenge (10-100%) | Cores (4), RAM (4GB) |

### Wiederholungen

Jeder Test wird standardmäßig **1x ausgeführt** (konfigurierbar via `EXPERIMENT_REPETITIONS`).
Bei mehreren Wiederholungen werden gemessen:
- Mittelwert
- Standardabweichung
- Min/Max

---

## Neue Notebook-Abschnitte

### Abschnitt 16: Ressourcen-Monitoring Framework

**Was ist das?**
Eine Python-Klasse die **während der Pipeline-Ausführung** System-Ressourcen misst.
Nutzt `psutil` um CPU, RAM und Disk I/O in regelmäßigen Intervallen zu samplen.

**ResourceMonitor-Klasse:**

```python
class ResourceMonitor:
    """Überwacht CPU, RAM, Disk I/O während der Ausführung."""

    def __init__(self, sample_interval: float = 0.5):
        """Sample alle 0.5 Sekunden."""

    def measure_step(self, name: str):
        """Context Manager - misst alles innerhalb des with-Blocks."""

    def get_metrics(self, step_name: str) -> dict:
        """Liefert Metriken für einen Schritt."""

# Beispiel-Nutzung:
monitor = ResourceMonitor()

with monitor.measure_step("UTXO berechnen"):
    utxo_df = compute_utxo(outputs_df, inputs_df)
    utxo_df.write.parquet("utxo.parquet")

with monitor.measure_step("Graph bauen"):
    edges_df = build_graph(inputs_for_clustering)

# Ergebnisse abrufen:
metrics = monitor.get_metrics("UTXO berechnen")
# → {
#     "duration_sec": 45.2,
#     "cpu_avg": 78.5,      # Durchschnittliche CPU-Auslastung in %
#     "cpu_peak": 98.2,     # Maximale CPU-Auslastung in %
#     "ram_avg_mb": 1856,   # Durchschnittlicher RAM in MB
#     "ram_peak_mb": 2048,  # Maximaler RAM in MB
#     "disk_read_mb": 512,  # Gelesene Daten in MB
#     "disk_write_mb": 256, # Geschriebene Daten in MB
# }
```

**Gemessene Metriken pro Pipeline-Schritt**:
| Metrik | Beschreibung | Einheit |
|--------|--------------|---------|
| `duration_sec` | Gesamtdauer des Schritts | Sekunden |
| `cpu_avg` | Durchschnittliche CPU-Auslastung | % |
| `cpu_peak` | Maximale CPU-Auslastung | % |
| `ram_avg_mb` | Durchschnittlicher RAM-Verbrauch | MB |
| `ram_peak_mb` | Maximaler RAM-Verbrauch (Peak) | MB |
| `disk_read_mb` | Gelesene Daten von Disk | MB |
| `disk_write_mb` | Geschriebene Daten auf Disk | MB |

### Abschnitt 17: CPU-Skalierungsexperiment

**Fragestellung**: Wie verhält sich die Laufzeit bei 1, 2, 4, 8 CPU-Cores?

```python
class CPUScalingExperiment:
    """Testet Pipeline-Performance mit verschiedenen Core-Anzahlen."""

    def run(self, core_counts: list = [1, 2, 4, 8], repetitions: int = 3):
        """
        Für jeden Core-Count:
        1. Spark-Session mit local[n] neu starten
        2. Pipeline ausführen
        3. Metriken sammeln
        4. 3x wiederholen für statistische Signifikanz
        """
```

**Output**:
- Tabelle: Cores | Laufzeit (mean±std) | Speedup | Effizienz
- Plot: Speedup-Kurve mit idealem linearem Speedup als Referenz
- Plot: Effizienz-Kurve (sollte bei 100% starten und fallen)

**Erwartete Erkenntnis**:
- Linearer Speedup bis ~4 Cores, dann Abflachung durch I/O-Bottleneck
- Effizienz sinkt mit steigender Core-Anzahl (Amdahl's Law)

### Abschnitt 18: RAM-Skalierungsexperiment

**Fragestellung**: Wird die Pipeline schneller/stabiler mit mehr RAM?

```python
class RAMScalingExperiment:
    """Testet Pipeline-Performance mit verschiedenen Heap-Größen."""

    def run(self, ram_configs: list = ["1g", "2g", "4g", "8g"], repetitions: int = 3):
        """
        Für jede RAM-Konfiguration:
        1. Spark-Session mit spark.driver.memory=Xg neu starten
        2. Pipeline ausführen
        3. Spill-Metriken und GC-Overhead messen
        4. 3x wiederholen
        """
```

**Output**:
- Tabelle: RAM | Laufzeit | Spill-to-Disk (MB) | GC-Overhead (%)
- Plot: Laufzeit vs. RAM (erwarte: stark fallend, dann Plateau)
- Plot: Spill-to-Disk vs. RAM (erwarte: exponentiell fallend)

**Erwartete Erkenntnis**:
- Unter einem Schwellwert: Massives Disk-Spilling, langsam
- Über Schwellwert: Kaum noch Verbesserung
- Sweet-Spot identifizieren

### Abschnitt 19: Daten-Skalierungsexperiment

**Fragestellung**: Wie skaliert der Ressourcenbedarf mit der Datenmenge?

```python
class DataScalingExperiment:
    """Testet Pipeline-Performance mit verschiedenen Datenmengen."""

    def run(self, data_fractions: list = [0.1, 0.25, 0.5, 0.75, 1.0], repetitions: int = 3):
        """
        Für jede Datenmenge:
        1. Block-Limit setzen (z.B. 10% = erste 10% der Blöcke)
        2. Pipeline ausführen
        3. Ressourcen-Verbrauch messen
        4. 3x wiederholen
        """
```

**Output**:
- Tabelle: Datenmenge | Transaktionen | Laufzeit | RAM-Peak | CPU-Avg
- Plot: Laufzeit vs. Datenmenge (linear? superlinear?)
- Plot: RAM-Peak vs. Datenmenge
- Regressionsanalyse: Bestimmung der Skalierungskomplexität

**Erwartete Erkenntnis**:
- Daten laden: O(n)
- UTXO-Berechnung: O(n) oder O(n log n)
- Graph-Clustering: Potentiell superlinear

### Abschnitt 20: Kombinierte Experimente (2D-Analyse)

**NEU: CPU × Datenmenge und RAM × Datenmenge**

```python
class CombinedScalingExperiment:
    """Testet Kombinationen aus Ressourcen und Datenmengen."""

    def run_cpu_data_matrix(
        self,
        core_counts: list = [2, 4, 8],
        data_fractions: list = [0.25, 0.5, 1.0],
        repetitions: int = 3
    ) -> pd.DataFrame:
        """
        Führt Matrix-Experiment durch:
        - Für jede Kombination (cores, data_fraction)
        - Spark neu starten mit entsprechenden Cores
        - Pipeline mit entsprechender Datenmenge ausführen
        - 3x wiederholen

        Returns:
            DataFrame mit Spalten: cores, data_fraction, runtime_mean, runtime_std, ...
        """

    def run_ram_data_matrix(
        self,
        ram_configs: list = ["2g", "4g", "8g"],
        data_fractions: list = [0.25, 0.5, 1.0],
        repetitions: int = 3
    ) -> pd.DataFrame:
        """Analog für RAM × Datenmenge."""
```

**Output: 2D-Heatmaps**

```
CPU × Datenmenge (Laufzeit in Sekunden):
              25% Daten    50% Daten    100% Daten
2 Cores         15s          32s          68s
4 Cores          9s          18s          38s
8 Cores          6s          13s          28s

→ Zeigt: Mehr Cores helfen proportional bei allen Datenmengen
```

**Visualisierung:**
- Heatmap mit Farbskala (grün=schnell, rot=langsam)
- Oder 3D-Surface-Plot
- Liniendiagramm: Mehrere Kurven (eine pro Core-Anzahl) über Datenmenge

### Abschnitt 21: Bottleneck-Analyse pro Pipeline-Schritt

**Was ist das?**
Eine Auswertung der ResourceMonitor-Daten, die für jeden Pipeline-Schritt bestimmt:
- **Was ist der limitierende Faktor?** (CPU, RAM oder Disk)
- **Was sollte man verbessern?** (Konkrete Empfehlung)

**Die Logik dahinter:**

| Wenn... | Dann ist der Schritt... | Empfehlung |
|---------|------------------------|------------|
| CPU >80%, RAM <60% | **CPU-bound** | Mehr Cores helfen |
| RAM >80%, CPU <60% | **Memory-bound** | Mehr RAM hilft |
| Disk I/O hoch, CPU+RAM niedrig | **I/O-bound** | Schnellere SSD hilft |
| Alles niedrig | **Ausgewogen** | Keine Aktion nötig |

```python
def analyze_bottlenecks(monitor_results: dict) -> pd.DataFrame:
    """
    Analysiert die Metriken und klassifiziert jeden Schritt.

    Returns:
        DataFrame mit Spalten:
        - step_name: Name des Pipeline-Schritts
        - cpu_avg: CPU-Auslastung
        - ram_peak_mb: RAM-Peak
        - disk_io_mb: Disk I/O
        - bottleneck_type: "CPU-bound", "Memory-bound", "I/O-bound", "Ausgewogen"
        - recommendation: Konkrete Empfehlung
    """

# Beispiel-Output:
"""
Schritt              CPU    RAM     Disk   Bottleneck     Empfehlung
─────────────────────────────────────────────────────────────────────────
Daten laden          25%    512MB   1.2GB  I/O-bound      SSD nutzen, JSON→Parquet
UTXO berechnen       92%    2.0GB   100MB  CPU-bound      Mehr Cores (aktuell: 4)
Graph-Clustering     35%    3.8GB   50MB   Memory-bound   Mehr RAM (aktuell: 4GB)
Whale Detection      45%    1.2GB   80MB   Ausgewogen     -
"""
```

**Visualisierung: Bottleneck-Heatmap**

```
                    CPU     RAM     Disk
                   ─────   ─────   ─────
Daten laden        [  ]    [  ]    [██]   ← I/O-bound (Disk rot)
UTXO berechnen     [██]    [░░]    [  ]   ← CPU-bound (CPU rot)
Graph-Clustering   [░░]    [██]    [  ]   ← Memory-bound (RAM rot)
Whale Detection    [░░]    [░░]    [  ]   ← Ausgewogen

Legende: [██] >80%  [░░] 40-80%  [  ] <40%
```

**Warum ist das nützlich?**
- Zeigt wo man investieren sollte (mehr RAM kaufen vs. mehr Cores?)
- Identifiziert Optimierungspotential (z.B. JSON→Parquet für I/O-bound Schritte)
- Erklärt warum manche Schritte nicht von mehr Ressourcen profitieren

### Abschnitt 22: Visualisierungen

**Professionelle Plots für alle Experimente**:

```python
# === 1D-Plots (einzelne Dimension variiert) ===

def plot_cpu_scaling(results: dict):
    """
    Zwei Subplots:
    1. Speedup-Kurve: Gemessen vs. Ideal (linear)
    2. Effizienz-Kurve: E(n) = S(n)/n
    """

def plot_ram_scaling(results: dict):
    """
    Zwei Subplots:
    1. Laufzeit vs. RAM-Größe
    2. Spill-to-Disk vs. RAM-Größe
    """

def plot_data_scaling(results: dict):
    """
    Drei Subplots:
    1. Laufzeit vs. Datenmenge (mit Regressionslinie)
    2. RAM-Peak vs. Datenmenge
    3. CPU-Auslastung vs. Datenmenge
    """

# === 2D-Plots (zwei Dimensionen variiert) ===

def plot_cpu_data_heatmap(results: pd.DataFrame):
    """
    Heatmap: CPU-Cores × Datenmenge
    - X-Achse: Datenmenge (25%, 50%, 100%)
    - Y-Achse: CPU-Cores (2, 4, 8)
    - Farbe: Laufzeit (grün=schnell, rot=langsam)
    - Annotationen: Konkrete Werte in jeder Zelle
    """

def plot_ram_data_heatmap(results: pd.DataFrame):
    """
    Heatmap: RAM × Datenmenge
    - X-Achse: Datenmenge (25%, 50%, 100%)
    - Y-Achse: RAM (2GB, 4GB, 8GB)
    - Farbe: Laufzeit
    """

def plot_scaling_lines(results: pd.DataFrame, group_by: str = "cores"):
    """
    Liniendiagramm mit mehreren Kurven:
    - X-Achse: Datenmenge
    - Y-Achse: Laufzeit
    - Linien: Eine pro Core-Anzahl (oder RAM-Größe)

    Zeigt ob die Kurven parallel verlaufen (= gute Skalierung)
    oder divergieren (= Bottleneck bei großen Daten)
    """

def plot_bottleneck_heatmap(results: dict):
    """
    Heatmap: Pipeline-Schritte × Ressourcen-Typ
    Farbe zeigt relative Auslastung (CPU, RAM, Disk)
    """
```

### Abschnitt 23: Skalierungsempfehlungen

**Automatische Empfehlungen basierend auf Messergebnissen**:

```python
def generate_scaling_recommendations(all_results: dict) -> str:
    """
    Generiert konkreten Bericht:

    1. CPU-Empfehlung:
       "4 Cores bieten 3.2x Speedup (80% Effizienz).
        8 Cores bieten nur 4.1x Speedup (51% Effizienz).
        → 4 Cores sind der Sweet-Spot für dieses Dataset."

    2. RAM-Empfehlung:
       "Unter 2GB: 45% Disk-Spilling, 2.3x langsamer.
        Bei 4GB: Kein Spilling, optimale Performance.
        Über 4GB: Keine weitere Verbesserung.
        → Mindestens 4GB RAM empfohlen."

    3. Skalierungsprognose:
       "Für 10x größeres Dataset:
        - Geschätzte Laufzeit: ~45 Minuten (aktuell: 5 Min)
        - Geschätzter RAM-Bedarf: ~12GB
        - Empfohlene Cores: 8+"

    4. Kombinierte Analyse:
       "CPU-Skalierung ist unabhängig von Datenmenge:
        Speedup von 4 Cores bleibt bei ~3x für alle Datenmengen.
        → Parallelisierung skaliert gut."
    """
```

### Abschnitt 24: Vollautomatische Experiment-Durchführung

**Ziel: Eine Zelle ausführen → Alle Experimente laufen → Ergebnisse werden gespeichert**

```python
def run_all_experiments(
    spark_creator,  # Funktion zum Erstellen von Spark Sessions
    data_path: str,
    output_path: str,
) -> dict:
    """
    Führt ALLE Experimente vollautomatisch durch.

    Ablauf:
    1. CPU-Skalierung: 1, 2, 4, 8 Cores (je 3x Wiederholung)
    2. RAM-Skalierung: 1, 2, 4, 8 GB (je 3x Wiederholung)
    3. Daten-Skalierung: 10%, 25%, 50%, 75%, 100% (je 3x Wiederholung)
    4. Kombiniert: CPU × Daten Matrix
    5. Kombiniert: RAM × Daten Matrix

    Für jedes Experiment:
    - Spark Session mit entsprechender Config starten
    - Alle Pipeline-Schritte durchlaufen
    - Metriken pro Schritt sammeln
    - Ergebnisse speichern
    - Spark Session beenden

    Returns:
        dict mit allen Ergebnissen
    """
```

**Gemessene Pipeline-Schritte (alle 11):**

```python
PIPELINE_STEPS = [
    ("Daten laden", lambda: load_transactions(spark, data_path)),
    ("Outputs extrahieren", lambda: extract_outputs(transactions_df)),
    ("Inputs extrahieren", lambda: extract_inputs(transactions_df)),
    ("UTXO berechnen", lambda: compute_utxo(outputs_df, inputs_df)),
    ("Common Input Ownership", lambda: prepare_clustering_inputs(inputs_df, outputs_df)),
    ("CoinJoin-Filterung", lambda: filter_coinjoin(clustering_inputs)),
    ("Graph bauen", lambda: build_address_graph(filtered_inputs)),
    ("Connected Components", lambda: find_connected_components(graph)),
    ("Whale Detection", lambda: detect_whales(components_df, utxo_df)),
    ("Visualisierung", lambda: create_whale_visualizations(whales_df)),
    ("Zeitreihen-Analyse", lambda: analyze_whale_timeseries(whales_df, utxo_history)),
]
```

**Ausgabe-Struktur:**

```
output/
└── experiments/
    ├── results/
    │   ├── cpu_scaling.json          # Rohdaten CPU-Experiment
    │   ├── ram_scaling.json          # Rohdaten RAM-Experiment
    │   ├── data_scaling.json         # Rohdaten Daten-Experiment
    │   ├── cpu_data_matrix.json      # Rohdaten CPU×Daten
    │   ├── ram_data_matrix.json      # Rohdaten RAM×Daten
    │   └── all_results.json          # Alles zusammen
    │
    ├── plots/
    │   ├── cpu_speedup.png           # Speedup-Kurve
    │   ├── cpu_efficiency.png        # Effizienz-Kurve
    │   ├── ram_impact.png            # RAM-Impact
    │   ├── data_scaling.png          # Daten-Skalierung
    │   ├── cpu_data_heatmap.png      # CPU×Daten Heatmap
    │   ├── ram_data_heatmap.png      # RAM×Daten Heatmap
    │   ├── scaling_lines.png         # Multi-Linien-Plot
    │   └── bottleneck_heatmap.png    # Bottleneck-Analyse
    │
    ├── tables/
    │   ├── cpu_scaling.csv           # Tabelle für Report
    │   ├── ram_scaling.csv
    │   ├── data_scaling.csv
    │   ├── bottleneck_analysis.csv
    │   └── recommendations.txt       # Automatische Empfehlungen
    │
    └── report/
        └── experiment_report.md      # Vollständiger Bericht (Markdown)
```

**Automatische Ausführung via EXPERIMENT_MODE Flag:**

Das Notebook prüft am Ende automatisch das Flag und führt bei Bedarf alle Experimente aus:

```python
# ══════════════════════════════════════════════════════════════════════════════
# AUTOMATISCHE EXPERIMENT-AUSFÜHRUNG (am Ende des Notebooks)
# ══════════════════════════════════════════════════════════════════════════════

if EXPERIMENT_MODE:
    print("🧪 Starte automatische Experiment-Ausführung...")
    print(f"   Referenzsystem: {get_system_info()['cpu_model']}, {get_system_info()['ram_total_gb']}GB RAM")

    # Alle Experimente durchführen
    results = run_all_experiments(
        spark_creator=create_spark_session,
        data_path=BLOCKCHAIN_DATA_PATH,
        output_path=OUTPUT_PATH,
        cpu_configs=EXPERIMENT_CPU_CONFIGS,
        ram_configs=EXPERIMENT_RAM_CONFIGS,
        data_fractions=EXPERIMENT_DATA_FRACTIONS,
        repetitions=EXPERIMENT_REPETITIONS,
        system_info=get_system_info(),  # Referenzsystem wird mit gespeichert!
    )

    # Report generieren (inkl. Referenzsystem)
    generate_report(results, output_path=f"{OUTPUT_PATH}/experiments")

    print(f"\n✓ Fertig! Ergebnisse in: {OUTPUT_PATH}/experiments/")
else:
    print("ℹ️  Experiment-Mode ist deaktiviert.")
    print("   Setze EXPERIMENT_MODE=true in .env.experiment um Experimente auszuführen.")
```

**Workflow für den User:**

```bash
# 1. .env.experiment anpassen
EXPERIMENT_MODE=true
EXPERIMENT_CPU_CONFIGS=2,4,8
EXPERIMENT_DATA_FRACTIONS=0.5,1.0

# 2. Notebook komplett ausführen (Run All)
jupyter notebook bitcoin_whale_explained_experiment.ipynb
# → Kernel → Run All

# 3. Warten... (Fortschritt wird angezeigt)

# 4. Ergebnisse anschauen
open output/experiments/report/experiment_report.md
```

**Was passiert während der Ausführung:**

```
[12:00:00] ══════════════════════════════════════════════════════════════
[12:00:00] EXPERIMENT 1/5: CPU-Skalierung
[12:00:00] ══════════════════════════════════════════════════════════════
[12:00:01] Config: 1 Core, 4GB RAM, 50% Daten
[12:00:01]   Durchlauf 1/3...
[12:00:45]     ✓ Daten laden: 8.2s (CPU: 45%, RAM: 512MB)
[12:01:12]     ✓ Outputs extrahieren: 12.1s (CPU: 78%, RAM: 1.2GB)
[12:01:45]     ✓ UTXO berechnen: 33.4s (CPU: 92%, RAM: 2.1GB)
           ... (alle 11 Schritte)
[12:05:30]   Durchlauf 1/3 komplett: 329.5s
[12:05:31]   Durchlauf 2/3...
           ...
[12:15:00] ✓ CPU-Skalierung komplett. Ergebnisse: output/experiments/results/cpu_scaling.json

[12:15:01] ══════════════════════════════════════════════════════════════
[12:15:01] EXPERIMENT 2/5: RAM-Skalierung
[12:15:01] ══════════════════════════════════════════════════════════════
           ...

[13:45:00] ══════════════════════════════════════════════════════════════
[13:45:00] ALLE EXPERIMENTE ABGESCHLOSSEN
[13:45:00] ══════════════════════════════════════════════════════════════
[13:45:01] Generiere Visualisierungen...
[13:45:15] Generiere Tabellen...
[13:45:18] Generiere Report...
[13:45:20] ✓ Fertig!
```

### Abschnitt 25: Experiment-Ergebnisse im Notebook

**WICHTIG: Alle Ergebnisse werden direkt im Notebook angezeigt!**

Das Notebook enthält dedizierte Output-Sektionen, die nach Ausführung der Experimente automatisch befüllt werden:

#### 25.1 Referenzsystem-Info (Markdown-Zelle + Code-Zelle)

```python
# Code-Zelle: Zeigt System-Info
display_system_info()
```

**Output (wird im Notebook angezeigt):**
```
╔══════════════════════════════════════════════════════════════════╗
║                      REFERENZSYSTEM                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Hostname:        Romans-MacBook-Pro                             ║
║  OS:              Darwin 23.1.0 (macOS Sonoma)                   ║
║  CPU:             Apple M1 Pro                                   ║
║  Cores:           8 (physisch) / 8 (logisch)                     ║
║  RAM:             16.0 GB                                        ║
║  Python:          3.11.5                                         ║
║  Spark:           3.5.0                                          ║
║  Experiment-Datum: 2024-01-15 14:32:00                           ║
╚══════════════════════════════════════════════════════════════════╝
```

#### 25.2 CPU-Skalierung Ergebnisse

```python
# Code-Zelle: Zeigt CPU-Ergebnisse als Tabelle + Plot
display_cpu_scaling_results(cpu_results)
```

**Output (Tabelle + eingebetteter Plot im Notebook):**
- Tabelle mit Cores, Laufzeit, Speedup, Effizienz
- Plot wird inline angezeigt (nicht nur gespeichert)

#### 25.3 RAM-Skalierung Ergebnisse

```python
# Code-Zelle: Zeigt RAM-Ergebnisse
display_ram_scaling_results(ram_results)
```

#### 25.4 Daten-Skalierung Ergebnisse

```python
# Code-Zelle: Zeigt Daten-Ergebnisse
display_data_scaling_results(data_results)
```

#### 25.5 Kombinierte Heatmaps

```python
# Code-Zelle: Zeigt 2D-Heatmaps
display_combined_heatmaps(combined_results)
```

**Output:** CPU×Daten und RAM×Daten Heatmaps inline im Notebook

#### 25.6 Bottleneck-Analyse

```python
# Code-Zelle: Zeigt Bottleneck-Tabelle und Heatmap
display_bottleneck_analysis(bottleneck_results)
```

**Output:**
```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         BOTTLENECK-ANALYSE                                       ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  Pipeline-Schritt          │ Dauer  │ CPU  │ RAM    │ Disk  │ Bottleneck        ║
║  ─────────────────────────────────────────────────────────────────────────────  ║
║  1. Daten laden            │  8.2s  │ 25%  │ 512MB  │ 1.2GB │ I/O-bound         ║
║  2. UTXO berechnen         │ 33.4s  │ 92%  │ 2.1GB  │ 100MB │ CPU-bound         ║
║  ... (alle 11 Schritte)                                                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

+ Heatmap inline

#### 25.7 Empfehlungen & Fazit

```python
# Code-Zelle: Zeigt finale Empfehlungen
display_recommendations(all_results)
```

**Output:**
```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                      SKALIERUNGSEMPFEHLUNGEN                                     ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  CPU-EMPFEHLUNG:                                                                 ║
║  → 4 Cores bieten 3.2x Speedup (80% Effizienz)                                  ║
║  → 8 Cores bieten nur 4.1x Speedup (51% Effizienz)                              ║
║  → Sweet-Spot: 4 Cores                                                          ║
║                                                                                  ║
║  RAM-EMPFEHLUNG:                                                                 ║
║  → Unter 2GB: 45% Disk-Spilling, 2.3x langsamer                                 ║
║  → Bei 4GB: Kein Spilling, optimale Performance                                 ║
║  → Sweet-Spot: 4GB RAM                                                          ║
║                                                                                  ║
║  SKALIERUNGSPROGNOSE (für 10x Daten):                                           ║
║  → Geschätzte Laufzeit: ~45 Minuten                                             ║
║  → Geschätzter RAM-Bedarf: ~12GB                                                ║
║  → Empfohlene Cores: 8+                                                         ║
║                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

### Display-Funktionen

```python
def display_system_info():
    """Zeigt Referenzsystem-Info formatiert im Notebook."""
    info = get_system_info()
    # Formatierte Ausgabe mit Box-Drawing Characters
    # Wird direkt im Notebook angezeigt

def display_cpu_scaling_results(results: dict):
    """Zeigt CPU-Ergebnisse: Tabelle + inline Plot."""
    # 1. Pandas DataFrame anzeigen
    display(results_df)
    # 2. Plot inline anzeigen (plt.show())
    plot_cpu_scaling(results)
    plt.show()

def display_ram_scaling_results(results: dict):
    """Analog für RAM."""

def display_data_scaling_results(results: dict):
    """Analog für Daten."""

def display_combined_heatmaps(results: dict):
    """Zeigt beide Heatmaps inline."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    plot_cpu_data_heatmap(results, ax=axes[0])
    plot_ram_data_heatmap(results, ax=axes[1])
    plt.tight_layout()
    plt.show()

def display_bottleneck_analysis(results: dict):
    """Zeigt Bottleneck-Tabelle und Heatmap inline."""

def display_recommendations(results: dict):
    """Zeigt finale Empfehlungen formatiert."""
```

### Notebook-Struktur nach Ausführung

Nach dem Ausführen des Notebooks mit `EXPERIMENT_MODE=true` sieht die Struktur so aus:

```
Notebook-Inhalt:
├── Abschnitte 1-15: Bestehende Pipeline (mit Outputs)
├── Abschnitt 16: ResourceMonitor (Code)
├── Abschnitt 17: CPU-Skalierung (Code)
├── Abschnitt 18: RAM-Skalierung (Code)
├── Abschnitt 19: Daten-Skalierung (Code)
├── Abschnitt 20: Kombinierte Experimente (Code)
├── Abschnitt 21: Bottleneck-Analyse (Code)
├── Abschnitt 22: Visualisierungen (Code)
├── Abschnitt 23: Empfehlungen (Code)
├── Abschnitt 24: Automatische Ausführung (Code + läuft)
└── Abschnitt 25: ERGEBNISSE (mit Outputs!)
    ├── 25.1 Referenzsystem ← Tabelle sichtbar
    ├── 25.2 CPU-Ergebnisse ← Tabelle + Plot sichtbar
    ├── 25.3 RAM-Ergebnisse ← Tabelle + Plot sichtbar
    ├── 25.4 Daten-Ergebnisse ← Tabelle + Plot sichtbar
    ├── 25.5 Heatmaps ← 2 Heatmaps sichtbar
    ├── 25.6 Bottleneck ← Tabelle + Heatmap sichtbar
    └── 25.7 Empfehlungen ← Text sichtbar
```

**Vorteil:** Man kann das Notebook öffnen und sieht sofort alle Ergebnisse - ohne in Ordner schauen zu müssen!

---

## Workflow für Experimente

### Phase 1: Vorbereitung
```bash
# 1. Notebook öffnen
jupyter notebook bitcoin_whale_explained_experiment.ipynb

# 2. Basis-Pipeline ausführen (Abschnitte 1-15)
# Dies stellt sicher, dass alle Funktionen definiert sind
```

### Phase 2: CPU-Skalierung testen
```python
# Abschnitt 17 ausführen
# ACHTUNG: Startet Spark mehrfach neu (dauert länger)

cpu_exp = CPUScalingExperiment(spark, BLOCKCHAIN_DATA_PATH)
cpu_results = cpu_exp.run(core_counts=[1, 2, 4, 8], repetitions=3)
```

### Phase 3: RAM-Skalierung testen
```python
# Abschnitt 18 ausführen
# ACHTUNG: Startet Spark mehrfach neu

ram_exp = RAMScalingExperiment(spark, BLOCKCHAIN_DATA_PATH)
ram_results = ram_exp.run(ram_configs=["1g", "2g", "4g", "8g"], repetitions=3)
```

### Phase 4: Daten-Skalierung testen
```python
# Abschnitt 19 ausführen

data_exp = DataScalingExperiment(spark, BLOCKCHAIN_DATA_PATH)
data_results = data_exp.run(data_fractions=[0.1, 0.25, 0.5, 0.75, 1.0], repetitions=3)
```

### Phase 5: Analyse & Dokumentation
```python
# Abschnitte 20-23 ausführen
# Visualisierungen werden in notebooks/images/ gespeichert
# Empfehlungen werden als Text ausgegeben
```

---

## Erwartete Ergebnisse

### CPU-Skalierung: Beispiel-Output

```
╔══════════════════════════════════════════════════════════════════╗
║                    CPU-SKALIERUNGSEXPERIMENT                     ║
╠══════════════════════════════════════════════════════════════════╣
║ Cores │ Laufzeit (s)    │ Speedup │ Effizienz │ Status          ║
╠═══════╪═════════════════╪═════════╪═══════════╪═════════════════╣
║   1   │ 120.4 ± 2.1     │ 1.00x   │ 100%      │ Baseline        ║
║   2   │  65.2 ± 1.8     │ 1.85x   │  92%      │ ✓ Gut           ║
║   4   │  38.7 ± 1.2     │ 3.11x   │  78%      │ ✓ Akzeptabel    ║
║   8   │  28.9 ± 2.4     │ 4.16x   │  52%      │ ⚠ Diminishing   ║
╚═══════╧═════════════════╧═════════╧═══════════╧═════════════════╝

→ Erkenntnis: 4 Cores bieten das beste Preis-Leistungs-Verhältnis.
  Bei 8 Cores wird nur noch 52% jedes zusätzlichen Cores genutzt.
  Vermutlich I/O-Bottleneck beim Lesen der JSON-Dateien.
```

### RAM-Skalierung: Beispiel-Output

```
╔══════════════════════════════════════════════════════════════════╗
║                    RAM-SKALIERUNGSEXPERIMENT                     ║
╠══════════════════════════════════════════════════════════════════╣
║  RAM  │ Laufzeit (s)    │ Spill (MB) │ GC (%)  │ Status         ║
╠═══════╪═════════════════╪════════════╪═════════╪════════════════╣
║  1 GB │ 89.2 ± 5.3      │ 2,340      │ 18.2%   │ ⚠ Spilling     ║
║  2 GB │ 52.1 ± 2.1      │   890      │  8.4%   │ ⚠ Noch Spill   ║
║  4 GB │ 38.7 ± 1.2      │     0      │  3.1%   │ ✓ Optimal      ║
║  8 GB │ 37.9 ± 1.4      │     0      │  2.8%   │ = Kein Gewinn  ║
╚═══════╧═════════════════╧════════════╧═════════╧════════════════╝

→ Erkenntnis: 4 GB RAM ist der Sweet-Spot für dieses Dataset.
  Unter 4 GB: Massives Disk-Spilling, 2.3x langsamer.
  Über 4 GB: Keine messbare Verbesserung.
```

### Daten-Skalierung: Beispiel-Output

```
╔══════════════════════════════════════════════════════════════════╗
║                   DATEN-SKALIERUNGSEXPERIMENT                    ║
╠══════════════════════════════════════════════════════════════════╣
║ Daten │ Transaktionen   │ Laufzeit (s) │ RAM (MB) │ Komplexität ║
╠═══════╪═════════════════╪══════════════╪══════════╪═════════════╣
║  10%  │    123,456      │   4.2 ± 0.3  │    512   │             ║
║  25%  │    308,641      │  10.8 ± 0.5  │    923   │             ║
║  50%  │    617,283      │  22.1 ± 0.8  │  1,645   │   O(n)      ║
║  75%  │    925,925      │  34.2 ± 1.1  │  2,312   │             ║
║ 100%  │  1,234,567      │  45.3 ± 1.4  │  2,948   │             ║
╚═══════╧═════════════════╧══════════════╧══════════╧═════════════╝

→ Erkenntnis: Laufzeit skaliert linear O(n) mit der Datenmenge.
  RAM-Verbrauch skaliert ebenfalls linear.

  Prognose für 10x Daten (12.3M Transaktionen):
  - Geschätzte Laufzeit: ~7.5 Minuten
  - Geschätzter RAM-Bedarf: ~30 GB
  - Empfehlung: Cluster-Setup oder Sampling
```

---

## Visualisierungen

### 1D-Plots: Einzelne Ressource variiert

#### 1. CPU-Speedup-Kurve
![CPU Speedup](images/cpu_speedup.png)
- X-Achse: Anzahl Cores
- Y-Achse: Speedup (T₁/Tₙ)
- Linien: Gemessen vs. Ideal (linear)

#### 2. CPU-Effizienz-Kurve
![CPU Efficiency](images/cpu_efficiency.png)
- X-Achse: Anzahl Cores
- Y-Achse: Effizienz (Speedup/Cores) in %
- Zeigt ab wann zusätzliche Cores "verschwendet" werden

#### 3. RAM-Impact-Kurve
![RAM Impact](images/ram_impact.png)
- X-Achse: RAM-Größe
- Y-Achse links: Laufzeit
- Y-Achse rechts: Disk-Spilling (MB)

#### 4. Daten-Skalierungskurve
![Data Scaling](images/data_scaling.png)
- X-Achse: Datenmenge (%)
- Y-Achse: Laufzeit
- Mit Regressionslinie und R²-Wert

### 2D-Plots: Kombinierte Analyse (NEU!)

#### 5. CPU × Datenmenge Heatmap
![CPU Data Heatmap](images/cpu_data_heatmap.png)
- X-Achse: Datenmenge (25%, 50%, 100%)
- Y-Achse: CPU-Cores (2, 4, 8)
- Farbe: Laufzeit in Sekunden
- Zeigt: Wie skaliert CPU-Nutzen mit Datenmenge?

```
Beispiel:
              25%      50%      100%
    2 Cores   15s      32s      68s
    4 Cores    9s      18s      38s
    8 Cores    6s      13s      28s
```

#### 6. RAM × Datenmenge Heatmap
![RAM Data Heatmap](images/ram_data_heatmap.png)
- X-Achse: Datenmenge (25%, 50%, 100%)
- Y-Achse: RAM (2GB, 4GB, 8GB)
- Farbe: Laufzeit in Sekunden
- Zeigt: Braucht man bei mehr Daten proportional mehr RAM?

#### 7. Skalierungslinien (Multi-Kurven-Plot)
![Scaling Lines](images/scaling_lines.png)
- X-Achse: Datenmenge (%)
- Y-Achse: Laufzeit
- Mehrere Linien: Eine pro Core-Anzahl
- Parallele Linien = gute Skalierung
- Divergierende Linien = Bottleneck bei großen Daten

### Bottleneck-Analyse

#### 8. Bottleneck-Heatmap
![Bottleneck Heatmap](images/bottleneck_heatmap.png)
- Zeilen: Pipeline-Schritte
- Spalten: CPU, RAM, Disk
- Farbe: Relative Auslastung (0-100%)

---

## Troubleshooting

### Spark-Session lässt sich nicht neu starten
```python
# Alte Session explizit beenden
spark.stop()
import time
time.sleep(2)  # Warten bis Ressourcen freigegeben
# Dann neue Session starten
```

### Out of Memory bei RAM-Experimenten
- Starte mit kleinerer Datenmenge (50%)
- Teste nur RAM-Konfigurationen die Sinn machen (nicht 1GB bei großem Dataset)

### Unzuverlässige Messungen
- Schließe andere Anwendungen
- Führe mehr Wiederholungen durch (repetitions=5)
- Ignoriere den ersten Durchlauf (Warmup-Effekt)

### Plots werden nicht gespeichert
```bash
mkdir -p notebooks/images
```

---

## Zusammenfassung

### Konfiguration via `.env` Datei

Alle Experiment-Parameter in **einer Datei** (`notebooks/.env.experiment`):

```bash
# .env.experiment
EXPERIMENT_MODE=true              # ← Flag zum Aktivieren
EXPERIMENT_CPU_CONFIGS=2,4,8      # ← Welche Cores testen
EXPERIMENT_RAM_CONFIGS=2g,4g,8g   # ← Welche RAM-Größen testen
EXPERIMENT_DATA_FRACTIONS=0.5,1.0 # ← Welche Datenmengen testen
```

**Workflow:**
1. `EXPERIMENT_MODE=true` setzen
2. Notebook "Run All" ausführen
3. Warten
4. Ergebnisse in `output/experiments/` anschauen

### Referenzsystem-Dokumentation

Jeder Report enthält automatisch die **Hardware-Spezifikationen**:
- CPU-Modell und Cores
- RAM (gesamt)
- Betriebssystem
- Python/Spark Version
- Experiment-Datum

### Die 4 Skalierungsfragen

| Frage | Experiment | Visualisierung |
|-------|------------|----------------|
| Bringen 4 CPUs 2x so viel wie 2? | CPU-Skalierung | Speedup-Kurve |
| Hilft mehr RAM? | RAM-Skalierung | RAM-Impact-Kurve |
| Wie wächst der Bedarf? | Daten-Skalierung | Skalierungskurve mit Regression |
| **CPU × Datenmenge?** | Kombiniert (NEU!) | **2D-Heatmap** |

### Neue Notebook-Abschnitte (10 Stück)

| # | Abschnitt | Inhalt |
|---|-----------|--------|
| 16 | ResourceMonitor | Metriken-Framework (CPU, RAM, Disk) |
| 17 | CPU-Skalierung | 1, 2, 4, 8 Cores testen |
| 18 | RAM-Skalierung | 1, 2, 4, 8 GB testen |
| 19 | Daten-Skalierung | 10-100% Datenmenge testen |
| 20 | Kombiniert | CPU×Daten, RAM×Daten Heatmaps |
| 21 | Bottleneck-Analyse | CPU-bound vs. Memory-bound pro Schritt |
| 22 | Visualisierungen | Alle Plots generieren |
| 23 | Empfehlungen | Automatische Skalierungsempfehlungen |
| 24 | **Automatische Ausführung** | **Eine Zelle → Alles läuft** |
| 25 | Dokumentation | Ergebnisse festhalten |

### Automatisierung

**Eine Zelle ausführen → Alles läuft automatisch:**
- Alle 11 Pipeline-Schritte werden für jede Konfiguration gemessen
- Ergebnisse werden in `output/experiments/` gespeichert
- Plots, Tabellen und Report werden automatisch generiert

### Kernmetriken

- **CPU**: Speedup & Effizienz
- **RAM**: Spill-to-Disk & GC-Overhead
- **Daten**: Komplexitätsklasse O(n), O(n log n)
- **Kombiniert**: Heatmap-Werte, Skalierungsfaktor

### Outputs

- Konkrete Zahlen in Tabellen
- **8 Visualisierungen** (5 × 1D-Plots, 3 × 2D-Heatmaps)
- Automatische Empfehlungen für Produktivbetrieb
