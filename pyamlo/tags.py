import os
from collections import UserDict, UserList
from typing import Any, Hashable, Optional, Union

from yaml import MappingNode, UnsafeLoader, ScalarNode, SequenceNode


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
    ) -> None:
        self.path: str = path
        self.args: list[Any] = args
        self.kwargs: dict[str, Any] = kwargs


class InterpolatedCallSpec:
    """A CallSpec that defers path interpolation until resolution time."""

    def __init__(
        self,
        path_template: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        self.path_template = path_template  # Contains {variable} placeholders
        self.args = args
        self.kwargs = kwargs


class IncludeSpec:
    def __init__(self, path: str):
        self.path = path
        self._base_path: Optional[str] = None

    def set_base_path(self, base_path: str) -> None:
        self._base_path = base_path


class ImportSpec:
    def __init__(self, path: str):
        self.path = path


class IncludeFromSpec:
    def __init__(self, path: str):
        self.path = path
        self._base_path: Optional[str] = None

    def set_base_path(self, base_path: str) -> None:
        self._base_path = base_path


class ConfigLoader(UnsafeLoader):
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
        return CallSpec(suffix, [], mapping)  # type: ignore
    if isinstance(node, SequenceNode):
        seq: list[Any] = loader.construct_sequence(node, deep=True)
        return CallSpec(suffix, seq, {})
    if isinstance(node, ScalarNode):
        val = loader.construct_scalar(node)
        args: list[Any] = [] if val in (None, "") else [val]
        return CallSpec(suffix, args, {})
    raise TagError(f"Unsupported !@ tag '{suffix}' at {node.start_mark}")


def construct_interpolated_callspec(
    loader: ConfigLoader,
    suffix: str,
    node: Union[MappingNode, SequenceNode, ScalarNode],
) -> InterpolatedCallSpec:
    """Constructor for !$ tags that defers path interpolation."""
    if isinstance(node, MappingNode):
        mapping: dict[Hashable, Any] = loader.construct_mapping(node, deep=True)
        return InterpolatedCallSpec(suffix, [], mapping)  # type: ignore
    if isinstance(node, SequenceNode):
        seq: list[Any] = loader.construct_sequence(node, deep=True)
        return InterpolatedCallSpec(suffix, seq, {})
    if isinstance(node, ScalarNode):
        val = loader.construct_scalar(node)
        args: list[Any] = [] if val in (None, "") else [val]
        return InterpolatedCallSpec(suffix, args, {})
    raise TagError(f"Unsupported !$ tag '{suffix}' at {node.start_mark}")


def construct_include(loader: ConfigLoader, node: ScalarNode) -> IncludeSpec:
    return IncludeSpec(loader.construct_scalar(node))


def construct_import(loader: ConfigLoader, node: ScalarNode) -> ImportSpec:
    if not isinstance(node, ScalarNode):
        raise TagError(f"!import must be used with a string path at {node.start_mark}")
    return ImportSpec(loader.construct_scalar(node))


def construct_include_from(loader: ConfigLoader, node: ScalarNode) -> IncludeFromSpec:
    if not isinstance(node, ScalarNode):
        line_info = f" at line {node.start_mark.line + 1}" if hasattr(node, 'start_mark') and node.start_mark else ""
        raise TagError(f"!include_from must be used with a file path, not {node.tag}{line_info}")
    
    path = loader.construct_scalar(node)
    if not path or not isinstance(path, str):
        line_info = f" at line {node.start_mark.line + 1}" if hasattr(node, 'start_mark') and node.start_mark else ""
        raise TagError(f"!include_from requires a non-empty file path{line_info}")
    
    return IncludeFromSpec(path)


ConfigLoader.add_multi_constructor("!@", construct_callspec)
ConfigLoader.add_multi_constructor("!$", construct_interpolated_callspec)
ConfigLoader.add_constructor("!env", construct_env)
ConfigLoader.add_constructor("!extend", construct_extend)
ConfigLoader.add_constructor("!patch", construct_patch)
ConfigLoader.add_constructor("!include", construct_include)
ConfigLoader.add_constructor("!import", construct_import)
ConfigLoader.add_constructor("!include_from", construct_include_from)
