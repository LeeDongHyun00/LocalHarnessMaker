"""Keep control deadlines within the approved caller budgets."""

import pytest

from controller.settings import load_object
from tests.controller.support import ROOT


@pytest.mark.parametrize("backend", ["codex_cli", "cheap_api"])
def test_measured_cloud_deadline_allows_loaded_host_headroom(backend: str) -> None:
    config = load_object(ROOT / "controller/config.yaml")
    # Contract latency rose from 15.6 s idle to 20.0 s with four Codex jobs.
    # The plugin independently enforces its approved 30 s contract cutoff.
    assert config[backend]["timeout_seconds"] == 35


def test_three_cloud_calls_fit_smallest_multi_call_budget() -> None:
    config = load_object(ROOT / "controller/config.yaml")
    # Revised 2026-10-22 decision: handoff=120 s, judge=120 s. Using the
    # larger deadline covers all CLI/HTTP retry and fallback combinations.
    per_call_deadline = max(
        config[backend]["timeout_seconds"] for backend in ("codex_cli", "cheap_api")
    )
    max_generation_calls = 3
    startup_overhead_seconds = 1
    smallest_multi_call_budget_seconds = 120
    assert max_generation_calls * (
        per_call_deadline + startup_overhead_seconds
    ) < smallest_multi_call_budget_seconds
