"""Approved handoff CLI, immutable inputs and contract-free consistency checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from verifier.__main__ import main


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "schemas/examples/handoff.json"


def test_reference_handoff_module_entrypoint() -> None:
    supplied = "./schemas/examples/handoff.json"
    original = EXAMPLE.read_bytes()
    result = subprocess.run(
        [sys.executable, "-m", "verifier", "validate-handoff", "--handoff", supplied],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout == supplied + "\n"
    assert result.stderr == ""
    assert EXAMPLE.read_bytes() == original


def test_valid_handoff_preserves_bytes_and_supplied_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "handoff file.json"
    original = b" \r\n" + EXAMPLE.read_bytes() + b"\r\n\t"
    path.write_bytes(original)
    monkeypatch.chdir(tmp_path)
    supplied = "././handoff file.json"
    assert main(["validate-handoff", "--handoff", supplied]) == 0
    captured = capsys.readouterr()
    assert captured.out == supplied + "\n"
    assert captured.err == ""
    assert path.read_bytes() == original


@pytest.mark.parametrize("case", [
    "invalid_json", "invalid_utf8", "missing_field", "extra_field", "wrong_type",
    "nested_missing_field", "nested_extra_field", "nested_wrong_type", "overlap",
])
def test_invalid_handoff_is_input_error_and_preserves_bytes(
    case: str, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    handoff: dict[str, Any] = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    if case == "missing_field":
        del handoff["decisions"]
    elif case == "extra_field":
        handoff["unknown"] = []
    elif case == "wrong_type":
        handoff["done"] = "SC-1"
    elif case == "nested_missing_field":
        del handoff["done"][0]["artifact"]
    elif case == "nested_extra_field":
        handoff["remaining"][0]["unknown"] = "extra"
    elif case == "nested_wrong_type":
        handoff["remaining"][0]["criterion_id"] = 1
    elif case == "overlap":
        handoff["remaining"][0]["criterion_id"] = handoff["done"][0]["criterion_id"]
    original = json.dumps(handoff).encode("utf-8")
    if case == "invalid_json":
        original = b'{"done":'
    elif case == "invalid_utf8":
        original = b"\xff"
    path = tmp_path / "handoff.json"
    path.write_bytes(original)
    assert main(["validate-handoff", "--handoff", str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "input error:" in captured.err
    if case == "overlap":
        assert "both done and remaining: SC-1" in captured.err
    assert path.read_bytes() == original


@pytest.mark.parametrize("case", ["missing", "directory", "unreadable"])
def test_unavailable_handoff_is_input_error(
    case: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "handoff.json"
    if case == "directory":
        path.mkdir()
    elif case == "unreadable":
        path.write_bytes(EXAMPLE.read_bytes())

        def denied(self: Path, *args: Any, **kwargs: Any) -> str:
            raise PermissionError("handoff read denied")

        monkeypatch.setattr(Path, "read_text", denied)
    assert main(["validate-handoff", "--handoff", str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "input error:" in captured.err


@pytest.mark.parametrize("error", [
    RuntimeError("validator failed"), FileNotFoundError("schema missing"),
    json.JSONDecodeError("invalid schema JSON", "?", 0),
])
def test_validator_infrastructure_failure_is_internal_error(
    error: Exception, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "handoff.json"
    original = EXAMPLE.read_bytes()
    path.write_bytes(original)

    def broken(*args: Any, **kwargs: Any) -> None:
        raise error

    monkeypatch.setattr("verifier.handoff_validate.validate", broken)
    assert main(["validate-handoff", "--handoff", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "internal error:" in captured.err
    assert path.read_bytes() == original


@pytest.mark.parametrize("extra_args", [[], ["--handoff", str(EXAMPLE), "--out", "unused.json"]])
def test_handoff_cli_rejects_missing_path_and_out_flag(extra_args: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "verifier", "validate-handoff", *extra_args],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "input error:" in result.stderr
