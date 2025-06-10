"""CLI utilities for PYAMLO configuration overrides."""

from io import StringIO
import sys
from typing import Any, Dict, Optional
from functools import reduce

import yaml

from pyamlo.merge import deep_merge
from pyamlo.tags import ConfigLoader


class OverrideError(Exception):
    """Raised when there's an error processing a CLI override."""



def _collect_cli_overrides() -> list[str]:
    """Extract CLI overrides from command line arguments."""
    return [
        arg 
        for arg in sys.argv[1:] 
        if arg.startswith("pyamlo.") and "=" in arg
    ]


def _prepare_overrides(
    overrides: Optional[list[str]], use_cli: bool
) -> list[str]:
    """Prepare all overrides from parameters and CLI."""
    all_overrides = list(overrides) if overrides else []
    if use_cli:
        all_overrides.extend(_collect_cli_overrides())
    return all_overrides


def parse_cli_overrides(overrides: list[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for override in overrides:
        if "=" not in override:
            raise OverrideError(
                f"Invalid override format: {override}. Expected key=value"
            )

        key, value = override.split("=", 1)
        if not key.startswith("pyamlo."):
            continue

        parts = key[7:].split(".")

        try:
            loader = ConfigLoader(StringIO(value))
            parsed_value = loader.get_single_data()
        except Exception:
            try:
                parsed_value = yaml.safe_load(value)
            except yaml.YAMLError:
                parsed_value = value

        target = reduce(lambda d, k: d.setdefault(k, {}), parts[:-1], result)
        target[parts[-1]] = parsed_value

    return result


def process_overrides(
    config: Dict[str, Any], overrides: Optional[list[str]] = None, use_cli: bool = False
) -> Dict[str, Any]:
    overrides = _prepare_overrides(overrides, use_cli)
    if not overrides:
        return config
    override_config = parse_cli_overrides(overrides)
    result = deep_merge(config, override_config)
    return result
