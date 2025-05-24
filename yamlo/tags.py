import os
from collections import UserDict, UserList
from typing import Any, Hashable, Optional, Union

from yaml import MappingNode, SafeLoader, ScalarNode, SequenceNode


class ResolutionError(Exception):
    """Problems during interpolation or object resolution."""


class TagError(Exception):
    """Problems during interpolation or object resolution."""


class ExtendSpec(UserList):
    def __init__(self, items: list[Any]) -> None:
        super().__init__(items)
        self.items = items


class PatchSpec(UserDict):
    def __init__(self, mapping: dict[Hashable, Any]) -> None:
        super().__init__(mapping)
        self.mapping = mapping


class CallSpec:
    def __init__(
        self,
        path: str,
        args: list[Any],
        kwargs: dict[str, Any],
        id_: Optional[str],
    ) -> None:
        self.path: str = path
        self.args: list[Any] = args
        self.kwargs: dict[str, Any] = kwargs
        self.id: Optional[str] = id_


class IncludeSpec:
    def __init__(self, path: str):
        self.path = path


class ConfigLoader(SafeLoader):
    pass


def construct_env(loader: ConfigLoader, node: Union[ScalarNode, MappingNode]) -> Any:
    if isinstance(node, ScalarNode):
        var = loader.construct_scalar(node)
        val = os.environ.get(var)
        if val is None:
            raise ResolutionError(
                f"Environment variable '{var}' not set {node.start_mark}"
            )
        return val
    elif isinstance(node, MappingNode):
        mapping = loader.construct_mapping(node, deep=True)
        var = mapping.get("var") or mapping.get("name")  # type: ignore
        default = mapping.get("default")
        val = os.environ.get(var, default)
        if val is None:
            raise ResolutionError(
                f"Environment variable '{var}' not set and no default provided {node.start_mark}"
            )
        return val
    else:
        raise TagError(
            f"!env must be used with a scalar or mapping node at {node.start_mark}"
        )


def construct_extend(loader: ConfigLoader, node: SequenceNode) -> ExtendSpec:
    if not isinstance(node, SequenceNode):
        raise TagError(f"!extend must be used on a YAML sequence at {node.start_mark}")
    return ExtendSpec(loader.construct_sequence(node, deep=True))


def construct_patch(loader: ConfigLoader, node: MappingNode) -> PatchSpec:
    if not isinstance(node, MappingNode):
        raise TagError(f"!patch must be used on a YAML mapping at {node.start_mark}")
    return PatchSpec(loader.construct_mapping(node, deep=True))


def construct_callspec(
    loader: ConfigLoader,
    suffix: str,
    node: Union[MappingNode, SequenceNode, ScalarNode],
) -> CallSpec:
    if isinstance(node, MappingNode):
        mapping: dict[Hashable, Any] = loader.construct_mapping(node, deep=True)
        id_ = mapping.pop("id", None)
        return CallSpec(suffix, [], mapping, id_)  # type: ignore
    if isinstance(node, SequenceNode):
        seq: list[Any] = loader.construct_sequence(node, deep=True)
        return CallSpec(suffix, seq, {}, None)
    if isinstance(node, ScalarNode):
        val = loader.construct_scalar(node)
        args: list[Any] = [] if val in (None, "") else [val]
        return CallSpec(suffix, args, {}, None)
    raise TagError(f"Unsupported !@ tag '{suffix}' at {node.start_mark}")


def construct_include(loader: ConfigLoader, node: ScalarNode) -> IncludeSpec:
    return IncludeSpec(loader.construct_scalar(node))


ConfigLoader.add_multi_constructor("!@", construct_callspec)
ConfigLoader.add_constructor("!env", construct_env)
ConfigLoader.add_constructor("!extend", construct_extend)
ConfigLoader.add_constructor("!patch", construct_patch)
ConfigLoader.add_constructor("!include", construct_include)
