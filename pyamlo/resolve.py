import importlib
import os
import re
from functools import singledispatchmethod
from typing import Any

from pyamlo.expressions import ExpressionEvaluator, is_expression
from pyamlo.include import load_raw, process_includes
from pyamlo.tags import (
    CallSpec,
    ImportSpec,
    IncludeFromSpec,
    IncludeSpec,
    InterpolatedCallSpec,
    ResolutionError,
)


class Resolver:
    VAR_RE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self._expression_evaluator = ExpressionEvaluator(self._get)

    @singledispatchmethod
    def resolve(self, node: Any, path: str = "") -> Any:
        return node

    @resolve.register
    def _(self, node: ImportSpec, path: str = "") -> Any:
        return _import_attr(node.path)

    def _include(self, node, path: str = "") -> dict:
        fn = self.VAR_RE.sub(lambda m: str(self._get(m.group(1))), node.path)
        if hasattr(node, "_base_path") and node._base_path and not os.path.isabs(fn):
            fn = os.path.join(os.path.dirname(node._base_path), fn)
        raw = load_raw(fn)
        merged = process_includes(raw, fn)
        return self.resolve(merged)

    @resolve.register
    def _(self, node: IncludeSpec, path: str = "") -> dict:
        return self._include(node, path)

    @resolve.register
    def _(self, node: IncludeFromSpec, path: str = "") -> dict:
        resolved = self._include(node, path)
        try:
            return resolved.pop(path.split(".")[-1])
        except KeyError:
            raise ResolutionError(
                f"Include '{node.path}' did not resolve to a valid key '{path.split('.')[-1]}'"
            )

    @resolve.register
    def _(self, node: CallSpec, path: str = "") -> Any:
        fn = _import_attr(node.path)
        args = [self.resolve(a, path) for a in node.args]
        kwargs = {k: self.resolve(v, path) for k, v in node.kwargs.items()}
        inst = _apply_call(fn, args, kwargs)
        self.ctx[path] = inst
        return inst

    @resolve.register
    def _(self, node: InterpolatedCallSpec, path: str = "") -> Any:
        interpolated_path = re.sub(
            r"@([a-zA-Z_][a-zA-Z0-9_]*)",
            lambda m: str(self._get(m.group(1))),
            node.path_template,
        )

        fn = _import_attr(interpolated_path)
        args = [self.resolve(a, path) for a in node.args]
        kwargs = {k: self.resolve(v, path) for k, v in node.kwargs.items()}
        inst = _apply_call(fn, args, kwargs)
        self.ctx[path] = inst
        return inst

    @resolve.register
    def _(self, node: dict, path: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {}
        self.ctx[path] = out
        for key, val in node.items():
            child = f"{path}.{key}" if path else key
            out[key] = self.ctx[child] = self.resolve(val, child)
        return out

    @resolve.register
    def _(self, node: list, path: str = "") -> list[Any]:
        return [self.resolve(x, path) for x in node]

    @resolve.register
    def _(self, node: str, path: str = "") -> Any:
        if m := self.VAR_RE.fullmatch(node):
            expression = m.group(1)
            return (
                self._expression_evaluator.evaluate(expression)
                if is_expression(expression)
                else self._get(expression)
            )
        return self.VAR_RE.sub(lambda m: self._resolve_var_to_string(m.group(1)), node)

    def _resolve_var_to_string(self, expression: str) -> str:
        """Resolve any variable/expression to its string representation."""
        result = (
            self._expression_evaluator.evaluate(expression)
            if is_expression(expression)
            else self._get(expression)
        )
        return str(result)

    def _get(self, path: str) -> Any:
        parts = path.split(".")
        obj = self.ctx.get(parts[0])
        if obj is None:
            raise ResolutionError(f"Unknown variable '{parts[0]}'")

        for part in parts[1:]:
            try:
                obj = obj[part] if isinstance(obj, dict) else getattr(obj, part)
            except (KeyError, AttributeError) as e:
                raise ResolutionError(
                    f"Failed to resolve '{part}' in '{path}': {e}"
                ) from e

        return obj


def _import_attr(path: str):
    module, _, name = path.rpartition(".")
    mod = importlib.import_module(module or "builtins")
    return getattr(mod, name or module)


def _apply_call(fn, args, kwargs):
    try:
        return fn(*args, **kwargs)
    except TypeError:
        if len(args) > 1:
            return fn([args], **kwargs)
        raise
