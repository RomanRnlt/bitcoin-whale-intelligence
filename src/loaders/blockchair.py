#!/usr/bin/env python3
"""
Blockchair Data Loader for PySpark
Lädt lokale Blockchair TSV-Dumps in PySpark DataFrames.

Usage:
    from scripts.load_blockchair_data import BlockchairDataLoader

    loader = BlockchairDataLoader("/Volumes/MySSD/bitcoin_data/extracted")
    df_transactions = loader.load_transactions("2021-01-01", "2021-01-07")
    df_transactions.show()
"""

from pathlib import Path
from typing import Optional, List
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    IntegerType, BooleanType, TimestampType
)


class BlockchairDataLoader:
    """Lädt Blockchair TSV-Dumps in PySpark."""

    # Schema-Definitionen (basierend auf Blockchair Dokumentation)
    SCHEMA_BLOCKS = StructType([
        StructField("id", LongType(), False),
        StructField("hash", StringType(), False),
        StructField("date", StringType(), True),
        StructField("time", TimestampType(), True),
        StructField("median_time", TimestampType(), True),
        StructField("size", IntegerType(), True),
        StructField("stripped_size", IntegerType(), True),
        StructField("weight", IntegerType(), True),
        StructField("version", IntegerType(), True),
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
        StructField("input_total_usd", LongType(), True),
        StructField("output_total", LongType(), True),
        StructField("output_total_usd", LongType(), True),
        StructField("fee_total", LongType(), True),
        StructField("fee_total_usd", LongType(), True),
        StructField("fee_per_kb", LongType(), True),
        StructField("fee_per_kb_usd", LongType(), True),
        StructField("fee_per_kwu", LongType(), True),
        StructField("fee_per_kwu_usd", LongType(), True),
        StructField("cdd_total", LongType(), True),
        StructField("generation", LongType(), True),
        StructField("generation_usd", LongType(), True),
        StructField("reward", LongType(), True),
        StructField("reward_usd", LongType(), True),
        StructField("guessed_miner", StringType(), True),
    ])

    SCHEMA_TRANSACTIONS = StructType([
        StructField("block_id", LongType(), False),
        StructField("id", LongType(), False),
        StructField("hash", StringType(), False),
        StructField("date", StringType(), True),
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
        StructField("input_total_usd", LongType(), True),
        StructField("output_total", LongType(), True),
        StructField("output_total_usd", LongType(), True),
        StructField("fee", LongType(), True),
        StructField("fee_usd", LongType(), True),
        StructField("fee_per_kb", LongType(), True),
        StructField("fee_per_kb_usd", LongType(), True),
        StructField("fee_per_kwu", LongType(), True),
        StructField("fee_per_kwu_usd", LongType(), True),
        StructField("cdd_total", LongType(), True),
    ])

    SCHEMA_OUTPUTS = StructType([
        StructField("block_id", LongType(), False),
        StructField("transaction_id", LongType(), False),
        StructField("index", IntegerType(), False),
        StructField("transaction_hash", StringType(), True),
        StructField("date", StringType(), True),
        StructField("time", TimestampType(), True),
        StructField("value", LongType(), True),
        StructField("value_usd", LongType(), True),
        StructField("recipient", StringType(), True),
        StructField("type", StringType(), True),
        StructField("script_hex", StringType(), True),
        StructField("is_from_coinbase", BooleanType(), True),
        StructField("is_spendable", BooleanType(), True),
        StructField("is_spent", BooleanType(), True),
        StructField("spending_block_id", LongType(), True),
        StructField("spending_transaction_id", LongType(), True),
        StructField("spending_index", IntegerType(), True),
        StructField("spending_transaction_hash", StringType(), True),
        StructField("spending_date", StringType(), True),
        StructField("spending_time", TimestampType(), True),
        StructField("spending_value_usd", LongType(), True),
        StructField("spending_sequence", LongType(), True),
        StructField("spending_signature_hex", StringType(), True),
        StructField("spending_witness", StringType(), True),
        StructField("lifespan", IntegerType(), True),
        StructField("cdd", LongType(), True),
    ])

    def __init__(self, data_dir: str, spark: Optional[SparkSession] = None):
        """
        Initialisiert DataLoader.

        Args:
            data_dir: Pfad zum 'extracted' Verzeichnis (TSV-Dateien)
            spark: Existierende SparkSession (optional, wird sonst erstellt)
        """
        self.data_dir = Path(data_dir)

        if not self.data_dir.exists():
            raise ValueError(f"Data directory nicht gefunden: {self.data_dir}")

        # SparkSession
        if spark is None:
            self.spark = SparkSession.builder \
                .appName("BlockchairDataLoader") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .getOrCreate()
        else:
            self.spark = spark

    def _get_file_paths(self, table: str, start_date: str, end_date: str) -> List[str]:
        """Findet alle TSV-Dateien für Tabelle im Zeitraum."""
        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        paths = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            filename = f"blockchair_bitcoin_{table}_{date_str}.tsv"
            filepath = self.data_dir / table / filename

            if filepath.exists():
                paths.append(str(filepath))

            current += timedelta(days=1)

        return paths

    def load_blocks(self, start_date: str, end_date: str) -> DataFrame:
        """
        Lädt Blocks-Daten für Zeitraum.

        Args:
            start_date: Format "YYYY-MM-DD"
            end_date: Format "YYYY-MM-DD"

        Returns:
            PySpark DataFrame
        """
        paths = self._get_file_paths("blocks", start_date, end_date)

        if not paths:
            raise ValueError(f"Keine blocks-Daten gefunden für {start_date} bis {end_date}")

        print(f"📦 Loading {len(paths)} blocks files...")

        df = self.spark.read \
            .option("header", "true") \
            .option("sep", "\t") \
            .option("inferSchema", "false") \
            .schema(self.SCHEMA_BLOCKS) \
            .csv(paths)

        print(f"✅ Loaded {df.count():,} blocks")
        return df

    def load_transactions(self, start_date: str, end_date: str,
                         filter_coinbase: bool = True) -> DataFrame:
        """
        Lädt Transactions-Daten für Zeitraum.

        Args:
            start_date: Format "YYYY-MM-DD"
            end_date: Format "YYYY-MM-DD"
            filter_coinbase: Coinbase-Transactions filtern (default: True)

        Returns:
            PySpark DataFrame
        """
        paths = self._get_file_paths("transactions", start_date, end_date)

        if not paths:
            raise ValueError(f"Keine transactions-Daten gefunden für {start_date} bis {end_date}")

        print(f"📦 Loading {len(paths)} transactions files...")

        df = self.spark.read \
            .option("header", "true") \
            .option("sep", "\t") \
            .option("inferSchema", "false") \
            .schema(self.SCHEMA_TRANSACTIONS) \
            .csv(paths)

        if filter_coinbase:
            df = df.filter(df.is_coinbase == False)

        print(f"✅ Loaded {df.count():,} transactions")
        return df

    def load_outputs(self, start_date: str, end_date: str,
                    unspent_only: bool = False) -> DataFrame:
        """
        Lädt Outputs-Daten (UTXOs) für Zeitraum.

        Args:
            start_date: Format "YYYY-MM-DD"
            end_date: Format "YYYY-MM-DD"
            unspent_only: Nur unverbrauchte UTXOs laden (default: False)

        Returns:
            PySpark DataFrame
        """
        paths = self._get_file_paths("outputs", start_date, end_date)

        if not paths:
            raise ValueError(f"Keine outputs-Daten gefunden für {start_date} bis {end_date}")

        print(f"📦 Loading {len(paths)} outputs files...")

        df = self.spark.read \
            .option("header", "true") \
            .option("sep", "\t") \
            .option("inferSchema", "false") \
            .schema(self.SCHEMA_OUTPUTS) \
            .csv(paths)

        if unspent_only:
            df = df.filter(df.is_spent == False)

        print(f"✅ Loaded {df.count():,} outputs")
        return df

    def get_multi_input_transactions(self, start_date: str, end_date: str,
                                    min_inputs: int = 2,
                                    max_inputs: int = 50) -> DataFrame:
        """
        Lädt Multi-Input-Transaktionen (für Entity-Clustering).

        Args:
            start_date: Format "YYYY-MM-DD"
            end_date: Format "YYYY-MM-DD"
            min_inputs: Minimum Inputs (default: 2)
            max_inputs: Maximum Inputs (default: 50, filtert Exchanges)

        Returns:
            PySpark DataFrame mit Multi-Input-Transactions
        """
        df = self.load_transactions(start_date, end_date, filter_coinbase=True)

        df_multi = df.filter(
            (df.input_count >= min_inputs) &
            (df.input_count <= max_inputs)
        )

        count = df_multi.count()
        total = df.count()
        print(f"🔗 Multi-Input Transactions: {count:,} ({count/total*100:.1f}%)")

        return df_multi

    def create_temp_views(self, start_date: str, end_date: str):
        """
        Erstellt temporäre SQL-Views für alle Tabellen.
        Ermöglicht SQL-Queries via spark.sql()

        Args:
            start_date: Format "YYYY-MM-DD"
            end_date: Format "YYYY-MM-DD"
        """
        print(f"🔧 Creating temporary SQL views...")

        df_blocks = self.load_blocks(start_date, end_date)
        df_blocks.createOrReplaceTempView("blocks")

        df_transactions = self.load_transactions(start_date, end_date)
        df_transactions.createOrReplaceTempView("transactions")

        df_outputs = self.load_outputs(start_date, end_date)
        df_outputs.createOrReplaceTempView("outputs")

        print(f"✅ Views created: blocks, transactions, outputs")
        print(f"\nNow you can run SQL queries:")
        print(f"  spark.sql('SELECT * FROM transactions WHERE input_count > 5 LIMIT 10').show()")


