from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from verifier.__main__ import main
from verifier.check import validate


def arguments(contract_path: Path, workspace: Path, transcript: Path, output: Path) -> list[str]:
    return ["check", "--contract", str(contract_path), "--workspace", str(workspace),
            "--transcript", str(transcript), "--attempt", "1", "--out", str(output)]


def test_cli_exact_stdout_and_schema(
    contract: dict[str, Any], workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "Report exists", "check": {"type": "file_exists", "path": "report.txt"}}]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 0
    captured = capsys.readouterr()
    assert captured.out == str(output) + "\n"
    assert "verifier elapsed_seconds=" in captured.err
    verdict = json.loads(output.read_text())
    assert verdict["overall"] == "pass"
    validate(verdict, "verdict.schema.json")


def test_cli_failing_verdict_is_successful_operation(
    contract: dict[str, Any], workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "Absent", "check": {"type": "file_exists", "path": "absent"}}]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 0
    assert json.loads(output.read_text())["overall"] == "fail"
    assert capsys.readouterr().out == str(output) + "\n"


def test_cli_invalid_input(
    workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    path = workspace / "contract.json"
    path.write_text("{}")
    output = workspace / "verdict.json"
    assert main(arguments(path, workspace, transcript, output)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "input error:" in captured.err
    assert not output.exists()


def test_cli_output_failure(
    contract: dict[str, Any], workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    contract["success_criteria"] = []
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    assert main(arguments(path, workspace, transcript, workspace / "absent/verdict.json")) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "internal error:" in captured.err


def test_cli_internal_failure(
    workspace: Path, transcript: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = workspace / "contract.json"
    path.write_text("{}")

    def broken(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("mock verifier failure")

    monkeypatch.setattr("verifier.__main__.check_contract", broken)
    assert main(arguments(path, workspace, transcript, workspace / "verdict.json")) == 2
    assert capsys.readouterr().out == ""


def test_module_entrypoint_bad_arguments() -> None:
    result = subprocess.run([sys.executable, "-m", "verifier", "check"], capture_output=True, text=True)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "input error:" in result.stderr
