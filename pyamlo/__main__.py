"""Command line interface for PYAMLO."""

import argparse
import sys
from pathlib import Path

from pyamlo import load_config
from pprint import pprint


def main():
    parser = argparse.ArgumentParser(description="PYAMLO: YAML configuration loader")
    parser.add_argument(
        "configs",
        type=Path,
        nargs="+",
        help="One or more YAML config files. Later files override earlier ones.",
    )
    args, remaining = parser.parse_known_args()

    actual_configs = []
    override_args = []

    for config_arg in args.configs:
        config_str = str(config_arg)
        if config_str.startswith("pyamlo.") and "=" in config_str:
            override_args.append(config_str)
        else:
            actual_configs.append(config_arg)

    overrides = override_args + [arg for arg in remaining if arg.startswith("pyamlo.")]

    if not actual_configs:
        print("Error: At least one config file must be specified", file=sys.stderr)
        return 1

    try:
        config = load_config(actual_configs, cli_overrides=overrides)
        pprint(config)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