# Convenience Functions
def load_blockchair_data(data_dir: str, start_date: str, end_date: str,
                        spark: Optional[SparkSession] = None) -> dict:
    """
    Convenience function - lädt alle Tabellen auf einmal.

    Args:
        data_dir: Pfad zu extracted/ Verzeichnis
        start_date: Format "YYYY-MM-DD"
        end_date: Format "YYYY-MM-DD"
        spark: Optional SparkSession

    Returns:
        dict mit DataFrames: {'blocks': df, 'transactions': df, 'outputs': df}
    """
    loader = BlockchairDataLoader(data_dir, spark)

    return {
        'blocks': loader.load_blocks(start_date, end_date),
        'transactions': loader.load_transactions(start_date, end_date),
        'outputs': loader.load_outputs(start_date, end_date)
    }


if __name__ == "__main__":
    # Test/Demo
    import argparse

    parser = argparse.ArgumentParser(description="Test Blockchair Data Loader")
    parser.add_argument('--data-dir', required=True, help='Pfad zu extracted/ Verzeichnis')
    parser.add_argument('--start-date', required=True, help='Start-Datum (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End-Datum (YYYY-MM-DD)')

    args = parser.parse_args()

    loader = BlockchairDataLoader(args.data_dir)

    print("\n" + "="*70)
    print("TESTING BLOCKCHAIR DATA LOADER")
    print("="*70 + "\n")

    # Test Transactions
    df = loader.load_transactions(args.start_date, args.end_date)
    print("\nSample Transactions:")
    df.select("hash", "input_count", "output_count", "fee").show(5)

    # Test Multi-Input
    df_multi = loader.get_multi_input_transactions(args.start_date, args.end_date)
    print("\nSample Multi-Input Transactions:")
    df_multi.select("hash", "input_count", "output_count").show(5)

    # Create SQL views
    loader.create_temp_views(args.start_date, args.end_date)

    print("\n✅ All tests passed!")
