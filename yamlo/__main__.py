from pprint import pprint

import click

from yamlo import load_config


@click.command()
@click.argument(
    "config_path", type=click.Path(exists=True, dir_okay=False, readable=True)
)
def main(config_path):
    """Load and process a YAML config file using yamlo."""
    with open(config_path) as f:
        cfg = load_config(f)

    print("Configuration loaded successfully:\n")
    pprint(cfg, sort_dicts=False)


main()