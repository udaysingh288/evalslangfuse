from evaluators import contains_expected, heuristic_quality


def test_contains_expected_match():
    value, comment = contains_expected("The answer is 391.", "391")
    assert value == 1.0
    assert comment == "matched"


def test_contains_expected_is_case_insensitive():
    value, _ = contains_expected("THE ANSWER IS PARIS", "paris")
    assert value == 1.0


def test_contains_expected_miss():
    value, comment = contains_expected("The answer is 392.", "391")
    assert value == 0.0
    assert "391" in comment


def test_heuristic_quality_empty_answer():
    value, comment = heuristic_quality("q", "")
    assert value == 0.0
    assert "empty" in comment


def test_heuristic_quality_refusal():
    value, comment = heuristic_quality("q", "I cannot help with that.")
    assert value < 1.0
    assert "refusal" in comment or "hedge" in comment


def test_heuristic_quality_good_answer():
    value, _ = heuristic_quality("q", "391")
    assert value == 1.0


def test_heuristic_quality_long_answer():
    value, comment = heuristic_quality("q", "x" * 700)
    assert value == 0.6
    assert "long" in comment
