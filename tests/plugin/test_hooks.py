"""stdin-to-stdout tests with mocked CLIs and real session/approval state."""

from __future__ import annotations

import contextlib
import builtins
import io
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
HOOKS = {"SessionStart": "session_start.py", "UserPromptSubmit": "user_prompt_submit.py", "Stop": "stop.py"}


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(ROOT / "plugin/hooks"))
    monkeypatch.delenv("HARNESS_NESTED", raising=False)
    monkeypatch.delenv("HARNESS_STUB", raising=False)
    monkeypatch.delenv("HARNESS_EVENT_LOG", raising=False)
    monkeypatch.setenv("HARNESS_MAX_ATTEMPTS", "3")
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text('{"type":"example"}\n')
    calls: list[dict[str, Any]] = []
    control: dict[str, Any] = {"verdict": None, "returncode": 0, "stdout": None}

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        module, operation = command[2:4]
        calls.append({"module": module, "operation": operation, "command": command, **kwargs})
        assert kwargs["env"]["HARNESS_NESTED"] == "1"
        assert kwargs["shell"] is False
        assert kwargs["capture_output"] is True
        assert kwargs["timeout"] <= 30
        flag = "--handoff" if operation == "validate-handoff" else "--out"
        out = Path(command[command.index(flag) + 1])
        if operation == "contract":
            shutil.copyfile(ROOT / "schemas/examples/contract.json", out)
        elif operation == "check":
            attempt = int(command[command.index("--attempt") + 1])
            name = "verdict_fail.json" if attempt == 1 else "verdict_pass.json"
            value = json.loads((ROOT / "schemas/examples" / name).read_text())
            if control["verdict"] is not None:
                value = dict(control["verdict"])
                value["attempt"] = attempt
            out.write_text(json.dumps(value))
        return subprocess.CompletedProcess(command, control["returncode"],
                                           control["stdout"] if control["stdout"] is not None else str(out) + "\n", "")

    monkeypatch.setattr(subprocess, "run", run)

    def drive(event: str, **updates: Any) -> tuple[dict[str, Any] | None, str]:
        payload = {"session_id": "session-1", "cwd": str(tmp_path), "model": "test",
                   "hook_event_name": event, "transcript_path": str(transcript), **updates}
        stdout, stderr = io.StringIO(), io.StringIO()
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with pytest.raises(SystemExit) as result:
                runpy.run_path(str(ROOT / "plugin/hooks" / HOOKS[event]), run_name="__main__")
        assert result.value.code == 0
        assert "elapsed_seconds=" in stderr.getvalue()
        return json.loads(stdout.getvalue()) if stdout.getvalue() else None, stderr.getvalue()

    return {"drive": drive, "calls": calls, "root": tmp_path, "control": control}


@pytest.mark.parametrize("event", HOOKS)
def test_three_hooks_json_protocol_with_mocked_clis(event: str, harness: dict[str, Any]) -> None:
    drive, root, calls = harness["drive"], harness["root"], harness["calls"]
    if event == "SessionStart":
        directory = root / ".harness"
        directory.mkdir()
        shutil.copyfile(ROOT / "schemas/examples/handoff.json", directory / "handoff.json")
        response, _ = drive(event)
        assert "HARNESS_HANDOFF" in response["hookSpecificOutput"]["additionalContext"]
        assert calls[-1]["operation"] == "validate-handoff"
    else:
        response, _ = drive("UserPromptSubmit", prompt="Add a health endpoint")
        assert "HARNESS_CONTRACT" in response["hookSpecificOutput"]["additionalContext"]
        assert calls[-1]["module"] == "controller"
        if event == "Stop":
            drive("UserPromptSubmit", prompt="approve")
            response, _ = drive("Stop")
            fixture = json.loads((ROOT / "schemas/examples/verdict_fail.json").read_text())
            assert response == {"decision": "block", "reason": fixture["reinstruct_message"]}
            assert calls[-1]["module"] == "verifier"


def test_approval_then_one_reinstruction_then_pass(harness: dict[str, Any]) -> None:
    drive, root, calls = harness["drive"], harness["root"], harness["calls"]
    drive("SessionStart")
    drive("UserPromptSubmit", prompt="Add a health endpoint")
    assert drive("Stop")[0] is None
    assert len(calls) == 1
    assert (root / ".harness/contract.json").read_bytes() == (ROOT / "schemas/examples/contract.json").read_bytes()
    drive("UserPromptSubmit", prompt="approve")
    assert len(calls) == 1
    assert drive("Stop")[0]["decision"] == "block"
    assert drive("Stop", stop_hook_active=True)[0] is None
    assert [call["operation"] for call in calls] == ["contract", "check", "check"]
    state = json.loads((root / ".harness/state.json").read_text())
    assert set(state) == {"attempt", "contract_path", "verdict_path", "handoff_path", "started_at"}
    assert state["attempt"] == 2
    assert json.loads((root / ".harness/session.json").read_text())["phase"] == "complete"
    assert drive("Stop")[0] is None
    assert len(calls) == 3


