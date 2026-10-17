import pytest

from tools import CalculatorError, calculator, call_tool, count_letters


@pytest.mark.parametrize(
    "expr, value",
    [
        ("2 + 2", 4),
        ("23 * 17", 391),
        ("144 / 12", 12),
        ("(3 + 4) * (10 - 8)", 14),
        ("2 ** 10", 1024),
        ("-5 + 2", -3),
        ("15/100 * 200", 30.0),
    ],
)
def test_calculator_basic(expr, value):
    assert calculator(expr) == value


@pytest.mark.parametrize("expr", ["__import__('os')", "open('x')", "1; 2", "a + 1", "1 if True else 2"])
def test_calculator_rejects_unsafe_or_unsupported_input(expr):
    with pytest.raises(CalculatorError):
        calculator(expr)


@pytest.mark.parametrize(
    "word, n",
    [("langfuse", 8), ("strawberry", 10), ("a-b c", 3), ("", 0), ("Claude3", 6)],
)
def test_count_letters(word, n):
    assert count_letters(word) == n


def test_call_tool_dispatches_to_calculator():
    assert call_tool("calculator", {"expression": "1+1"}) == 2


def test_call_tool_dispatches_to_count_letters():
    assert call_tool("count_letters", {"word": "hi"}) == 2


def test_call_tool_rejects_unknown_name():
    with pytest.raises(KeyError):
        call_tool("nope", {})
