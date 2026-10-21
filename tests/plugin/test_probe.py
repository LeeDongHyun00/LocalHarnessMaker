"""Tests for the isolated compatibility probe, not production hook claims."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from plugin.hooks.probe import probe


@pytest.mark.parametrize("event", ["SessionStart", "UserPromptSubmit", "Stop"])
def test_stdin_stdout_protocol(event: str, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[2] / "plugin/hooks/probe.py"
    payload = {"hook_event_name": event, "session_id": "test", "stop_hook_active": False}
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