def test_resume_preserves_pending_contract_but_new_session_resets(harness: dict[str, Any]) -> None:
    drive, root = harness["drive"], harness["root"]
    drive("UserPromptSubmit", prompt="Add a health endpoint")
    original = (root / ".harness/state.json").read_bytes()
    drive("SessionStart", source="resume")
    assert (root / ".harness/state.json").read_bytes() == original
    drive("UserPromptSubmit", prompt="approve")
    drive("Stop")
    drive("SessionStart", source="startup", session_id="new-session")
    assert json.loads((root / ".harness/state.json").read_text())["attempt"] == 0
    assert json.loads((root / ".harness/session.json").read_text())["phase"] == "idle"


def test_edits_regenerate_instead_of_approving(harness: dict[str, Any]) -> None:
    drive, root = harness["drive"], harness["root"]
    drive("UserPromptSubmit", prompt="Add a health endpoint")
    drive("UserPromptSubmit", prompt="edit: preserve the existing response")
    assert "Add a health endpoint" in (root / ".harness/request.txt").read_text()
    assert "edit: preserve" in (root / ".harness/request.txt").read_text()
    assert drive("Stop")[0] is None
    assert [call["operation"] for call in harness["calls"]] == ["contract", "contract"]


def test_changed_contract_cannot_inherit_approval(harness: dict[str, Any]) -> None:
    drive, root = harness["drive"], harness["root"]
    drive("UserPromptSubmit", prompt="Add a health endpoint")
    path = root / ".harness/contract.json"
    value = json.loads(path.read_text())
    value["task_summary"] = "Changed after the summary was reviewed"
    path.write_text(json.dumps(value))
    response, stderr = drive("UserPromptSubmit", prompt="approve")
    assert response is None
    assert "contract changed after review" in stderr
    assert drive("Stop")[0] is None


@pytest.mark.parametrize("limit,missing_message", [(1, False), (3, True)])
def test_exhaustion_or_null_message_ends_with_unmet_items(
    harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch, limit: int, missing_message: bool,
) -> None:
    monkeypatch.setenv("HARNESS_MAX_ATTEMPTS", str(limit))
    fixture = json.loads((ROOT / "schemas/examples/verdict_fail.json").read_text())
    if missing_message:
        fixture["reinstruct_message"] = None
    harness["control"]["verdict"] = fixture
    drive = harness["drive"]
    drive("UserPromptSubmit", prompt="Add a health endpoint")
    drive("UserPromptSubmit", prompt="approve")
    response, _ = drive("Stop")
    assert "decision" not in response
    assert "SC-3" in response["systemMessage"] and "SC-4" in response["systemMessage"]
    assert "Evidence:" in response["systemMessage"]
    assert drive("Stop")[0] is None


@pytest.mark.parametrize("event", HOOKS)
def test_hook_runtime_exception_always_fails_open(harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch, event: str) -> None:
    import _runtime

    def fail(*args: object) -> None:
        raise RuntimeError("simulated state failure")

    monkeypatch.setattr(_runtime.Runtime, "dispatch", fail)
    response, stderr = harness["drive"](event)
    assert response is None
    assert "warning: RuntimeError" in stderr


def test_cli_failure_and_bad_stdout_fail_open(harness: dict[str, Any]) -> None:
    harness["control"]["returncode"] = 2
    response, stderr = harness["drive"]("UserPromptSubmit", prompt="request")
    assert response is None and "exited 2" in stderr
    harness["control"].update(returncode=0, stdout="extra text\n")
    response, stderr = harness["drive"]("UserPromptSubmit", prompt="request")
    assert response is None and "exactly its output path" in stderr


def test_null_transcript_is_fail_open_without_calling_verifier(harness: dict[str, Any]) -> None:
    drive = harness["drive"]
    drive("UserPromptSubmit", prompt="request")
    drive("UserPromptSubmit", prompt="approve")
    response, stderr = drive("Stop", transcript_path=None)
    assert response is None and "available transcript" in stderr
    assert len(harness["calls"]) == 1


def test_default_three_attempt_limit_is_bounded(harness: dict[str, Any]) -> None:
    harness["control"]["verdict"] = json.loads((ROOT / "schemas/examples/verdict_fail.json").read_text())
    drive = harness["drive"]
    drive("UserPromptSubmit", prompt="request")
    drive("UserPromptSubmit", prompt="approve")
    assert drive("Stop")[0]["decision"] == "block"
    assert drive("Stop", stop_hook_active=True)[0]["decision"] == "block"
    assert "unmet items" in drive("Stop", stop_hook_active=True)[0]["systemMessage"]
    assert drive("Stop", stop_hook_active=True)[0] is None
    assert len(harness["calls"]) == 4


@pytest.mark.parametrize("event", HOOKS)
def test_entrypoint_import_failure_always_fails_open(
    harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch, event: str,
) -> None:
    original = builtins.__import__

    def importing(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "_entrypoint":
            raise ImportError("simulated runtime import failure")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    response, stderr = harness["drive"](event)
    assert response is None
    assert "warning: ImportError" in stderr
