# -*- coding: utf-8 -*-
"""
Bitcoin-ETL Data Processing Module

Dieses Modul enthält alle Funktionen zum Laden und Verarbeiten von Bitcoin-Daten,
die mit bitcoin-etl (https://github.com/blockchain-etl/bitcoin-etl) exportiert wurden.

Hauptfunktionen:
- create_spark_session(): Optimierte Spark-Session für Bitcoin-Analyse
- load_transactions(): Lädt bitcoin-etl JSON Transaktionsdaten
- load_blocks(): Lädt bitcoin-etl JSON Blockdaten
- explode_outputs(): Transformiert nested outputs zu flacher Tabelle
- explode_inputs(): Transformiert nested inputs zu flacher Tabelle
- compute_utxo_set(): Berechnet unspent transaction outputs
- enrich_clustering_inputs(): Reichert Multi-Input-TXs mit Adressen an
"""

from pathlib import Path
from typing import Optional, Tuple

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, explode, explode_outer, size, when, coalesce,
    from_unixtime, to_timestamp, lit, array, element_at,
    monotonically_increasing_id
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, IntegerType,
    BooleanType, ArrayType
)


# ==============================================================================
# SCHEMAS FÜR BITCOIN-ETL JSON
# ==============================================================================

INPUT_SCHEMA = StructType([
    StructField("index", IntegerType(), True),
    StructField("spent_transaction_hash", StringType(), True),
    StructField("spent_output_index", IntegerType(), True),
    StructField("script_asm", StringType(), True),
    StructField("script_hex", StringType(), True),
    StructField("sequence", LongType(), True),
    StructField("required_signatures", IntegerType(), True),
    StructField("type", StringType(), True),
    StructField("addresses", ArrayType(StringType()), True),
    StructField("value", LongType(), True),
])

OUTPUT_SCHEMA = StructType([
    StructField("index", IntegerType(), True),
    StructField("script_asm", StringType(), True),
    StructField("script_hex", StringType(), True),
    StructField("required_signatures", IntegerType(), True),
    StructField("type", StringType(), True),
    StructField("addresses", ArrayType(StringType()), True),
    StructField("value", LongType(), True),
])

TRANSACTION_SCHEMA = StructType([
    StructField("hash", StringType(), False),
    StructField("size", IntegerType(), True),
    StructField("virtual_size", IntegerType(), True),
    StructField("version", IntegerType(), True),
    StructField("lock_time", LongType(), True),
    StructField("block_number", LongType(), True),
    StructField("block_hash", StringType(), True),
    StructField("block_timestamp", LongType(), True),
    StructField("is_coinbase", BooleanType(), True),
    StructField("index", IntegerType(), True),
    StructField("inputs", ArrayType(INPUT_SCHEMA), True),
    StructField("outputs", ArrayType(OUTPUT_SCHEMA), True),
    StructField("input_count", IntegerType(), True),
    StructField("output_count", IntegerType(), True),
    StructField("input_value", LongType(), True),
    StructField("output_value", LongType(), True),
    StructField("fee", LongType(), True),
])

BLOCK_SCHEMA = StructType([
    StructField("hash", StringType(), False),
    StructField("size", IntegerType(), True),
    StructField("stripped_size", IntegerType(), True),
    StructField("weight", IntegerType(), True),
    StructField("number", LongType(), True),
    StructField("version", IntegerType(), True),
    StructField("merkle_root", StringType(), True),
    StructField("timestamp", LongType(), True),
    StructField("nonce", StringType(), True),
    StructField("bits", StringType(), True),
    StructField("coinbase_param", StringType(), True),
    StructField("transaction_count", IntegerType(), True),
])


# ==============================================================================
# SPARK SESSION
# ==============================================================================

