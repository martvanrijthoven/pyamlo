import re
from typing import Any

import keyword

from pyamlo.security import SecurityPolicy


class ExpressionError(Exception):
    """Errors specific to expression evaluation."""


_OPERATORS = {
    "+",
    "-",
    "*",
    "/",
    "//",
    "%",
    "**",
    "(",
    ")",
    "&",
    "|",
    "^",
    "~",
    "<<",
    ">>",
    "==",
    "!=",
    "<=",
    ">=",
    "<",
    ">",
}
_KEYWORDS = {"and", "or", "not", "if", "else"}


def is_expression(expression: str) -> bool:
    return any(op in expression for op in _OPERATORS) or any(
        re.search(rf"\b{kw}\b", expression) for kw in _KEYWORDS
    )


def _extract_variables(expression: str) -> list[str]:
    no_strings = re.sub(r'"[^"]*"|\'[^\']*\'', "", expression)
    variables = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_.]*\b", no_strings)
    return [var for var in variables if not keyword.iskeyword(var)]


class ExpressionEvaluator:
    def __init__(self, variable_resolver, security_policy: SecurityPolicy):
        self._get = variable_resolver
        self.security_policy = security_policy

    def evaluate(self, expression: str) -> Any:
        if is_expression(expression):
            self.security_policy.check_expression(expression)
        safe_expression, namespace = self._get_safe_expr_with_ns(expression)
        try:
            return eval(safe_expression, {"__builtins__": {}}, namespace)
        except Exception as e:
            raise ExpressionError(f"Invalid expression '{expression}': {e}")

    def _get_safe_expr_with_ns(self, expression):
        variables_found = _extract_variables(expression)
        namespace = {}
        safe_expression = expression

        for var_name in variables_found:
            try:
                value = self._get(var_name)
                safe_name = var_name.replace(".", "_")
                namespace[safe_name] = value
                if safe_name != var_name:
                    safe_expression = safe_expression.replace(var_name, safe_name)
            except Exception as e:
                raise ExpressionError(f"Failed to resolve variable '{var_name}': {e}")

        return safe_expression, namespace
