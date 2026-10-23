"""Host measurement safety and accounting, using injected subprocesses only."""

import json
from pathlib import Path
from typing import Any

import pytest

from controller import measure_contracts as measurement
from controller.backends.codex_cli import CodexCLIBackend
from tests.controller.support import model_contract
from tests.controller.test_codex_cli import MockRunner


def install_runner(monkeypatch: pytest.MonkeyPatch, runner: MockRunner) -> None:
    original = CodexCLIBackend.__init__

    def initialize(self: CodexCLIBackend) -> None:
        original(self, runner=runner, executable="/mock/codex")

    monkeypatch.setattr(CodexCLIBackend, "__init__", initialize)


def test_without_approval_prints_estimate_but_never_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: Any) -> None:
        pytest.fail("Approval gate must precede all model calls")

    monkeypatch.setattr(measurement, "SingleCallBackend", forbidden)
    output = tmp_path / "summary.json"
    assert measurement.main(["--out", str(output)]) == 1
    text = capsys.readouterr().out
    assert "Planned calls: 30" in text and "0.066000" in text
    assert "Refusing to start" in text and not output.exists()


def test_approved_batch_invokes_cli_once_per_sample_and_sums_logs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    runner = MockRunner(output=model_contract())
    install_runner(monkeypatch, runner)
    output = tmp_path / "summary.json"
    assert measurement.main(["--out", str(output), "--i-have-approval"]) == 0
    report = json.loads(output.read_text())
    assert len(runner.calls) == 30
    assert report["cheap_api"]["status"] == report["local"]["status"] == "not measured"
    assert report["totals"]["schema_valid"] == 30
    assert report["totals"]["criteria_count"] == sum(report["totals"]["criteria_by_type"].values())
    assert report["totals"]["llm_judge_share"] == pytest.approx(
        report["totals"]["criteria_by_type"]["llm_judge"] / report["totals"]["criteria_count"])
    for row in report["samples"]:
        assert row["exit_code"] == 0 and row["schema_valid"]
        assert row["usd"] == row["control_calls"][0]["usd"]
        assert row["latency_seconds"] == row["control_calls"][0]["latency_seconds"]
        assert row["assumptions_count"] == len(model_contract()["assumptions"])
    assert report["totals"]["usd"] == pytest.approx(sum(row["usd"] for row in report["samples"]))
    assert all(call["kwargs"]["env"]["HARNESS_NESTED"] == "1" for call in runner.calls)
    assert "gpt-6-luna" in runner.calls[0]["argv"]
    # Curated response fields must never be supplied as golden answers.
    assert "Add and test the specified health endpoint." not in runner.calls[0]["kwargs"]["input"]


@pytest.mark.parametrize("failure", ["invalid", "transport", "unknown"])
def test_failed_sample_never_retries_or_uses_http(
    failure: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    runner = MockRunner(output={} if failure == "invalid" else model_contract(),
                        returncode=1 if failure == "transport" else 0,
                        stdout="" if failure == "unknown" else None)
    install_runner(monkeypatch, runner)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-use-http")
    row = measurement.measure_sample({"id": "sample", "prompt": "Create a file.",
                                      "ambiguous": False}, tmp_path)
    assert len(runner.calls) == 1 and not row["schema_valid"] and row["exit_code"] == 2
    assert row["assumptions_count"] is None and row["criteria_by_type"] is None
    totals = measurement.summarize([row])
    assert totals["llm_judge_share"] is None and totals["schema_pass_rate"] == 0
    if failure == "unknown":
        assert row["usd"] is None and totals["usd"] is None
        assert not totals["accounting_complete"]
