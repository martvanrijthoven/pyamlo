"""Configuration loading and processing."""

import sys
from pathlib import Path
from typing import IO, Any, Optional, Sequence, Union


from pyamlo.cli import process_cli
from pyamlo.merge import deep_merge
from pyamlo.include import process_includes, set_base_paths
from pyamlo.resolve import Resolver
from pyamlo.tags import ConfigLoader
from pyamlo.security import SecurityPolicy


def _load_yaml(
    source: Union[str, Path, IO[str]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    """Load raw YAML from a file or file-like object."""
    if isinstance(source, (str, Path)):
        with open(source, "r") as f:
            loader = ConfigLoader(f, security_policy=security_policy)
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()
    else:
        loader = ConfigLoader(source, security_policy=security_policy)
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()


def load_config(
    source: Union[str, Path, IO[str], Sequence[Union[str, Path, IO[str]]]],
    overrides: Optional[list[str]] = None,
    use_cli: bool = False,
    security_policy: SecurityPolicy = SecurityPolicy(restrictive=False),
) -> dict:
    """Parse YAML from one or more config sources, applying includes, merges, tags, and
    variable interpolation.
    """

    sources = (
        [source]
        if not isinstance(source, Sequence) or isinstance(source, (str, Path))
        else source
    )

    all_overrides = list(overrides) if overrides else []
    if use_cli:
        cli_overrides = [
            arg for arg in sys.argv[1:] if arg.startswith("pyamlo.") and "=" in arg
        ]
        all_overrides.extend(cli_overrides)

    config: dict[str, Any] = {}
    for src in sources:
        raw = _load_yaml(src, security_policy=security_policy)
        if raw:
            if hasattr(src, "name") and hasattr(src, "read"):
                src_path = src.name
            else:
                src_path = str(src)
            if src_path:
                set_base_paths(raw, src_path)
            processed = process_includes(raw, src_path, security_policy=security_policy)
            config = deep_merge(config, processed)

    if all_overrides:
        config = process_cli(config, all_overrides)
    return Resolver(security_policy=security_policy).resolve(config)
