<div align="center">
  <h1>Bitcoin Whale Intelligence</h1>
  <h3>Big Data Pipeline for Identifying Bitcoin Whale Entities</h3>
  <p>
    <img src="https://img.shields.io/badge/python-3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/spark-4.1-orange" alt="Spark">
    <img src="https://img.shields.io/badge/graphframes-0.10-red" alt="GraphFrames">
    <img src="https://img.shields.io/badge/notebook-Jupyter-yellow" alt="Jupyter">
  </p>
</div>

**Bitcoin Whale Intelligence** is an Apache Spark pipeline that de-anonymizes the Bitcoin blockchain to identify whale entities. One owner can control thousands of addresses — this project clusters them using graph analysis, filters out CoinJoin noise, and profiles entities holding 100+ BTC.

> **Core insight**: Apply the Common Input Ownership Heuristic, build an address graph, run Connected Components, aggregate UTXO balances — whale entities emerge.

## Pipeline

```
Blockchain Data → Explode Tx → UTXO Set → Filter CoinJoins → Build Graph → Connected Components → Balances → Whale Detection
```

| Step | What it does |
|---|---|
| Load & Explode | Parse Hive-partitioned JSON, flatten nested inputs/outputs |
| UTXO Set | LEFT ANTI JOIN to find all unspent outputs (current balances) |
| CoinJoin Filter | Detect & exclude Whirlpool, Wasabi, and generic CoinJoins |
| Address Graph | Build edges from co-occurring addresses in multi-input transactions |
| Connected Components | GraphFrames clustering — addresses sharing inputs = same entity |
| Whale Detection | Categorize entities by BTC holdings |

## Whale Categories

| Category | Threshold |
|---|---|
| Mega Whale | ≥ 1,000 BTC |
| Whale | 100 – 1,000 BTC |
| Large | 10 – 100 BTC |
| Medium | 1 – 10 BTC |
| Small | < 1 BTC |

## Key Features

- **CoinJoin Detection** — Identifies and filters Whirlpool (5 inputs/outputs at pool denominations), Wasabi (≥10 equal outputs), and generic CoinJoins to prevent false clustering.
- **Time-Series Analysis** — Tracks whale balance trajectories over time. Visualizes accumulation patterns and wealth concentration trends.
- **Performance Experiments** — Built-in scaling experiments across CPU cores, RAM, and data size with automated bottleneck classification.
- **Two Data Sources** — Blockchair free dumps or Google BigQuery public dataset. Both produce the same bitcoin-etl JSON format.
- **Explained Notebook** — 78 cells with ASCII diagrams explaining every algorithm step. Educational and production-grade.

## Performance

Benchmarked on Apple M4 / M4 Pro:

| Dataset | Size | Transactions | Runtime |
|---|---|---|---|
| Small | ~1 GB | ~1M | ~5 min |
| Medium | ~6 GB | ~3.4M | ~15 min |
| Large | ~20 GB | ~10M | ~hours |

> **Bottleneck**: GraphFrames Connected Components accounts for ~88% of total pipeline runtime. The docs discuss why a native graph DB (Neo4j, TigerGraph) would outperform Spark for this specific step.

## Quick Start

> **Prerequisites**: Python 3.11, Java 17 or 21, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
uv venv --python 3.11
source .venv/bin/activate
uv sync
```

### Get Data

**Option A — Blockchair (free, no account):**
```bash
python src/download_btc_blockchair.py --start-date 2024-01-15 --end-date 2024-02-04
```

**Option B — Google BigQuery (free tier, 1 TB/month):**
```bash
gcloud auth application-default login
python src/export_btc_bigquery.py \
  --start-date 2024-01-15 --end-date 2024-02-04 \
  --output-dir ./blockchain_exports
```

### Run

```bash
cd notebooks
cp .env.experiment .env    # edit paths and Spark config
jupyter notebook bitcoin_whale_explained_experiment.ipynb
```

Or use the startup script:
```bash
./start_project.sh
```

### Key Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `BLOCKCHAIN_DATA_PATH` | `../blockchain_exports` | Path to JSON data |
| `OUTPUT_PATH` | `../output` | Parquet + charts output |
| `SPARK_DRIVER_MEMORY` | `8g` | Adjust to available RAM |
| `SPARK_NUM_CORES` | `8` | Number of Spark cores |
| `EXPERIMENT_MODE` | `false` | Enable scaling experiments |

## Tech Stack

| Component | Technology |
|---|---|
| Processing | PySpark 4.1 |
| Graph Analysis | GraphFrames (Connected Components) |
| Storage | Parquet via PyArrow |
| Visualization | Matplotlib + Seaborn |
| Notebook | Jupyter |
| Monitoring | psutil (CPU/RAM sampling) |
| Package Manager | uv |

## Project Structure

```
├── notebooks/
│   ├── bitcoin_whale_explained_experiment.ipynb           # Main notebook (clean)
│   ├── ..._with_outputs_6gb.ipynb                         # Pre-run with 6 GB results
│   └── ..._with_outputs_20gb.ipynb                        # Pre-run with 20 GB results
├── src/
│   ├── etl.py                      # Core PySpark ETL library
│   ├── download_btc_blockchair.py  # Blockchair data downloader
│   └── export_btc_bigquery.py      # BigQuery data exporter
├── docs/
│   ├── setup.md                    # Full setup guide
│   ├── INTERPRETATION.md           # Experiment result analysis
│   └── *_run_interpretation/       # Charts (PNG) for 6 GB and 20 GB runs
└── blockchain_exports/             # Data directory (user-populated)
```

## Experiment Framework

Six automated experiments with visualization:

1. **CPU Scaling** — 1/2/4/8 cores, speedup analysis
2. **RAM Scaling** — 8g/12g/16g/20g, sweet spot detection
3. **Data Scaling** — 25%/50%/75%/100%, complexity curve
4. **CPU x Data Matrix** — 2D heatmap
5. **RAM x Data Matrix** — 2D heatmap
6. **Bottleneck Analysis** — Auto-classifies each step as CPU/Memory/I/O-bound

See [docs/INTERPRETATION.md](docs/INTERPRETATION.md) for detailed results.
