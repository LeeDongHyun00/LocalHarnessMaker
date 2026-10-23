"""Host measurement safety and accounting, using injected subprocesses only."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from controller import measure_contracts as measurement
from controller.backends.codex_cli import CodexCLIBackend
from tests.controller.support import model_contract
from tests.controller.test_codex_cli import MockRunner


def install_runner(monkeypatch: pytest.MonkeyPatch, runner: MockRunner) -> None:
    original = CodexCLIBackend.__init__

    def initialize(self: CodexCLIBackend, **kwargs: Any) -> None:
        original(self, runner=runner, executable="/mock/codex", **kwargs)

    monkeypatch.setattr(CodexCLIBackend, "__init__", initialize)


def test_without_approval_prints_estimate_but_never_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: Any) -> None:
        pytest.fail("Approval gate must precede all model calls")

    monkeypatch.setattr(measurement, "measurement_backend", forbidden)
    output = tmp_path / "summary.json"
    assert measurement.main(["--out", str(output)]) == 1
    text = capsys.readouterr().out
    assert "Planned calls: 90" in text and "0.198000" in text
    assert "no HTTP fallback" in text
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
    assert report["maximum_generations"] == 90
    assert report["totals"]["generations"] == 30
    assert report["totals"]["quality_gate_firings"] == 0
    assert report["totals"]["criteria_count"] == sum(report["totals"]["criteria_by_type"].values())
    assert report["totals"]["llm_judge_share"] == pytest.approx(
        report["totals"]["criteria_by_type"]["llm_judge"] / report["totals"]["criteria_count"])
    for row in report["samples"]:
        assert row["exit_code"] == 0 and row["schema_valid"]
        assert row["generations"] == 1 and not row["quality_gate_fired"]
        assert row["usd"] == row["control_calls"][0]["usd"]
        assert row["latency_seconds"] == row["control_calls"][0]["latency_seconds"]
        assert row["assumptions_count"] == len(model_contract()["assumptions"])
    assert report["totals"]["usd"] == pytest.approx(sum(row["usd"] for row in report["samples"]))
    assert all(call["kwargs"]["env"]["HARNESS_NESTED"] == "1" for call in runner.calls)
    assert "gpt-6-luna" in runner.calls[0]["argv"]
    # Curated response fields must never be supplied as golden answers.
    assert "Add and test the specified health endpoint." not in runner.calls[0]["kwargs"]["input"]


@pytest.mark.parametrize("failure", ["invalid", "transport", "unknown"])
def test_failed_sample_uses_production_retry_policy_without_http(
    failure: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    runner = MockRunner(output={} if failure == "invalid" else model_contract(),
                        returncode=1 if failure == "transport" else 0,
                        stdout="" if failure == "unknown" else None)
    install_runner(monkeypatch, runner)
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-use-http")
    def forbidden(**kwargs: Any) -> None:
        pytest.fail("Measurement must never construct HTTP backend")

    monkeypatch.setattr("controller.backends.routing.CheapAPIBackend", forbidden)
    row = measurement.measure_sample({"id": "sample", "prompt": "Create a file.",
                                      "ambiguous": False}, tmp_path)
    expected_calls = 3 if failure == "invalid" else 1
    assert len(runner.calls) == row["generations"] == expected_calls
    assert not row["schema_valid"] and row["exit_code"] == 2
    assert not row["quality_gate_fired"]
    assert row["assumptions_count"] is None and row["criteria_by_type"] is None
    totals = measurement.summarize([row])
    assert totals["llm_judge_share"] is None and totals["schema_pass_rate"] == 0
    if failure == "unknown":
        assert row["usd"] is None and totals["usd"] is None
        assert not totals["accounting_complete"]


class SequenceRunner(MockRunner):
    def __init__(self, outputs: list[dict[str, Any]], *, unknown_last: bool = False) -> None:
        super().__init__()
        self.outputs = outputs
        self.unknown_last = unknown_last

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.output = self.outputs[len(self.calls)]
        if self.unknown_last and len(self.calls) == len(self.outputs) - 1:
            self.stdout = ""
        return super().__call__(argv, **kwargs)


@pytest.mark.parametrize("sequence,valid,gate", [
    (["judge", "valid"], True, True),
    (["invalid", "judge", "valid"], True, True),
    (["judge", "invalid", "valid"], True, True),
    (["judge", "judge"], True, True),
    (["invalid", "judge", "judge"], True, True),
    (["judge", "invalid", "judge"], True, True),
    (["judge", "invalid", "invalid"], False, True),
    (["invalid", "invalid", "judge"], False, True),
    (["invalid", "invalid", "valid"], True, False),
])
def test_measurement_runs_production_quality_and_schema_regenerations(
    sequence: list[str], valid: bool, gate: bool,
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    judge = model_contract()
    judge["success_criteria"] = [{"id": "SC-1", "description": "Review result",
                                  "check": {"type": "llm_judge", "rubric": "Correct"}}]
    outputs = {"judge": judge, "valid": model_contract(), "invalid": {}}
    runner = SequenceRunner([outputs[kind] for kind in sequence])
    install_runner(monkeypatch, runner)
    row = measurement.measure_sample({"id": "quality", "prompt": "Create example.py and tests.",
                                      "ambiguous": True}, tmp_path)
    assert row["schema_valid"] is valid
    assert row["exit_code"] == (0 if valid else 2)
    assert row["quality_gate_fired"] is gate
    assert row["generations"] == len(runner.calls) == len(sequence)
    assert row["accounting_complete"]
    assert row["usd"] == pytest.approx(sum(call["usd"] for call in row["control_calls"]))
    assert row["latency_seconds"] == sum(call["latency_seconds"] for call in row["control_calls"])
    totals = measurement.summarize([row])
    assert totals["quality_gate_firings"] == int(gate)
    assert totals["generations"] == len(sequence)
    assert totals["usd"] == row["usd"]
    if valid and sequence[-1] == "judge":
        assert row["assumptions_count"] == len(judge["assumptions"]) + 1
        assert row["criteria_by_type"]["llm_judge"] == 1
    if sequence[:2] == ["judge", "valid"]:
        assert "preceding contract contained no mechanical" in runner.calls[1]["kwargs"]["input"]


def test_unknown_retry_cost_keeps_all_calls_and_null_total(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    runner = SequenceRunner([{}, model_contract()], unknown_last=True)
    install_runner(monkeypatch, runner)
    row = measurement.measure_sample({"id": "unknown", "prompt": "Create example.py.",
                                      "ambiguous": False}, tmp_path)
    assert row["generations"] == 2 and row["exit_code"] == 2
    assert row["control_calls"][0]["usd"] is not None
    assert row["control_calls"][1]["usd"] is None
    assert row["usd"] is None and not row["accounting_complete"]
    assert measurement.summarize([row])["usd"] is None
