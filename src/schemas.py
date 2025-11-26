"""
Blockchair TSV Schema Definitions for PySpark

This module contains schema definitions for the four main Blockchair Bitcoin dump files:
- blocks
- transactions
- inputs
- outputs

These schemas ensure correct data types are used when loading TSV files into Spark DataFrames,
particularly for:
- Large integers (Satoshi values, block IDs)
- Timestamps
- Boolean flags
- Nullable fields
"""

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    IntegerType,
    DoubleType,
    TimestampType,
    BooleanType,
)


# ==============================================================================
# BLOCKS SCHEMA (36 fields)
# ==============================================================================

BLOCKS_SCHEMA = StructType([
    StructField("id", LongType(), False),
    StructField("hash", StringType(), True),
    StructField("time", TimestampType(), True),
    StructField("median_time", TimestampType(), True),
    StructField("size", LongType(), True),
    StructField("stripped_size", LongType(), True),
    StructField("weight", LongType(), True),
    StructField("version", LongType(), True),
    StructField("version_hex", StringType(), True),
    StructField("version_bits", StringType(), True),
    StructField("merkle_root", StringType(), True),
    StructField("nonce", LongType(), True),
    StructField("bits", LongType(), True),
    StructField("difficulty", LongType(), True),
    StructField("chainwork", StringType(), True),
    StructField("coinbase_data_hex", StringType(), True),
    StructField("transaction_count", IntegerType(), True),
    StructField("witness_count", IntegerType(), True),
    StructField("input_count", IntegerType(), True),
    StructField("output_count", IntegerType(), True),
    StructField("input_total", LongType(), True),
    StructField("input_total_usd", DoubleType(), True),
    StructField("output_total", LongType(), True),
    StructField("output_total_usd", DoubleType(), True),
    StructField("fee_total", LongType(), True),
    StructField("fee_total_usd", DoubleType(), True),
    StructField("fee_per_kb", DoubleType(), True),
    StructField("fee_per_kb_usd", DoubleType(), True),
    StructField("fee_per_kwu", DoubleType(), True),
    StructField("fee_per_kwu_usd", DoubleType(), True),
    StructField("cdd_total", DoubleType(), True),
    StructField("generation", LongType(), True),
    StructField("generation_usd", DoubleType(), True),
    StructField("reward", LongType(), True),
    StructField("reward_usd", DoubleType(), True),
    StructField("guessed_miner", StringType(), True),
])


# ==============================================================================
# TRANSACTIONS SCHEMA (22 fields)
# ==============================================================================

TRANSACTIONS_SCHEMA = StructType([
    StructField("block_id", LongType(), False),
    StructField("hash", StringType(), False),
    StructField("time", TimestampType(), True),
    StructField("size", IntegerType(), True),
    StructField("weight", IntegerType(), True),
    StructField("version", IntegerType(), True),
    StructField("lock_time", LongType(), True),
    StructField("is_coinbase", BooleanType(), True),
    StructField("has_witness", BooleanType(), True),
    StructField("input_count", IntegerType(), True),
    StructField("output_count", IntegerType(), True),
    StructField("input_total", LongType(), True),
    StructField("input_total_usd", DoubleType(), True),
    StructField("output_total", LongType(), True),
    StructField("output_total_usd", DoubleType(), True),
    StructField("fee", LongType(), True),
    StructField("fee_usd", DoubleType(), True),
    StructField("fee_per_kb", DoubleType(), True),
    StructField("fee_per_kb_usd", DoubleType(), True),
    StructField("fee_per_kwu", DoubleType(), True),
    StructField("fee_per_kwu_usd", DoubleType(), True),
    StructField("cdd_total", DoubleType(), True),
])


# ==============================================================================
# INPUTS SCHEMA (21 fields)
# ==============================================================================

INPUTS_SCHEMA = StructType([
    StructField("block_id", LongType(), False),
    StructField("transaction_hash", StringType(), False),
    StructField("index", IntegerType(), False),
    StructField("time", TimestampType(), True),
    StructField("value", LongType(), True),
    StructField("value_usd", DoubleType(), True),
    StructField("recipient", StringType(), True),
    StructField("type", StringType(), True),
    StructField("script_hex", StringType(), True),
    StructField("is_from_coinbase", BooleanType(), True),
    StructField("is_spendable", BooleanType(), True),
    # Spending information (nullable - only present if output has been spent)
    StructField("spending_block_id", LongType(), True),
    StructField("spending_transaction_hash", StringType(), True),
    StructField("spending_index", IntegerType(), True),
    StructField("spending_time", TimestampType(), True),
    StructField("spending_value_usd", DoubleType(), True),
    StructField("spending_sequence", LongType(), True),
    StructField("spending_signature_hex", StringType(), True),
    StructField("spending_witness", StringType(), True),
    StructField("lifespan", LongType(), True),
    StructField("cdd", DoubleType(), True),
])


# ==============================================================================
# OUTPUTS SCHEMA (11 fields)
# ==============================================================================

OUTPUTS_SCHEMA = StructType([
    StructField("block_id", LongType(), False),
    StructField("transaction_hash", StringType(), False),
    StructField("index", IntegerType(), False),
    StructField("time", TimestampType(), True),
    StructField("value", LongType(), True),
    StructField("value_usd", DoubleType(), True),
    StructField("recipient", StringType(), True),
    StructField("type", StringType(), True),
    StructField("script_hex", StringType(), True),
    StructField("is_from_coinbase", BooleanType(), True),
    StructField("is_spendable", BooleanType(), True),
])


# ==============================================================================
# HELPER FUNCTION
# ==============================================================================

def load_blockchair_data(spark, data_path):
    """
    Load all four Blockchair TSV datasets into Spark DataFrames.

    Args:
        spark: SparkSession instance
        data_path: Base path to the Blockchair data directory
                   The function expects this structure (as created by blockchair-downloader):
                   data_path/
                   ├── extracted/
                   │   ├── blocks/*.tsv
                   │   ├── transactions/*.tsv
                   │   ├── inputs/*.tsv
                   │   └── outputs/*.tsv
                   └── raw/  (optional, .gz files)

    Returns:
        dict: Dictionary with keys 'blocks', 'transactions', 'inputs', 'outputs'
              containing the respective DataFrames

    Example:
        >>> spark = SparkSession.builder.appName("Bitcoin Analysis").getOrCreate()
        >>> data = load_blockchair_data(spark, '/Users/professor/blockchair-data')
        >>> blocks_df = data['blocks']
        >>> transactions_df = data['transactions']
    """
    # Automatically append /extracted if not already present
    from pathlib import Path
    base_path = Path(data_path)
    if base_path.name != 'extracted' and (base_path / 'extracted').exists():
        extracted_path = base_path / 'extracted'
    else:
        extracted_path = base_path

    return {
        'blocks': spark.read.csv(
            f"{extracted_path}/blocks/*.tsv",
            sep='\t',
            header=True,
            schema=BLOCKS_SCHEMA
        ),
        'transactions': spark.read.csv(
            f"{extracted_path}/transactions/*.tsv",
            sep='\t',
            header=True,
            schema=TRANSACTIONS_SCHEMA
        ),
        'inputs': spark.read.csv(
            f"{extracted_path}/inputs/*.tsv",
            sep='\t',
            header=True,
            schema=INPUTS_SCHEMA
        ),
        'outputs': spark.read.csv(
            f"{extracted_path}/outputs/*.tsv",
            sep='\t',
            header=True,
            schema=OUTPUTS_SCHEMA
        )
    }
