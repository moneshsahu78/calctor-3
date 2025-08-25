"""
Safe arithmetic expression evaluator.

Supports: +, -, *, /, //, %, **, parentheses, and unary +/-.
Blocks variables, function calls, attribute access, and other Python syntax.
"""

from __future__ import annotations

import ast
from typing import Any


_ALLOWED_BINOPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)

_ALLOWED_UNARYOPS = (
    ast.UAdd,
    ast.USub,
)


class _SafeEvaluator(ast.NodeVisitor):
    """AST visitor that evaluates only arithmetic expressions safely."""

    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            raise ValueError(f"Unsupported expression component: {node.__class__.__name__}")
        return visitor(node)  # type: ignore[misc]

    def visit_Expression(self, node: ast.Expression) -> float:
        return float(self.visit(node.body))

    def visit_BinOp(self, node: ast.BinOp) -> float:
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ValueError("Operator not allowed")
        left = float(self.visit(node.left))
        right = float(self.visit(node.right))

        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.Pow):
            # rudimentary guard against explosive exponentiation
            if abs(right) > 1000:
                raise ValueError("Exponent too large")
            return left ** right
        raise ValueError("Operator not allowed")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        if not isinstance(node.op, _ALLOWED_UNARYOPS):
            raise ValueError("Unary operator not allowed")
        operand = float(self.visit(node.operand))
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("Unary operator not allowed")

    def visit_Num(self, node: ast.Num) -> float:  # Python <3.8
        return float(node.n)

    def visit_Constant(self, node: ast.Constant) -> float:  # Python 3.8+
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed")

    # Block everything else explicitly
    def generic_visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        raise ValueError(f"Unsupported expression component: {node.__class__.__name__}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression safely and return a float result.

    Raises ValueError on invalid syntax or disallowed constructs.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    expr = expression.strip()
    if not expr:
        raise ValueError("Empty expression")
    if len(expr) > 2000:
        raise ValueError("Expression too long")

    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {exc.msg}") from exc

    evaluator = _SafeEvaluator()
    return evaluator.visit(parsed)

