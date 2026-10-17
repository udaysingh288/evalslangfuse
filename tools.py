"""Tools the agent can call. Pure functions; each returns a JSON-serializable value.

calculator uses ast, not eval(): only numbers and + - * / ** % and parentheses
parse, so a prompt-injected expression can't reach a name, a call, or an import.
"""

import ast
import operator

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


class CalculatorError(ValueError):
    pass


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise CalculatorError(f"unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression. No names, calls, or attribute access."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"not a valid expression: {expression!r}") from exc
    return _eval_node(tree.body)


def count_letters(word: str) -> int:
    """Count alphabetic characters, ignoring spaces, punctuation, and digits."""
    return sum(1 for ch in word if ch.isalpha())


TOOLS = [
    {
        "name": "calculator",
        "description": (
            "Evaluate a basic arithmetic expression (+ - * / ** % and parentheses). "
            "Use this for any arithmetic instead of computing it yourself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "count_letters",
        "description": "Count the letters in a word or phrase. Use this instead of counting yourself.",
        "input_schema": {
            "type": "object",
            "properties": {"word": {"type": "string"}},
            "required": ["word"],
        },
    },
]


def call_tool(name: str, tool_input: dict):
    if name == "calculator":
        return calculator(tool_input["expression"])
    if name == "count_letters":
        return count_letters(tool_input["word"])
    raise KeyError(f"unknown tool: {name}")
