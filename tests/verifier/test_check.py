from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import re
from typing import Any

import pytest
from jsonschema import ValidationError

from verifier.check import check_contract, validate
from verifier.rules import Result
from verifier.sandbox import Execution


def test_shared_example_golden_mechanical_pass(
    contract: dict[str, Any], workspace: Path, transcript: Path,
) -> None:
    """Original shared command strings, with explicitly mocked command outcomes."""
    commands = [c["check"]["command"] for c in contract["success_criteria"][:3]]
    seen: list[str] = []

    def runner(command: str, root: Path, timeout: float) -> Execution:
        seen.append(command)
        return Execution(0, "health response verified\n" if command == commands[1] else "")

    mechanical = copy.deepcopy(contract)
    mechanical["success_criteria"] = mechanical["success_criteria"][:3]
    verdict = check_contract(mechanical, workspace, transcript, 2, runner)
    reference = json.loads((Path(__file__).resolve().parents[2] / "schemas/examples/verdict_pass.json").read_text())
    assert [(i["id"], i["status"]) for i in verdict["items"]] == [(i["id"], i["status"]) for i in reference["items"][:3]]
    assert verdict["overall"] == "pass"
    assert verdict["reinstruct_message"] is None
    assert seen == commands
    validate(verdict, "verdict.schema.json")


def test_shared_example_golden_mechanical_fail(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands = [c["check"]["command"] for c in contract["success_criteria"][:3]]

    def runner(command: str, root: Path, timeout: float) -> Execution:
        if command == commands[2]:
            return Execution(4, stderr="ERROR: file or directory not found: tests/test_health.py")
        return Execution(0, "health response verified\n" if command == commands[1] else "")

    reference = json.loads((Path(__file__).resolve().parents[2] / "schemas/examples/verdict_fail.json").read_text())

    def judge(*args: Any, **kwargs: Any) -> Result:
        item = reference["items"][3]
        return Result(item["status"], item["evidence"], item["reason"])

    monkeypatch.setattr("verifier.check.judge_criterion", judge)
    verdict = check_contract(contract, workspace, transcript, 1, runner)
    assert [(i["id"], i["status"]) for i in verdict["items"]] == [(i["id"], i["status"]) for i in reference["items"]]
    assert verdict["overall"] == "fail"

    def named_items(message: str) -> set[str]:
        prefix = message.split(" are not done.", 1)[0]
        return {f"SC-{number}" for number in re.findall(r"\b(?:SC-)?(\d+)\b", prefix)}

    assert verdict["reinstruct_message"] is not None
    assert named_items(verdict["reinstruct_message"]) == named_items(reference["reinstruct_message"])
    validate(verdict, "verdict.schema.json")


def test_full_example_does_not_pass_without_judge(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*args: Any, **kwargs: Any) -> None:
        raise OSError("mock missing controller judge")

    monkeypatch.setattr("verifier.judge.run_judge", unavailable)
    def runner(command: str, root: Path, timeout: float) -> Execution:
        return Execution(0, "health response verified\n" if "TestClient" in command else "")

    verdict = check_contract(contract, workspace, transcript, 1, runner)
    assert verdict["overall"] == "fail"
    assert verdict["items"][3]["status"] == "unverifiable"


@pytest.mark.parametrize("empty", [True, False])
def test_quality_warning(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    capsys: pytest.CaptureFixture[str], empty: bool,
) -> None:
    contract["success_criteria"] = [] if empty else [contract["success_criteria"][3]]

    def forbidden(command: str, root: Path, timeout: float) -> Execution:
        raise AssertionError("quality warnings must not execute checks")

    verdict = check_contract(contract, workspace, transcript, 1, forbidden)
    assert verdict["overall"] == "fail"
    assert all(i["status"] == "unverifiable" for i in verdict["items"])
    assert verdict["reinstruct_message"] is not None
    assert len(verdict["reinstruct_message"]) <= 300
    assert "Items 1 are not done." in verdict["reinstruct_message"]
    assert ("contract-quality" if empty else "SC-4") == verdict["items"][0]["id"]
    assert "warning:" in capsys.readouterr().err
    validate(verdict, "verdict.schema.json")


def test_duplicate_ids_rejected(contract: dict[str, Any], workspace: Path, transcript: Path) -> None:
    contract["success_criteria"][1]["id"] = "SC-1"
    with pytest.raises(ValueError, match="unique"):
        check_contract(contract, workspace, transcript, 1)


def test_invalid_contract_rejected(contract: dict[str, Any], workspace: Path, transcript: Path) -> None:
    contract["success_criteria"][0]["check"]["expected"] = "success"
    with pytest.raises(ValidationError):
        check_contract(contract, workspace, transcript, 1)


def test_invalid_transcript_rejected(contract: dict[str, Any], workspace: Path) -> None:
    path = workspace / "bad.jsonl"
    path.write_text("not JSON")
    with pytest.raises(ValueError):
        check_contract(contract, workspace, path, 1)


def test_stable_mocked_verdict_and_timing_log(
    contract: dict[str, Any], workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = contract["success_criteria"][:3]

    def runner(command: str, root: Path, timeout: float) -> Execution:
        return Execution(0, "health response verified\n" if "TestClient" in command else "", duration=0.0)

    first = check_contract(contract, workspace, transcript, 1, runner)
    second = check_contract(contract, workspace, transcript, 1, runner)
    assert first == second
    logs = capsys.readouterr().err.splitlines()
    assert len(logs) == 2
    assert all("elapsed_seconds=" in line and "overhead_seconds=" in line for line in logs)
    assert all(float(line.split("overhead_seconds=")[1]) < 1 for line in logs)


def test_verifier_never_imports_controller() -> None:
    for source in (Path(__file__).resolve().parents[2] / "verifier").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                assert all(not a.name.startswith("controller") for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("controller")
            elif isinstance(node, ast.Call) and node.args:
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    assert not (isinstance(node.args[0], ast.Constant) and str(node.args[0].value).startswith("controller"))
