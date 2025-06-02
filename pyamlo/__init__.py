"""
PYAMLO: A flexible YAML configuration loader.
"""

from .config import load_config
from .resolve import call

__all__ = ["load_config", "call"]
