"""Verifier-owned fixtures only; no imports from the controller."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
collect_ignore_glob = ["fixtures/*"]


@pytest.fixture(autouse=True)
def verifier_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HARNESS_MAX_ATTEMPTS", raising=False)
    monkeypatch.delenv("HARNESS_BACKEND", raising=False)
    monkeypatch.delenv("HARNESS_JUDGE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("HARNESS_VERIFY_BUDGET_SECONDS", raising=False)


@pytest.fixture
def contract() -> dict[str, Any]:
    return copy.deepcopy(json.loads((ROOT / "schemas/examples/contract.json").read_text()))


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "report.txt").write_text("health ok\nroute preserved\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def transcript() -> Path:
    return FIXTURES / "transcript_pass.jsonl"


_CLAIM_METRICS = pytest.StashKey[dict[str, int]]()


@pytest.fixture
def claim_metrics(request: pytest.FixtureRequest) -> Callable[[dict[str, int]], None]:
    def record(counts: dict[str, int]) -> None:
        request.config.stash[_CLAIM_METRICS] = counts
    return record


def pytest_terminal_summary(terminalreporter: Any) -> None:
    counts = terminalreporter.config.stash.get(_CLAIM_METRICS, None)
    if counts is None:
        return
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    terminalreporter.write_line(
        f"Claim extractor synthetic fixture: reports={counts['reports']} "
        f"precision={precision:.6f} recall={recall:.6f} TP={tp} FP={fp} FN={fn}"
    )
