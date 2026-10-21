"""Deterministic token bounds, pricing, and executor effort rules (v0)."""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


def count_tokens(text: str) -> int:
    """Return a conservative UTF-8 byte bound, not a model tokenizer count.

    This preflight bound excludes protocol overhead. Actual API usage is used
    for billing metadata; no model-generated token count is trusted.
    """
    return len(text.encode("utf-8"))


@dataclass(frozen=True)
class Prices:
    """Standard USD rates per million tokens."""

    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Prices":
        rates = cls(*(Decimal(str(value[key])) for key in (
            "input_per_million", "cached_input_per_million", "output_per_million"
        )))
        if any(not rate.is_finite() or rate < 0 for rate in (
            rates.input_per_million, rates.cached_input_per_million,
            rates.output_per_million,
        )):
            raise ValueError("Prices must be finite and nonnegative")
        return rates


def calculate_cost(
    input_tokens: int, output_tokens: int, prices: Prices, cached_input_tokens: int = 0
) -> float:
    """Calculate USD from API usage, including cached-input discounts."""
    for value in (input_tokens, output_tokens, cached_input_tokens):
        if type(value) is not int or value < 0:
            raise ValueError("Token counts must be nonnegative integers")
    if cached_input_tokens > input_tokens:
        raise ValueError("Cached input exceeds total input")
    cost = (
        (input_tokens - cached_input_tokens) * prices.input_per_million
        + cached_input_tokens * prices.cached_input_per_million
        + output_tokens * prices.output_per_million
    ) / Decimal(1_000_000)
    return float(cost)


def reasoning_effort(request: str) -> dict[str, str]:
    """Select executor effort from four explainable request features."""
    size = count_tokens(request)
    files = set(re.findall(
        r"(?<![\w/])(?:[\w.-]+/)*[\w-]+\.[A-Za-z][A-Za-z0-9]*(?![\w/])", request
    ))
    tests = bool(re.search(r"\b(?:tests?|pytest|unittest|testing)\b|테스트", request, re.I))
    requirements = len([part for part in re.split(r"[\n;]+|(?<=[.!?])\s+", request)
                        if part.strip()])
    score = (
        (0 if size < 500 else 1 if size < 2000 else 2 if size < 6000 else 3)
        + min(len(files), 3)
        + int(tests)
        + (0 if requirements < 3 else 1 if requirements < 6 else 2)
    )
    value = ("low" if score <= 1 else "medium" if score <= 3 else "high"
             if score <= 5 else "xhigh" if score <= 7 else "max")
    return {"value": value, "rationale": (
        f"effort-v0: utf8_byte_bound={size}; distinct_files={len(files)}; "
        f"tests_requested={str(tests).lower()}; requirement_segments={requirements}; score={score}"
    )}
