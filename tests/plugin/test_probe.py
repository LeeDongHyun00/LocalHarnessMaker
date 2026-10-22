"""Tests for the isolated compatibility probe, not production hook claims."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from plugin.hooks.probe import probe
from plugin.probe import prepare


@pytest.mark.parametrize("event", ["SessionStart", "UserPromptSubmit", "Stop"])
def test_stdin_stdout_protocol(event: str, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "plugin/hooks/probe.py"
    (tmp_path / ".local-harness-maker").touch()
    payload = {"cwd": str(tmp_path), "hook_event_name": event, "session_id": "test", "stop_hook_active": False}
    result = subprocess.run(
        [sys.executable, str(script)], input=json.dumps(payload), text=True,
        capture_output=True, env={**os.environ, "HARNESS_PROBE_DIR": str(tmp_path)}, check=False,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    if event == "Stop":
        assert output == {"decision": "block", "reason": "test: print one more line"}
    else:
        assert output["hookSpecificOutput"]["hookEventName"] == event
    record = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert record == {"input": payload, "output": output}
    assert "elapsed_seconds=" in result.stderr


def test_stop_bounded_even_without_active_flag(tmp_path: Path) -> None:
    payload = {"hook_event_name": "Stop"}
    assert probe(payload, tmp_path)["decision"] == "block"
    assert probe(payload, tmp_path) == {}


def test_active_stop_does_not_reinstruct(tmp_path: Path) -> None:
    assert probe({"hook_event_name": "Stop", "stop_hook_active": True}, tmp_path) == {}


def test_nested_probe_exits_without_reading_stdin_or_writing(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "plugin/hooks/probe.py"
    process = subprocess.Popen(
        [sys.executable, str(script)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "HARNESS_NESTED": "1", "HARNESS_PROBE_DIR": str(tmp_path / "unused")},
    )
    try:
        # Leave stdin open with no data: reading it would hang.
        assert process.wait(timeout=2) == 0
        stdout, stderr = process.communicate()
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
    assert stdout == b""
    assert stderr == b""
    assert not (tmp_path / "unused").exists()


@pytest.mark.parametrize("stdin", ["not json", '{"hook_event_name":"Unknown"}'])
def test_errors_fail_open(stdin: str, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "plugin/hooks/probe.py"
    result = subprocess.run(
        [sys.executable, str(script)], input=stdin, text=True, capture_output=True,
        env={**os.environ, "HARNESS_PROBE_DIR": str(tmp_path)}, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert "warning:" in result.stderr
    assert "elapsed_seconds=" in result.stderr


def test_prepare_isolated_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("plugin.probe.tempfile.mkdtemp", lambda **kwargs: str(tmp_path / "isolated"))
    (tmp_path / "isolated").mkdir()
    auth_home = tmp_path / "existing-home"
    auth_home.mkdir()
    (auth_home / "auth.json").write_text("test credentials must stay outside evidence")
    monkeypatch.setenv("CODEX_HOME", str(auth_home))
    calls: list[list[str]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "codex-cli 0.162.0-alpha.17.2\n", "")

    output = tmp_path / "evidence"
    metadata = prepare(output, run=run)
    isolated = Path(str(metadata["codex_home"]))
    assert calls == [["codex", "--version"]]
    assert (isolated / "auth.json").is_symlink()
    assert not (output / "auth.json").exists()
    assert not (auth_home / "hooks.json").exists()
    hooks = json.loads((isolated / "hooks.json").read_text())
    assert set(hooks["hooks"]) == {"SessionStart", "UserPromptSubmit", "Stop"}


def test_unlisted_version_runs_and_records_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "no-auth"))
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, "codex-cli 0.163.0-alpha.11.1\n", "")

    output = tmp_path / "evidence"
    metadata = prepare(output, run=run)
    assert metadata["version"] == "codex-cli 0.163.0-alpha.11.1"
    assert json.loads((output / "experiment.json").read_text())["version"] == metadata["version"]


@pytest.mark.parametrize("code,stdout", [(1, "codex-cli 0.163.0-alpha.11.1"), (0, "")])
def test_invalid_version_probe_writes_nothing(tmp_path: Path, code: int, stdout: str) -> None:
    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, code, stdout, "")
    with pytest.raises(ValueError):
        prepare(tmp_path / "evidence", run=run)
    assert not (tmp_path / "evidence").exists()


def test_existing_evidence_cannot_be_overwritten(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="new evidence directory"):
        prepare(tmp_path)


def test_verified_versions_have_passing_matching_evidence() -> None:
    from plugin.versions import verified_versions
    from plugin.check_probe_evidence import audit
    plugin = Path(__file__).resolve().parents[2] / "plugin"
    versions = verified_versions()
    assert next(iter(versions)) == "codex-cli 0.162.0-alpha.17.2"
    for version, directories in versions.items():
        for directory in directories:
            assert audit(plugin / directory, expected_version=version)["version"] == version


@pytest.mark.parametrize("rows", [[], [{"version": "wrong", "evidence": ["evidence/x"]}],
    [{"version": "codex-cli 1.0.0", "evidence": []}],
    [{"version": "codex-cli 1.0.0", "evidence": ["evidence/../escape"]}],
    [{"version": "codex-cli 1.0.0", "evidence": ["evidence/x"]}] * 2])
def test_invalid_verified_versions_rejected(tmp_path: Path, rows: object) -> None:
    from plugin.versions import verified_versions
    path = tmp_path / "versions.json"
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        verified_versions(path)


def test_probe_audit_checks_recorded_version(tmp_path: Path) -> None:
    import shutil
    from plugin.check_probe_evidence import audit
    source = Path(__file__).resolve().parents[2] / "plugin/evidence/2026-10-21-exec"
    with pytest.raises(AssertionError):
        audit(source, expected_version="codex-cli 0.163.0-alpha.11.1")
    copy = tmp_path / "copy"
    shutil.copytree(source, copy)
    metadata = json.loads((copy / "experiment.json").read_text())
    metadata["version"] = ""
    (copy / "experiment.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="invalid Codex version"):
        audit(copy)
