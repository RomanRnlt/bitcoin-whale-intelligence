"""
Data Source Configuration
Central configuration for selecting data sources in notebooks.

Usage in notebook:
    from src.data_config import DataConfig, load_data

    # Select data source
    config = DataConfig(source="local")  # or "bigquery" or "demo"

    # Load data
    df = load_data(config, "2021-01-01", "2021-01-07")
"""

import os
from pathlib import Path
from typing import Literal, Optional
from pyspark.sql import SparkSession, DataFrame


class DataConfig:
    """Configuration for data sources."""

    def __init__(self,
                 source: Literal["local", "bigquery", "demo"] = "demo",
                 local_data_path: Optional[str] = None):
        """
        Initialize data configuration.

        Args:
            source: Data source to use
                - "local": Blockchair local data (downloaded via download_bitcoin_data.py)
                - "bigquery": Google BigQuery (requires credentials)
                - "demo": Small demo data (no setup needed)
            local_data_path: Path to extracted Blockchair data
                             (only needed if source="local")
        """
        self.source = source

        # Auto-detect local data path if not provided
        if source == "local" and local_data_path is None:
            self.local_data_path = self._auto_detect_local_path()
        else:
            self.local_data_path = local_data_path

        # Validate
        if source == "local" and not self.local_data_path:
            raise ValueError(
                "Local data path not found. Please either:\n"
                "1. Download data first: python scripts/download_bitcoin_data.py\n"
                "2. Specify path: DataConfig(source='local', local_data_path='/path/to/extracted')"
            )

    def _auto_detect_local_path(self) -> Optional[str]:
        """Try to auto-detect local data path."""
        possible_paths = [
            # Common macOS locations
            "/Volumes/MySSD/bitcoin_data/extracted",
            "/Volumes/ExternalSSD/bitcoin_data/extracted",
            Path.home() / "bitcoin_data" / "extracted",

            # Common Windows locations
            "D:/bitcoin_data/extracted",
            "E:/bitcoin_data/extracted",

            # Common Linux locations
            "/mnt/ssd/bitcoin_data/extracted",
            "/data/bitcoin_data/extracted",
        ]

        for path in possible_paths:
            p = Path(path)
            if p.exists() and (p / "transactions").exists():
                print(f"✓ Auto-detected local data: {p}")
                return str(p)

        return None

    def __repr__(self):
        if self.source == "local":
            return f"DataConfig(source='local', path='{self.local_data_path}')"
        else:
            return f"DataConfig(source='{self.source}')"


def load_data(config: DataConfig,
              start_date: str,
              end_date: str,
              spark: Optional[SparkSession] = None,
              filter_coinbase: bool = True) -> DataFrame:
    """
    Load transaction data based on configuration.

    Args:
        config: DataConfig instance
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        spark: Existing SparkSession (optional)
        filter_coinbase: Filter out coinbase transactions

    Returns:
        PySpark DataFrame with transactions

    Example:
        config = DataConfig(source="local")
        df = load_data(config, "2021-01-01", "2021-01-07")
        df.show()
    """
    if config.source == "local":
        return _load_local_data(config.local_data_path, start_date, end_date,
                               spark, filter_coinbase)

    elif config.source == "bigquery":
        return _load_bigquery_data(start_date, end_date, spark, filter_coinbase)

    elif config.source == "demo":
        return _load_demo_data(spark)

    else:
        raise ValueError(f"Unknown source: {config.source}")


def _load_local_data(data_path: str, start_date: str, end_date: str,
                     spark: Optional[SparkSession],
                     filter_coinbase: bool) -> DataFrame:
    """Load data from local Blockchair dumps."""
    from src.loaders.blockchair import BlockchairDataLoader

    loader = BlockchairDataLoader(data_path, spark=spark)
    df = loader.load_transactions(start_date, end_date, filter_coinbase=filter_coinbase)

    print(f"✓ Loaded {df.count():,} transactions from local data")
    return df


def _load_bigquery_data(start_date: str, end_date: str,
                        spark: Optional[SparkSession],
                        filter_coinbase: bool) -> DataFrame:
    """Load data from Google BigQuery."""
    try:
        from google.cloud import bigquery
    except ImportError:
        raise ImportError(
            "BigQuery requires: pip install google-cloud-bigquery\n"
            "See docs/SETUP.md for setup instructions"
        )

    client = bigquery.Client()

    coinbase_filter = "AND is_coinbase = FALSE" if filter_coinbase else ""

    query = f"""
    SELECT *
    FROM `bigquery-public-data.crypto_bitcoin.transactions`
    WHERE DATE(block_timestamp) BETWEEN '{start_date}' AND '{end_date}'
        {coinbase_filter}
    """

    print(f"⏳ Querying BigQuery...")
    df_pandas = client.query(query).to_dataframe()

    # Convert to Spark DataFrame
    if spark is None:
        spark = SparkSession.builder.appName("BigQuery").getOrCreate()

    df = spark.createDataFrame(df_pandas)

    print(f"✓ Loaded {df.count():,} transactions from BigQuery")
    return df


def _load_demo_data(spark: Optional[SparkSession]) -> DataFrame:
    """Load demo data."""
    if spark is None:
        spark = SparkSession.builder.appName("Demo").getOrCreate()

    demo_data = [
        (1, "hash1", "2021-01-01", 2, 1, 50000000, 49500000, 500000, False),
        (2, "hash2", "2021-01-01", 3, 2, 75000000, 74200000, 800000, False),
        (3, "hash3", "2021-01-01", 1, 1, 10000000, 9800000, 200000, False),
        (4, "hash4", "2021-01-01", 5, 2, 125000000, 123000000, 2000000, False),
        (5, "hash5", "2021-01-01", 4, 3, 90000000, 89000000, 1000000, False),
    ]

    schema = ["id", "hash", "date", "input_count", "output_count",
             "input_total", "output_total", "fee", "is_coinbase"]

    df = spark.createDataFrame(demo_data, schema)

    print(f"✓ Loaded {df.count():,} demo transactions")
    return df


# Convenience function
def get_loader(config: DataConfig, spark: Optional[SparkSession] = None):
    """
    Get appropriate data loader based on config.

    Returns:
        BlockchairDataLoader if source is local, else None

    Example:
        config = DataConfig(source="local")
        loader = get_loader(config)
        df = loader.load_transactions("2021-01-01", "2021-01-07")
    """
    if config.source == "local":
        from src.loaders.blockchair import BlockchairDataLoader
        return BlockchairDataLoader(config.local_data_path, spark=spark)
    else:
        return None
