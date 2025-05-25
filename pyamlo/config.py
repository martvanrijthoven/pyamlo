import getpass
import platform
import socket
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any

import yaml

from pyamlo.merge import process_includes
from pyamlo.resolve import Resolver
from pyamlo.tags import ConfigLoader


def load_config(stream: IO[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Parse YAML from `stream`, apply includes, merges, tags, and
    variable interpolation. Returns config
    """
    raw: dict[str, Any] = yaml.load(stream, Loader=ConfigLoader)
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
