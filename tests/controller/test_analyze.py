from decimal import Decimal

import pytest

from controller.analyze import Prices, calculate_cost, count_tokens, reasoning_effort


def test_token_bound_handles_empty_ascii_and_unicode() -> None:
    assert count_tokens("") == 0
    assert count_tokens("hello") == 5
    assert count_tokens("테스트") == 9


def test_cost_uses_cached_input_and_decimal_rates() -> None:
    prices = Prices(Decimal("0.4"), Decimal("0.1"), Decimal("1.6"))
    assert calculate_cost(1000, 200, prices, 100) == 0.00069


@pytest.mark.parametrize("inputs,outputs,cached", [(-1, 0, 0), (1, -1, 0),
    (1, 0, 2), (True, 0, 0), (1.1, 0, 0)])
def test_invalid_usage_rejected(inputs: int, outputs: int, cached: int) -> None:
    with pytest.raises(ValueError):
        calculate_cost(inputs, outputs, Prices(Decimal(1), Decimal(1), Decimal(1)), cached)


@pytest.mark.parametrize("rate", ["-1", "NaN", "Infinity"])
def test_invalid_prices_rejected(rate: str) -> None:
    with pytest.raises(ValueError):
        Prices.from_dict({"input_per_million": rate, "cached_input_per_million": "0",
                          "output_per_million": "1"})


@pytest.mark.parametrize("prompt,level", [
    ("Rename title", "low"),
    ("Update app/a.py and tests/b.py using pytest.", "medium"),
    ("a.py b.py c.py pytest.\nDo this.\nThen that.", "high"),
    ("x" * 2000 + " a.py b.py c.py pytest.\nDo this.\nThen that.", "xhigh"),
    ("x" * 6000 + " a.py b.py c.py pytest.\n1\n2\n3\n4\n5", "max"),
])
def test_effort_all_levels(prompt: str, level: str) -> None:
    effort = reasoning_effort(prompt)
    assert effort["value"] == level
    assert effort["rationale"].startswith("effort-v1:")


@pytest.mark.parametrize("size,points", [(499, 0), (500, 1), (1999, 1), (2000, 2),
                                       (5999, 2), (6000, 3)])
def test_size_thresholds(size: int, points: int) -> None:
    assert reasoning_effort("x" * size)["rationale"].endswith(f"score={points}")


def test_files_are_distinct_and_test_feature_is_explicit() -> None:
    rationale = reasoning_effort("Edit app/a.py and app/a.py; add 테스트.")["rationale"]
    assert "distinct_files=1" in rationale
    assert "tests_requested=true" in rationale


def test_effort_v1_deduplicates_requirement_segments() -> None:
    effort = reasoning_effort("1. Update title.\n2. update title!\n- Update   title; update title")
    assert "requirement_segments=1" in effort["rationale"]
