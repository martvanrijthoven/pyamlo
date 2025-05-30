"""CLI utilities for PYAMLO configuration overrides."""

from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict
from pathlib import Path

import yaml

from pyamlo.merge import deep_merge
from pyamlo.tags import ConfigLoader


class OverrideError(Exception):
    """Raised when there's an error processing a CLI override."""


def parse_args(args: List[str]) -> Tuple[List[Union[str, Path]], List[str]]:
    """Parse command line arguments into config files and override arguments.

    Separates config file paths from pyamlo override arguments.

    Args:
        args: List of command line arguments (e.g., from sys.argv[1:])

    Returns:
        Tuple of (config_files, override_args)

    Example:
        >>> files, overrides = parse_args([
        ...     "base.yml", "override.yml",
        ...     "pyamlo.debug=true", "pyamlo.app.name=MyApp"
        ... ])
        >>> files
        ['base.yml', 'override.yml']
        >>> overrides
        ['pyamlo.debug=true', 'pyamlo.app.name=MyApp']
    """
    config_files = []
    override_args = []

    for arg in args:
        if arg.startswith("pyamlo.") and "=" in arg:
            override_args.append(arg)
        elif not arg.startswith("-"):  # Skip flags like --verbose, etc.
            config_files.append(Path(arg))
        # Ignore other flags/options that aren't pyamlo overrides or config files

    return config_files, override_args


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
