"""Configuration loading and processing."""

import getpass
import platform
import socket
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, Optional, Sequence, Union

import yaml

from pyamlo.cli import process_cli
from pyamlo.merge import deep_merge, process_includes
from pyamlo.resolve import Resolver
from pyamlo.tags import ConfigLoader, IncludeSpec


def _set_base_paths(data: Any, base_path: str) -> None:
    """Recursively set base paths on IncludeSpec objects."""
    if isinstance(data, IncludeSpec):
        data.set_base_path(base_path)
    elif isinstance(data, dict):
        for value in data.values():
            _set_base_paths(value, base_path)
    elif isinstance(data, list):
        for item in data:
            _set_base_paths(item, base_path)


def _load_yaml(source: Union[str, Path, IO[str]]) -> dict[str, Any]:
    """Load raw YAML from a file or file-like object."""
    if isinstance(source, (str, Path)):
        with open(source, "r") as f:
            return yaml.load(f, Loader=ConfigLoader)
    return yaml.load(source, Loader=ConfigLoader)


def load_config(
    source: Union[str, Path, IO[str], Sequence[Union[str, Path, IO[str]]]],
    overrides: Optional[list[str]] = None,
    use_cli: bool = False,
) -> dict:
    """Parse YAML from one or more config sources, applying includes, merges, tags, and
    variable interpolation.

    Order of processing:
    1. For each config file:
       - Load the YAML content
       - Process include (relative to file's location)
    2. Merge config files in order (later files override earlier ones)
    3. Apply overrides (manual and/or CLI) if any
    4. Resolve variables and instantiate objects

    Args:
        source: One or more config sources. Each can be:
            - A path to a YAML file (as string or Path)
            - A file-like object containing YAML
            - A sequence of the above (files are merged in order)
        overrides: Optional list of override strings in format ["key=value", "key.nested=value"]
            Values can use YAML tags like !extend [4,5] or !patch {"debug": true}
        use_cli: If True, automatically reads CLI overrides from sys.argv and merges them
            with any manually provided overrides

    Returns:
        The resolved configuration dictionary
    """

    sources = (
        [source]
        if not isinstance(source, Sequence) or isinstance(source, (str, Path))
        else source
    )

    # Collect all overrides (manual + CLI if requested)
    all_overrides = list(overrides) if overrides else []

    if use_cli:
        import sys

        cli_overrides = [
            arg for arg in sys.argv[1:] if arg.startswith("pyamlo.") and "=" in arg
        ]
        all_overrides.extend(cli_overrides)

    config: dict[str, Any] = {}
    for src in sources:
        raw = _load_yaml(src)
        if raw:
            if hasattr(src, "name") and hasattr(src, "read"):
                src_path = src.name
            else:
                src_path = str(src)
            if src_path:
                _set_base_paths(raw, src_path)
            processed = process_includes(raw, src_path)
            config = deep_merge(config, processed)

    if all_overrides:
        config = process_cli(config, all_overrides)

    return Resolver().resolve(config)


@dataclass(frozen=True, slots=True)
class SystemInfo:
    host: str = field(default_factory=socket.gethostname)
    user: str = field(default_factory=getpass.getuser)
    os: str = field(default_factory=platform.system)
    arch: str = field(default_factory=platform.machine)
    python: str = field(default_factory=platform.python_version)
    cwd: str = field(default_factory=lambda: str(Path.cwd()))
    started: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_dict(self) -> Mapping[str, Any]:
        return asdict(self)
