from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from verifier.__main__ import main
from verifier.check import check_contract
from verifier.rules import Result
from verifier.sandbox import Execution
from verifier.schema import validate


@pytest.mark.parametrize("value", ["bad", "0", "-1", "nan", "inf", "-inf"])
def test_invalid_budget_runs_nothing(
    value: str, contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", value)
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("invalid budget must not run a criterion")
    monkeypatch.setattr("verifier.check.judge_criterion", forbidden)
    with pytest.raises(ValueError, match="HARNESS_VERIFY_BUDGET_SECONDS"):
        check_contract(contract, workspace, transcript, 1, forbidden)


@pytest.mark.parametrize("budget,expected", [(None, 120.0), ("10", 8.0), ("0.5", None)])
def test_command_budget_and_cutoff(
    budget: str | None, expected: float | None, contract: dict[str, Any],
    workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    if budget is not None:
        monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", budget)
    now = 0.0
    calls: list[float] = []
    contract["success_criteria"] = contract["success_criteria"][:3]
    def runner(command: str, root: Path, timeout: float) -> Execution:
        nonlocal now
        calls.append(timeout)
        now += 450 if budget is None else float(budget)
        return Execution(error="command timed out")
    verdict = check_contract(contract, workspace, transcript, 1, runner, clock=lambda: now)
    assert calls == ([] if expected is None else [expected])
    skipped = verdict["items"] if expected is None else verdict["items"][1:]
    assert all(item["status"] == "unverifiable" and "budget" in item["reason"] for item in skipped)
    assert verdict["reinstruct_message"] is None and verdict["overall"] == "fail"
    validate(verdict, "verdict.schema.json")


def test_remaining_budget_caps_judge_and_mechanical_checks(
    contract: dict[str, Any], workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "20")
    monkeypatch.setenv("HARNESS_JUDGE_TIMEOUT_SECONDS", "50")
    now = 0.0
    timeouts: list[float] = []
    contract["success_criteria"] = [contract["success_criteria"][0], contract["success_criteria"][3],
                                     contract["success_criteria"][1]]
    def runner(command: str, root: Path, timeout: float) -> Execution:
        nonlocal now
        timeouts.append(timeout)
        now += 5
        return Execution(0)
    def judge(*args: Any, timeout: float, **kwargs: Any) -> Result:
        nonlocal now
        timeouts.append(timeout)
        now += 10
        return Result("pass", "llm_judge: mock", "mock pass")
    monkeypatch.setattr("verifier.check.judge_criterion", judge)
    check_contract(contract, workspace, transcript, 1, runner, clock=lambda: now)
    assert timeouts == [18, 13, 3]


@pytest.mark.parametrize("attempt", [1, 3])
def test_budget_cli_writes_schema_valid_verdict_with_success_exit(
    attempt: int, contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "1")
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    out = workspace / "verdict.json"
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("budget reserve precludes starting criteria")
    monkeypatch.setattr("verifier.check.evaluate", forbidden)
    monkeypatch.setattr("verifier.check.judge_criterion", forbidden)
    assert main(["check", "--contract", str(path), "--workspace", str(workspace),
                 "--transcript", str(transcript), "--attempt", str(attempt), "--out", str(out)]) == 0
    assert capsys.readouterr().out == str(out) + "\n"
    verdict = json.loads(out.read_text())
    validate(verdict, "verdict.schema.json")
    assert all(i["status"] == "unverifiable" and "budget" in i["reason"] for i in verdict["items"])
    assert verdict["reinstruct_message"] is None
