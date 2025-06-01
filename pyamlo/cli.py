"""CLI utilities for PYAMLO configuration overrides."""

from typing import Any, Dict, Optional
from collections import defaultdict

import yaml

from pyamlo.merge import deep_merge
from pyamlo.tags import ConfigLoader


class OverrideError(Exception):
    """Raised when there's an error processing a CLI override."""


def parse_cli_overrides(overrides: list[str]) -> Dict[str, Any]:
    grouped_overrides = defaultdict(list)

    for override in overrides:
        if "=" not in override:
            raise OverrideError(
                f"Invalid override format: {override}. Expected key=value"
            )

        key, value = override.split("=", 1)
        if not key.startswith("pyamlo."):
            continue

        parts = key[7:].split(".")
        root = parts[0]

        grouped_overrides[root].append((parts[1:], value))

    combined_yaml = ""
    for root, entries in grouped_overrides.items():
        combined_yaml += f"{root}:\n"
        for parts, value in entries:
            indent = "  "
            for part in parts[:-1]:
                combined_yaml += f"{indent}{part}:\n"
                indent += "  "
            if parts:
                combined_yaml += f"{indent}{parts[-1]}: {value}\n"
            else:
                combined_yaml += f"{indent}{value}\n"

    try:
        parsed = yaml.load(combined_yaml, Loader=ConfigLoader)
        return parsed if parsed else {}
    except yaml.YAMLError as e:
        raise OverrideError(f"Invalid YAML in overrides: {e}")


def process_cli(
    config: Dict[str, Any], overrides: Optional[list[str]] = None
) -> Dict[str, Any]:
    if not overrides:
        return config

    override_config = parse_cli_overrides(overrides)
    result = deep_merge(config, override_config)
    return result
