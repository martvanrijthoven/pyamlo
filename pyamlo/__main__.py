"""Command line interface for PYAMLO."""

import sys
from pprint import pprint

from pyamlo import load_config
from pyamlo.cli import parse_args


def main():
    """Main CLI entry point."""
    try:
        # Parse arguments to separate config files from overrides
        config_files, override_args = parse_args(sys.argv[1:])
        
        if not config_files:
            raise ValueError("At least one config file must be provided")
        
        # Load config with CLI overrides
        config = load_config(config_files, overrides=override_args)
        pprint(config)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nUsage: python -m pyamlo config.yaml [config2.yaml ...] [pyamlo.key=value ...]")
        print("\nExamples:")
        print("  python -m pyamlo config.yaml")
        print("  python -m pyamlo base.yaml override.yaml pyamlo.debug=true")
        print("  python -m pyamlo config.yaml pyamlo.app.name=MyApp pyamlo.database.host=localhost")
        return 1
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
