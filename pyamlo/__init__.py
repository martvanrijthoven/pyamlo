"""
PYAMLO: A flexible YAML configuration loader.
"""

from .config import SystemInfo, load_config
from .resolve import call

__all__ = ["load_config", "SystemInfo", "call"]


class Step:
    def __init__(self, name: str, inputs: dict = None):
        self.name = name
        self.inputs = inputs
        self.outputs = None

