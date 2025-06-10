"""CLI utilities for PYAMLO configuration overrides."""

from io import StringIO
from typing import Any, Dict, Optional
from functools import reduce

import yaml

from pyamlo.merge import deep_merge
from pyamlo.tags import ConfigLoader


class OverrideError(Exception):
    """Raised when there's an error processing a CLI override."""


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


def process_cli(
    config: Dict[str, Any], overrides: Optional[list[str]] = None
) -> Dict[str, Any]:
    if not overrides:
        return config

    override_config = parse_cli_overrides(overrides)
    result = deep_merge(config, override_config)
    return result