def create_spark_session(
    app_name: str = "Bitcoin Whale Intelligence",
    driver_memory: str = "8g",
    enable_graphframes: bool = True
) -> SparkSession:
    """
    Erstellt eine optimierte Spark-Session für Bitcoin-Datenverarbeitung.

    Args:
        app_name: Name der Spark-Applikation
        driver_memory: Speicher für den Driver (z.B. "8g", "16g")
        enable_graphframes: GraphFrames-Pakete laden (für Connected Components)

    Returns:
        Konfigurierte SparkSession

    Optimierungen:
        - Adaptive Query Execution für bessere Join-Performance
        - Skew Join Handling für ungleiche Datenverteilung
        - Erhöhte Shuffle-Partitionen für große Datenmengen
    """
    # Ivy-Logging unterdrücken (vor Spark-Start)
    import os
    os.environ["SPARK_SUBMIT_ARGS"] = "--conf spark.driver.extraJavaOptions=-Divy.message.logger.level=4 pyspark-shell"

    builder = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.driver.memory", driver_memory) \
        .config("spark.driver.maxResultSize", "4g") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.sql.debug.maxToStringFields", "100") \
        .config("spark.ui.showConsoleProgress", "false") \
        .config("spark.memory.fraction", "0.8") \
        .config("spark.memory.storageFraction", "0.3") \
        .config("spark.driver.extraJavaOptions", "-Divy.message.logger.level=4") \
        .config("spark.executor.extraJavaOptions", "-Divy.message.logger.level=4")

    if enable_graphframes:
        builder = builder.config(
            "spark.jars.packages",
            "graphframes:graphframes:0.8.3-spark3.5-s_2.12"
        )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    return spark


# ==============================================================================
# DATEN LADEN
# ==============================================================================

def load_transactions(
    spark: SparkSession,
    base_path: str,
    use_schema: bool = True
) -> DataFrame:
    """
    Lädt bitcoin-etl Transaktionsdaten aus Hive-partitionierten JSON-Dateien.

    Args:
        spark: SparkSession
        base_path: Pfad zum blockchain_exports Verzeichnis
        use_schema: Schema explizit angeben (schneller) oder inferieren

    Returns:
        DataFrame mit Transaktionen (nested inputs/outputs)

    Erwartete Verzeichnisstruktur:
        base_path/
        └── <batch_folder>/
            └── transactions/
                └── date=YYYY-MM-DD/
                    └── transactions_*.json
    """
    base = Path(base_path)

    # Finde alle Batch-Ordner
    batch_folders = [d for d in base.iterdir()
                     if d.is_dir() and not d.name.startswith('.')]

    if not batch_folders:
        raise ValueError(f"Keine Batch-Ordner gefunden in {base_path}")

    # Sammle alle Transaction-Pfade
    tx_paths = []
    for batch in batch_folders:
        tx_path = batch / "transactions"
        if tx_path.exists():
            tx_paths.append(str(tx_path))

    if not tx_paths:
        raise ValueError(f"Keine transactions/ Ordner gefunden")

    # JSON laden (Spark erkennt Hive-Partitionen automatisch)
    if use_schema:
        df = spark.read.schema(TRANSACTION_SCHEMA).json(tx_paths)
    else:
        df = spark.read.json(tx_paths)

    # Timestamp konvertieren
    df = df.withColumn(
        "block_datetime",
        to_timestamp(from_unixtime(col("block_timestamp")))
    )

    return df


def load_blocks(
    spark: SparkSession,
    base_path: str,
    use_schema: bool = True
) -> DataFrame:
    """
    Lädt bitcoin-etl Blockdaten aus Hive-partitionierten JSON-Dateien.

    Args:
        spark: SparkSession
        base_path: Pfad zum blockchain_exports Verzeichnis
        use_schema: Schema explizit angeben oder inferieren

    Returns:
        DataFrame mit Blocks
    """
    base = Path(base_path)
    batch_folders = [d for d in base.iterdir()
                     if d.is_dir() and not d.name.startswith('.')]

    block_paths = []
    for batch in batch_folders:
        block_path = batch / "blocks"
        if block_path.exists():
            block_paths.append(str(block_path))

    if not block_paths:
        raise ValueError(f"Keine blocks/ Ordner gefunden")

    if use_schema:
        df = spark.read.schema(BLOCK_SCHEMA).json(block_paths)
    else:
        df = spark.read.json(block_paths)

    df = df.withColumn(
        "timestamp_dt",
        to_timestamp(from_unixtime(col("timestamp")))
    )

    return df


