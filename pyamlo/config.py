import getpass
import platform
import socket
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, Union

import yaml

from pyamlo.merge import process_includes
from pyamlo.resolve import Resolver
from pyamlo.tags import ConfigLoader


def load_config(
    source: Union[str, Path, IO[str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse YAML from a file path or file object, apply includes, merges, tags, and
    variable interpolation.

    Args:
        source: Either a path to a YAML file (as string or Path) or a file-like object

    Returns:
        The resolved configuration dictionary and instances dictionary
    """
    if isinstance(source, (str, Path)):
        with open(source, "r") as f:
            raw: dict[str, Any] = yaml.load(f, Loader=ConfigLoader)
    else:
        raw = yaml.load(source, Loader=ConfigLoader)

    merged: dict[str, Any] = process_includes(raw)
    return Resolver().resolve(merged)


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
