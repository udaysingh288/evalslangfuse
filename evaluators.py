"""Scoring functions shared by offline_eval.py and online_eval.py.

Each returns (value, comment). contains_expected and heuristic_quality are
pure and free; judge_quality calls the model and costs money, and is meant
as a simple stand-in for a real judge, not a production one.
"""

import os
import re


def contains_expected(output: str, expected_output: str) -> tuple[float, str]:
    """1.0 if the expected text appears in the output, case-insensitive."""
    hit = expected_output.strip().lower() in output.strip().lower()
    comment = "matched" if hit else f"expected {expected_output!r} not found in {output!r}"
    return (1.0 if hit else 0.0), comment


_BAD_PHRASES = ("i don't know", "i cannot", "i can't", "as an ai", "i'm not able")


def heuristic_quality(question: str, answer: str) -> tuple[float, str]:
    """A free, deterministic stand-in for a judge: present, not a refusal, not absurdly long."""
    text = answer.strip().lower()
    if not text:
        return 0.0, "empty answer"
    if any(phrase in text for phrase in _BAD_PHRASES):
        return 0.3, "answer looks like a refusal or hedge"
    if len(answer) > 600:
        return 0.6, "answer is unusually long for a short question"
    return 1.0, "non-empty, direct answer"


_SCORE_RE = re.compile(r"(\d(?:\.\d+)?)")


def judge_quality(question: str, answer: str, client=None) -> tuple[float, str]:
    """An LLM-as-judge score from 0 to 1. One extra model call; a demo, not a production judge."""
    if client is None:
        from anthropic import Anthropic

        client = Anthropic()
    model = os.environ.get("MODEL_NAME", "claude-sonnet-5")
    prompt = (
        "Rate how well the ANSWER addresses the QUESTION, from 0 (wrong or unhelpful) "
        "to 1 (correct and direct). Reply with only the number.\n\n"
        f"QUESTION: {question}\nANSWER: {answer}"
    )
    response = client.messages.create(
        model=model, max_tokens=10, messages=[{"role": "user", "content": prompt}]
    )
    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    match = _SCORE_RE.search(text)
    if not match:
        return 0.5, f"could not parse a score from: {text!r}"
    value = max(0.0, min(1.0, float(match.group(1))))
    return value, f"judge said: {text.strip()}"
