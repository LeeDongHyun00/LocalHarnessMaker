"""Evaluation metrics; invalid runs never contribute to pass rate."""

from typing import Any


def pass_rate(tasks: list[dict[str, Any]]) -> float | None:
    """Return passes divided by valid attempted tasks, or null if none exist."""
    valid = [task for task in tasks if task["outcome"] != "invalid"]
    return sum(task["outcome"] == "pass" for task in valid) / len(valid) if valid else None
