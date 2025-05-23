"""
Yamlo: A flexible YAML configuration loader.
"""

__version__ = "0.0.1"

from .config import load_config, SystemInfo
from .resolve import call

__all__ = ["load_config", "SystemInfo", "call"]