# ==============================================================================
# DATEN TRANSFORMIEREN (EXPLODE)
# ==============================================================================

def explode_outputs(tx_df: DataFrame) -> DataFrame:
    """
    Transformiert nested outputs zu einer flachen Tabelle.

    Aus:
        tx_hash | outputs: [{index:0, value:100, addresses:[...]}, ...]

    Wird:
        tx_hash | output_index | value | address

    Args:
        tx_df: Transaction DataFrame mit nested outputs

    Returns:
        Flache Output-Tabelle (eine Zeile pro Output)
    """
    return tx_df \
        .select(
            col("hash").alias("tx_hash"),
            col("block_number"),
            col("block_timestamp"),
            explode_outer("outputs").alias("output")
        ) \
        .select(
            "tx_hash",
            "block_number",
            "block_timestamp",
            col("output.index").alias("output_index"),
            col("output.value").alias("value"),
            col("output.addresses").alias("addresses"),
            col("output.type").alias("output_type"),
        )


def explode_inputs(tx_df: DataFrame) -> DataFrame:
    """
    Transformiert nested inputs zu einer flachen Tabelle.

    Args:
        tx_df: Transaction DataFrame mit nested inputs

    Returns:
        Flache Input-Tabelle mit Referenz zur Quell-UTXO
    """
    return tx_df \
        .select(
            col("hash").alias("tx_hash"),
            col("block_number"),
            col("block_timestamp"),
            col("is_coinbase"),
            explode_outer("inputs").alias("input")
        ) \
        .select(
            "tx_hash",
            "block_number",
            "block_timestamp",
            "is_coinbase",
            col("input.index").alias("input_index"),
            col("input.spent_transaction_hash").alias("spent_tx_hash"),
            col("input.spent_output_index").alias("spent_output_index"),
            col("input.addresses").alias("addresses"),
            col("input.value").alias("value"),
        )


# ==============================================================================
# UTXO SET BERECHNUNG
# ==============================================================================

def compute_utxo_set(
    outputs_df: DataFrame,
    inputs_df: DataFrame
) -> DataFrame:
    """
    Berechnet das UTXO Set (Unspent Transaction Outputs).

    Ein Output ist ein UTXO wenn er noch nicht als Input verwendet wurde.

    Berechnung:
        UTXO = Outputs LEFT ANTI JOIN Inputs
        (alle Outputs die NICHT in den Inputs referenziert werden)

    Args:
        outputs_df: Explodierte Outputs (von explode_outputs)
        inputs_df: Explodierte Inputs (von explode_inputs)

    Returns:
        DataFrame mit allen UTXOs (unspent outputs)

    Wichtig:
        Dies funktioniert nur korrekt wenn ALLE Transaktionen geladen sind.
        Bei Teil-Exporten fehlen möglicherweise die spending-Referenzen.
    """
    # Spent-Referenzen extrahieren (welche Outputs wurden ausgegeben?)
    spent_refs = inputs_df \
        .filter(col("is_coinbase") == False) \
        .select(
            col("spent_tx_hash").alias("ref_tx_hash"),
            col("spent_output_index").alias("ref_output_index")
        ) \
        .distinct()

    # LEFT ANTI JOIN: Outputs die NICHT in spent_refs sind
    utxos = outputs_df.join(
        spent_refs,
        on=[
            outputs_df.tx_hash == spent_refs.ref_tx_hash,
            outputs_df.output_index == spent_refs.ref_output_index
        ],
        how="left_anti"
    )

    return utxos


# ==============================================================================
# ENRICHMENT FÜR ENTITY CLUSTERING
# ==============================================================================

