"""Command line interface for PYAMLO."""

import json
import sys
from pathlib import Path
from pprint import pprint
from typing import List, Tuple

from pyamlo import load_config


def parse_args(args: List[str]) -> Tuple[list[Path], list[str], str]:
    config_files = []
    override_args = []
    cfg_output_file = None

    for arg in args:
        if arg.startswith("--cfg-output="):
            cfg_output_file = arg.split("=", 1)[1]
        elif arg.startswith("pyamlo.") and "=" in arg:
            override_args.append(arg)
        elif not arg.startswith("-"):  # Ignore flags
            config_files.append(Path(arg))

    return config_files, override_args, cfg_output_file


def main():
    """Main CLI entry point."""
    try:
        # Parse arguments to separate config files from overrides
        config_files, override_args, cfg_output_file = parse_args(sys.argv[1:])

        if not config_files:
            raise ValueError("At least one config file must be provided")

        # Load config with CLI overrides
        config = load_config(config_files, overrides=override_args)
        
        # If test output file is specified, write config as JSON for testing
        if cfg_output_file:
            with open(cfg_output_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "\nUsage: python -m pyamlo config.yaml [config2.yaml ...] [pyamlo.key=value ...]"
        )
        print("\nExamples:")
        print("  python -m pyamlo config.yaml")
        print("  python -m pyamlo base.yaml override.yaml pyamlo.debug=true")
        print(
            "  python -m pyamlo config.yaml pyamlo.app.name=MyApp pyamlo.database.host=localhost"
        )
        return 1
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
