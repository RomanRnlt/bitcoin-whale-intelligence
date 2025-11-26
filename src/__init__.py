"""
Bitcoin Whale Intelligence - Source Package

This package contains core data loading and configuration functionality.
"""

from .data_config import DataConfig, load_data, get_loader

__all__ = ["DataConfig", "load_data", "get_loader"]
