"""The claims sidecar supplies a denominator without extending verdict JSON."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from verifier.__main__ import main
from verifier.check import check_contract
from verifier.rules import Result
from verifier.schema import validate
from tests.verifier.test_cli import arguments
from tests.verifier.test_claims import report_record


@pytest.mark.parametrize("filename", ["verdict.json", "verdict-2.json", "day1-verdict-3.json", "verdict"])
def test_cli_complete_observations(
    filename: str, contract: dict[str, Any], workspace: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = [
        {"id": f"SC-{index}", "description": f"Criterion number {index}", "check": check}
        for index, check in enumerate([
            {"type": "file_exists", "path": "report.txt"},
            {"type": "file_exists", "path": "absent.txt"},
            {"type": "regex", "path": "absent.txt", "pattern": "ok"},
            {"type": "file_exists", "path": "report.txt"},
            {"type": "file_exists", "path": "absent.txt"},
            {"type": "regex", "path": "absent.txt", "pattern": "ok"},
        ], 1)
    ]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    report = "SC-1 through SC-3 pass. SC-4 through SC-6 pending."
    transcript = workspace / "transcript.jsonl"
    transcript.write_text(json.dumps(report_record(report)))
    output = workspace / filename
    assert main(arguments(path, workspace, transcript, output)) == 0
    assert capsys.readouterr().out == str(output) + "\n"
    verdict = json.loads(output.read_text())
    validate(verdict, "verdict.schema.json")
    sidecar = json.loads(output.with_suffix(".claims.json").read_text())
    assert sidecar == {"items": [
        {"id": f"SC-{index}", "claimed": index <= 3,
         "clause": "SC-1 through SC-3 pass." if index <= 3 else "", "status": status}
        for index, status in enumerate(["pass", "fail", "unverifiable"] * 2, 1)
    ], "summary": {"claimed_items": 3, "claimed_and_pass": 1, "claimed_and_fail": 1,
                   "claimed_and_unverifiable": 1, "unclaimed_items": 3}}
    assert verdict["items"][1]["reason"] == "claimed_without_evidence"
    assert verdict["items"][4]["reason"] == "required file is missing"
    first_bytes = output.with_suffix(".claims.json").read_bytes()
    assert main(arguments(path, workspace, transcript, output)) == 0
    assert output.with_suffix(".claims.json").read_bytes() == first_bytes


@pytest.mark.parametrize("empty", [True, False])
def test_quality_warning_sidecar(
    empty: bool, contract: dict[str, Any], workspace: Path, transcript: Path,
) -> None:
    contract["success_criteria"] = [] if empty else [contract["success_criteria"][3]]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 0
    observations = json.loads(output.with_suffix(".claims.json").read_text())
    assert observations["items"] == ([] if empty else [{
        "id": "SC-4", "claimed": True, "clause": "SC-4 done.", "status": "unverifiable",
    }])
    assert sum(observations["summary"][key] for key in ("claimed_items", "unclaimed_items")) == (0 if empty else 1)


@pytest.mark.parametrize("judge_status", ["pass", "fail", "unverifiable"])
def test_judge_claim_status_is_observed_without_changing_reason(
    judge_status: str, contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract["success_criteria"] = [contract["success_criteria"][0], contract["success_criteria"][3]]
    contract["success_criteria"][0]["check"] = {"type": "file_exists", "path": "report.txt"}
    monkeypatch.setattr("verifier.check.judge_criterion", lambda *args, **kwargs: Result(
        judge_status, "llm_judge reviewed artifact", "exact judge reason"))
    observations: dict[str, Any] = {}
    verdict = check_contract(contract, workspace, transcript, 1, observations=observations)
    assert verdict["items"][1]["reason"] == "exact judge reason"
    assert observations["items"][1] == {
        "id": "SC-4", "claimed": True, "clause": "SC-4 done.", "status": judge_status,
    }


def test_no_final_report_has_zero_claims(
    contract: dict[str, Any], workspace: Path,
) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "Report exists", "check": {
        "type": "file_exists", "path": "report.txt"}}]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    transcript = workspace / "no-final.jsonl"
    transcript.write_text(json.dumps(report_record("SC-1 done.", phase="commentary")))
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 0
    assert json.loads(output.with_suffix(".claims.json").read_text()) == {"items": [{
        "id": "SC-1", "claimed": False, "clause": "", "status": "pass",
    }], "summary": {"claimed_items": 0, "claimed_and_pass": 0, "claimed_and_fail": 0,
                    "claimed_and_unverifiable": 0, "unclaimed_items": 1}}


def test_sidecar_write_error_is_internal_and_preserves_verdict(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = []
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    output = workspace / "verdict.json"
    output.write_text("previous verdict")
    original = Path.write_text
    def write(target: Path, data: str, *args: Any, **kwargs: Any) -> int:
        if target == output.with_suffix(".claims.json"):
            raise PermissionError("injected claims write failure")
        return original(target, data, *args, **kwargs)
    monkeypatch.setattr(Path, "write_text", write)
    assert main(arguments(path, workspace, transcript, output)) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "injected claims write failure" in captured.err
    assert output.read_text() == "previous verdict"


def test_input_error_creates_no_sidecar(workspace: Path, transcript: Path) -> None:
    path = workspace / "contract.json"
    path.write_text("{}")
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 1
    assert not output.with_suffix(".claims.json").exists()


def test_module_entrypoint_writes_sidecar(
    contract: dict[str, Any], workspace: Path, transcript: Path,
) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "Report exists", "check": {
        "type": "file_exists", "path": "report.txt"}}]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    output = workspace / "verdict-1.json"
    completed = subprocess.run([sys.executable, "-m", "verifier", *arguments(
        path, workspace, transcript, output)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0 and completed.stdout == str(output) + "\n"
    assert json.loads(output.with_suffix(".claims.json").read_text())["summary"]["claimed_and_pass"] == 1


def test_budget_exhaustion_still_observes_every_criterion(
    contract: dict[str, Any], workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "1")
    observations: dict[str, Any] = {}
    verdict = check_contract(contract, workspace, transcript, 1, observations=observations)
    assert len(observations["items"]) == len(contract["success_criteria"])
    assert all(item["status"] == "unverifiable" for item in observations["items"])
    assert observations["summary"] == {
        "claimed_items": 4, "claimed_and_pass": 0, "claimed_and_fail": 0,
        "claimed_and_unverifiable": 4, "unclaimed_items": 0,
    }
    assert all("budget" in item["reason"] for item in verdict["items"])


def test_cli_description_claim_updates_reason_and_sidecar(
    contract: dict[str, Any], workspace: Path,
) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "Health endpoint returns JSON", "check": {
        "type": "file_exists", "path": "absent.py"}}]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    transcript = workspace / "description.jsonl"
    transcript.write_text(json.dumps(report_record("Health endpoint completed.")))
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 0
    assert json.loads(output.read_text())["items"][0]["reason"] == "claimed_without_evidence"
    assert json.loads(output.with_suffix(".claims.json").read_text())["items"] == [{
        "id": "SC-1", "claimed": True, "clause": "Health endpoint completed.", "status": "fail",
    }]
