"""
Yamlo: A flexible YAML configuration loader.
"""

from .__about__ import __version__

from .config import load_config, SystemInfo
from .resolve import call

__all__ = ["load_config", "SystemInfo", "call"]


