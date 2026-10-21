"""Offline demo boundary tests; live model execution remains opt-in."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest

from plugin.check_demo_evidence import audit
from plugin.demo import finish, launch, prepare


def test_demo_uses_copied_environment_and_explicit_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNESS_NESTED", "1")
    command_calls: list[dict[str, Any]] = []
    metadata = {"out": str(tmp_path), "codex_home": str(tmp_path / "home"),
                "workspace": str(tmp_path), "thread_id": "demo-session"}

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        command_calls.append({"command": command, **kwargs})
        (tmp_path / "approval-reply.txt").write_text("fixture result")
        return subprocess.CompletedProcess(command, 0, '{"type":"thread.started","thread_id":"demo-session"}\n', "")

    launch(metadata, "approval", run=run)
    call = command_calls[0]
    assert call["command"][4:6] == ["resume", "demo-session"]
    assert call["input"] == "approve"
    assert "HARNESS_NESTED" not in call["env"]
    assert call["env"]["HARNESS_STUB"] == "1"
    assert os.environ["HARNESS_NESTED"] == "1"
    assert call["shell"] is False
    assert call["timeout"] == 180


def test_demo_records_timeout_as_failure(tmp_path: Path) -> None:
    metadata = {"out": str(tmp_path), "codex_home": str(tmp_path / "home"), "workspace": str(tmp_path)}

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, 180, output=b"partial", stderr=b"timeout diagnostic")

    with pytest.raises(subprocess.TimeoutExpired):
        launch(metadata, "request", run=run)
    assert json.loads((tmp_path / "request-result.json").read_text())["exit_code"] == 124
    assert (tmp_path / "request-events.jsonl").read_bytes() == b"partial"


def test_demo_does_not_overwrite_an_attempted_approval(tmp_path: Path) -> None:
    (tmp_path / "approval-result.json").write_text('{"exit_code":124}')

    def forbidden(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("a second executor must not be launched")

    with pytest.raises(ValueError, match="already attempted"):
        finish({"out": str(tmp_path)}, scripted=True, run=forbidden)


def test_demo_rejects_version_upgrade_before_registration(tmp_path: Path) -> None:
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, "codex-cli wrong-version\n", "")

    with pytest.raises(ValueError, match="STOP-P2"):
        prepare(tmp_path / "evidence", run=run)
    assert not (tmp_path / "evidence").exists()


def test_recorded_demo_and_missing_continuation(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "plugin/evidence/2026-10-21-d2-pass"
    result = audit(source)
    assert result["reinstructions"] == 1
    assert result["real_task_verified"] is False
    copy = tmp_path / "damaged"
    shutil.copytree(source, copy)
    events = [json.loads(line) for line in (copy / "hooks.jsonl").read_text().splitlines()]
    for event in events:
        if event["event"] == "Stop" and event["output"] and event["output"].get("decision") == "block":
            event["output"] = None
    (copy / "hooks.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n")
    with pytest.raises(ValueError, match="re-instruction"):
        audit(copy)
