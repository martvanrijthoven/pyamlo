import importlib
import os
import re
from functools import singledispatchmethod
from typing import Any

from pyamlo.expressions import ExpressionEvaluator, is_expression
from pyamlo.include import load_raw, process_includes
from pyamlo.security import SecurityPolicy
from pyamlo.tags import (
    CallSpec,
    ImportSpec,
    IncludeFromSpec,
    IncludeSpec,
    ResolutionError,
)


class Resolver:
    VAR_RE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, security_policy=SecurityPolicy(restrictive=False)) -> None:
        self.ctx: dict[str, Any] = {}
        self._expression_evaluator = ExpressionEvaluator(
            self._get, security_policy=security_policy
        )
        self.security_policy = security_policy

    @singledispatchmethod
    def resolve(self, node: Any, path: str = "") -> Any:
        return node

    @resolve.register
    def _(self, node: ImportSpec, path: str = "") -> Any:
        if self.security_policy:
            self.security_policy.check_import(node.path)
        return _import_attr(node.path)

    def _include(self, node, path: str = "") -> dict:
        fn = self.VAR_RE.sub(lambda m: str(self._get(m.group(1))), node.path)
        if hasattr(node, "_base_path") and node._base_path and not os.path.isabs(fn):
            fn = os.path.join(os.path.dirname(node._base_path), fn)
        self.security_policy.check_include(fn)
        raw = load_raw(fn)
        merged = process_includes(raw, fn, security_policy=self.security_policy)
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
        if node.is_interpolated:
            fn = self._resolve_interpolated_callable(node.path)
        else:
            fn = self._resolve_direct_callable(node.path)
        
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
            if is_expression(expression):
                self.security_policy.check_expression(expression)
            return (
                self._expression_evaluator.evaluate(expression)
                if is_expression(expression)
                else self._get(expression)
            )
        return self.VAR_RE.sub(lambda m: self._resolve_var_to_string(m.group(1)), node)

    def _resolve_var_to_string(self, expression: str) -> str:
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

    def _resolve_direct_callable(self, path: str) -> Any:
        self.security_policy.check_import(path)
        return _import_attr(path)
    
    def _resolve_interpolated_callable(self, path_template: str) -> Any:
        if self._is_single_variable(path_template):
            return self._resolve_single_variable(path_template)
        elif self._is_method_call(path_template):
            return self._resolve_method_call(path_template)
        return self._resolve_variable_interpolation(path_template)
    
    def _is_single_variable(self, path: str) -> bool:
        return path.startswith("$") and "." not in path
    
    def _is_method_call(self, path: str) -> bool:
        return (path.startswith("$") and 
                "." in path and 
                not re.search(r"\$", path[1:]))
    
    def _resolve_single_variable(self, path: str) -> Any:
        var_value = self._get(path[1:])
        if isinstance(var_value, str):
            if self.security_policy:
                self.security_policy.check_import(var_value)
            return _import_attr(var_value)
        return var_value
    
    def _resolve_method_call(self, path: str) -> Any:
        obj_name, method_name = path[1:].split(".", 1)
        obj = self._get(obj_name)
        return getattr(obj, method_name)
    
    def _resolve_variable_interpolation(self, path_template: str) -> Any:
        interpolated_path = re.sub(
            r"\$([a-zA-Z_][a-zA-Z0-9_]*)",
            lambda m: str(self._get(m.group(1))),
            path_template,
        )
        if self.security_policy:
            self.security_policy.check_import(interpolated_path)
        return _import_attr(interpolated_path)


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
