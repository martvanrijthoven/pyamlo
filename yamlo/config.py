import getpass
import platform
import socket
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Mapping

import yaml

from yamlo.merge import process_includes
from yamlo.resolve import Resolver
from yamlo.tags import ConfigLoader


def load_config(stream: IO[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Parse YAML from `stream`, apply includes, merges, tags, and
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
    started: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> Mapping[str, Any]:
        return asdict(self)

def call(calling, **kwargs):
    if not kwargs:
        return calling()
    return calling(**kwargs)

