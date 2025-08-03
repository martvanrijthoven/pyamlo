"""Configuration loading and processing."""

from pathlib import Path
from typing import IO, Optional, Sequence, Union


from pyamlo.override import process_overrides
from pyamlo.resolve import Resolver
from pyamlo.sources import get_sources, merge_all_sources
from pyamlo.security import SecurityPolicy


def load_config(
    source: Union[str, Path, IO[str], dict, Sequence[Union[str, Path, IO[str], dict]]],
    overrides: Optional[list[str]] = None,
    use_cli: bool = False,
    security_policy: SecurityPolicy = SecurityPolicy(restrictive=False),
) -> dict:
    """Parse YAML from one or more config sources, applying includes, merges, tags, and
    variable interpolation.
    """
    sources = get_sources(source)
    config = merge_all_sources(sources, security_policy)
    config = process_overrides(config, overrides, use_cli)
    return Resolver(security_policy=security_policy).resolve(config)
