# Bitcoin Blockchain Export via BigQuery

Exportiert Bitcoin-Daten von Google BigQuery Public Datasets im bitcoin-etl Format.

## Voraussetzungen

```bash
# Google Cloud CLI installieren (einmalig)
brew install google-cloud-sdk

# Authentifizieren (einmalig)
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project btc-data-483415
```

## Export starten

```bash
cd /Users/roman/spark_project/bitcoin-whale-intelligence
source .venv/bin/activate

python src/export_btc_bigquery.py \
  --start-date 2024-01-15 \
  --end-date 2024-02-04 \
  --tables blocks transactions \
  --output-dir /Users/roman/spark_project/blockchain_exports
```

## Parameter

| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `--start-date` | Startdatum (YYYY-MM-DD) | `2024-01-15` |
| `--end-date` | Enddatum (YYYY-MM-DD) | `2024-02-04` |
| `--tables` | Tabellen (blocks, transactions) | `blocks transactions` |
| `--output-dir` | Zielverzeichnis | `/path/to/blockchain_exports` |
| `--project` | GCP Projekt-ID | `btc-data-483415` |

## Ausgabe-Struktur

```
blockchain_exports/
└── 2024-01-15_2024-02-04/
    ├── blocks/
    │   └── date=YYYY-MM-DD/
    │       └── blocks_00000.json
    └── transactions/
        └── date=YYYY-MM-DD/
            └── transactions_00000.json
```

## Richtwerte

| Zeitraum | Größe | Dauer | Quota-Verbrauch |
|----------|-------|-------|-----------------|
| 1 Tag | ~800 MB | ~15 Min | ~0.6 GB |
| 1 Woche | ~5.5 GB | ~2 Std | ~4 GB |
| 3 Wochen | ~17 GB | ~5 Std | ~13 GB |

**BigQuery Sandbox Limit:** 1 TB/Monat (kostenlos)

## Abbrechen & Fortsetzen

- `Ctrl+C` bricht den Export ab
- Bereits exportierte Tage bleiben erhalten
- Bei erneutem Start werden alle Tage neu exportiert
