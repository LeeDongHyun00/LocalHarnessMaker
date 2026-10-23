"""Seeded task-cluster metrics; unknown accounting stays unknown."""

import random
from typing import Any, Callable

METHOD = "task_cluster_percentile_bootstrap"


def pass_rate(tasks: list[dict[str, Any]]) -> float | None:
    """Return passes divided by valid attempted tasks."""
    valid = [t for t in tasks if t["outcome"] != "invalid"]
    return sum(t["outcome"] == "pass" for t in valid) / len(valid) if valid else None


def total(values: list[float | None]) -> float | None:
    """An empty sum is zero; an unknown summand makes the sum unknown."""
    return None if any(v is None for v in values) else sum(values)


def metric(clusters: list[dict[str, Any]], unit: str, size: int,
           statistic: Callable[[list[dict[str, Any]]], float | None], *,
           seed: int, resamples: int = 10000, reason: str = "Zero denominator or missing accounting.") -> dict[str, Any]:
    """Keep task observations together and never discard undefined replicates."""
    if resamples < 1000:
        raise ValueError("At least 1000 bootstrap resamples required")
    value = statistic(clusters) if clusters else None
    samples: list[float] = []
    rng = random.Random(seed)
    if value is not None:
        for _ in range(resamples):
            sample = statistic(rng.choices(clusters, k=len(clusters)))
            if sample is None:
                value = None
                reason = "A bootstrap replicate has zero denominator or missing accounting."
                break
            samples.append(sample)
    samples.sort()

    def quantile(p: float) -> float:
        offset = (len(samples) - 1) * p
        lower = int(offset)
        upper = min(lower + 1, len(samples) - 1)
        return samples[lower] + (samples[upper] - samples[lower]) * (offset - lower)

    return {"value": value, "sample_size": size, "sample_unit": unit,
            "ci95": {"level": .95, "lower": quantile(.025) if value is not None else None,
                     "upper": quantile(.975) if value is not None else None, "method": METHOD},
            "undefined_reason": reason if value is None else None}


def compute(tasks: list[dict[str, Any]], *, seed: int, resamples: int = 10000) -> dict[str, Any]:
    """Compute seven metrics; parity needs an explicit paired report."""
    valid = [t for t in tasks if t["outcome"] != "invalid"]
    eligible = [t for t in valid if t["two_session"]]

    def claims(sample: list[dict[str, Any]]) -> float | None:
        n = sum(t["done_claims"]["claimed_items"] for t in sample)
        return sum(t["done_claims"]["claimed_without_evidence"] for t in sample) / n if n else None

    def cost(sample: list[dict[str, Any]]) -> float | None:
        n = sum(t["outcome"] == "pass" for t in sample)
        usd = total([t["costs"]["total_usd"] for t in sample])
        return usd / n if usd is not None and n else None

    from eval.runner.task_completion import population, rate
    task_claims, counts = population(tasks)
    kwargs = {"seed": seed, "resamples": resamples}
    return {
        "pass_rate": metric(valid, "valid_task", len(valid), pass_rate, **kwargs),
        "false_done_rate": metric(valid, "claimed_criterion", sum(t["done_claims"]["claimed_items"] for t in valid), claims, **kwargs),
        "task_false_done_rate": metric(task_claims, "claimed_complete_task", counts["denominator"], rate,
            reason="No claimed-complete valid tasks with retained final messages and hidden grading; "
                   + str({"exclusions": counts["exclusions"], "undefined_outcomes": counts["undefined_outcomes"]}), **kwargs),
        "cost_per_pass": metric(tasks, "attempted_task", len(tasks), cost, **kwargs),
        "avg_attempts": metric(valid, "valid_task", len(valid), lambda s: sum(t["attempts"] for t in s) / len(s), **kwargs),
        "handoff_success": metric(eligible, "eligible_two_session_task", len(eligible),
            lambda s: sum(t["handoff"]["day2_pass"] and not t["handoff"]["user_restated_day1_context"] for t in s) / len(s), **kwargs),
        "parity": metric([], "matched_task", 0, lambda s: None, reason="No hash-pinned paired local/cheap_api comparator.", **kwargs),
    }