def enrich_clustering_inputs(
    tx_df: DataFrame,
    outputs_df: DataFrame,
    min_inputs: int = 2,
    max_inputs: int = 50
) -> DataFrame:
    """
    Reichert Inputs von Multi-Input-Transaktionen mit Adressen an.

    Für Entity Clustering brauchen wir die Adressen aller Inputs einer
    Multi-Input-Transaktion. Diese Information ist in den Rohdaten oft
    nicht vorhanden und muss durch einen Join mit den Outputs der
    Quell-Transaktionen ergänzt werden.

    Args:
        tx_df: Transaction DataFrame (mit nested inputs)
        outputs_df: Explodierte Outputs (Lookup-Tabelle)
        min_inputs: Minimum Input-Count (Standard: 2 für Clustering)
        max_inputs: Maximum Input-Count (Standard: 50, höher = wahrscheinlich Exchange)

    Returns:
        DataFrame mit:
            - tx_hash: Transaction Hash
            - addresses: Liste aller Input-Adressen dieser Transaktion

    Filterung:
        - Nur Transaktionen mit min_inputs <= input_count <= max_inputs
        - Keine Coinbase-Transaktionen
        - Transaktionen mit >50 Inputs sind oft Exchanges (verfälschen Clustering)
    """
    # 1. Multi-Input Transaktionen filtern
    multi_input_txs = tx_df \
        .filter(
            (col("input_count") >= min_inputs) &
            (col("input_count") <= max_inputs) &
            (col("is_coinbase") == False)
        )

    # 2. Inputs explodieren
    inputs_exploded = multi_input_txs \
        .select(
            col("hash").alias("tx_hash"),
            explode("inputs").alias("input")
        ) \
        .select(
            "tx_hash",
            col("input.spent_transaction_hash").alias("spent_tx_hash"),
            col("input.spent_output_index").alias("spent_output_index"),
            col("input.addresses").alias("raw_addresses"),
        )

    # 3. Output-Lookup vorbereiten
    output_lookup = outputs_df \
        .select(
            col("tx_hash").alias("source_tx_hash"),
            col("output_index").alias("source_output_index"),
            col("addresses").alias("source_addresses"),
        )

    # 4. JOIN: Inputs mit ihren Quell-Outputs
    enriched = inputs_exploded.join(
        output_lookup,
        on=[
            inputs_exploded.spent_tx_hash == output_lookup.source_tx_hash,
            inputs_exploded.spent_output_index == output_lookup.source_output_index
        ],
        how="left"
    )

    # 5. Adresse auswählen (bevorzuge enriched, fallback auf raw)
    # Nehme erste Adresse aus dem Array (typisch: 1 Adresse pro Output)
    enriched = enriched.withColumn(
        "address",
        when(
            (col("source_addresses").isNotNull()) & (size(col("source_addresses")) > 0),
            element_at(col("source_addresses"), 1)
        ).otherwise(
            when(
                (col("raw_addresses").isNotNull()) & (size(col("raw_addresses")) > 0),
                element_at(col("raw_addresses"), 1)
            )
        )
    )

    # 6. Nur relevante Spalten, Nulls filtern
    result = enriched \
        .filter(col("address").isNotNull()) \
        .select("tx_hash", "address")

    return result


# ==============================================================================
# HILFSFUNKTIONEN
# ==============================================================================

def get_data_summary(tx_df: DataFrame, blocks_df: DataFrame) -> dict:
    """
    Erstellt eine Zusammenfassung der geladenen Daten.

    Args:
        tx_df: Transaction DataFrame
        blocks_df: Block DataFrame

    Returns:
        Dictionary mit Statistiken
    """
    tx_count = tx_df.count()
    block_count = blocks_df.count()

    # Block-Range
    block_stats = blocks_df.agg(
        {"number": "min", "number": "max"}
    ).collect()[0]

    # Multi-Input Stats
    multi_input_count = tx_df.filter(
        (col("input_count") >= 2) & (col("is_coinbase") == False)
    ).count()

    return {
        "total_transactions": tx_count,
        "total_blocks": block_count,
        "multi_input_transactions": multi_input_count,
        "multi_input_ratio": multi_input_count / tx_count if tx_count > 0 else 0,
    }
