"""Re-audit synthetic retained runs without executors or artifact mutation."""

import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from eval.runner import core, reaudit
from eval.runner.audit import PrivateGraders, audit_logs


@pytest.fixture
def finished(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    public = repository / "eval/tasks/unit-task"
    public.mkdir(parents=True)
    (public / "prompt.md").write_text('Example: "shared-example"\n')
    monkeypatch.setattr(core, "REPOSITORY", repository)
    private_root = tmp_path / "trusted"
    graders = private_root / "unit-task"
    graders.mkdir(parents=True)
    (graders / "test_synthetic.py").write_text('assert check("shared-example")\n')
    private = PrivateGraders.load(private_root, "unit-task", repository)
    runtime = tmp_path / "runtime"
    (runtime / "workspace").mkdir(parents=True)
    (runtime / "codex-home/sessions").mkdir(parents=True)
    events = runtime / "exec-1.jsonl"
    events.write_text('{"type":"turn.completed"}\n')
    native = runtime / "codex-home/sessions/native.jsonl"
    native.write_text(json.dumps({"type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "CommandExecution", "command": ["pytest", "-q"],
        "aggregated_output": 'assert check("shared-example")\nif __name__ == "__main__":\n'}}}) + "\n")
    audit = audit_logs([events, native], private, workspace=runtime / "workspace", repository=repository,
                       grading_roots=core.audit_roots(runtime))
    out = tmp_path / "out"
    out.mkdir()
    (out / "checkpoint.json").write_text(json.dumps({"report_schema": "evaluation-report-v1", "tasks": {
        "unit-task": {"phase": "finished", "runtime": str(runtime), "segments": [{"events": events.name}],
                      "result": {"grader_access_audit": audit}}}}))
    (out / "report.json").write_text(json.dumps({"tasks": [{"task_id": "unit-task"}]}))

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Re-audit must never execute subprocesses")

    monkeypatch.setattr(core, "run_process", forbidden)
    monkeypatch.setattr(core.subprocess, "run", forbidden)
    return private_root, out, runtime


def snapshot(root: Path) -> dict[str, bytes]:
    """Include the original logs and run artifacts in the immutability check."""
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_reaudit_clean_is_read_only_and_sanitized(finished: tuple[Path, Path, Path],
                                                 monkeypatch: pytest.MonkeyPatch,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    private, out, runtime = finished
    before = snapshot(out.parent)
    monkeypatch.setattr("sys.argv", ["reaudit", "--private-root", str(private), "--out", str(out)])
    assert reaudit.main() == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {"task_id": "unit-task", "status": "clean",
                                        "error_kinds": [], "match_labels": []}
    assert str(runtime) not in captured.out and "shared-example" not in captured.out
    assert snapshot(out.parent) == before


@pytest.mark.parametrize("case", ["hidden_output", "private_path", "grading_path", "workspace_path",
                                  "unknown_record", "missing_log", "changed_log", "changed_grader",
                                  "missing_native", "missing_workspace"])
def test_reaudit_uses_real_roots_and_retained_manifests(finished: tuple[Path, Path, Path], case: str) -> None:
    private_root, out, runtime = finished
    private = PrivateGraders.load(private_root, "unit-task", core.REPOSITORY)
    log = runtime / "exec-1.jsonl"
    expected_errors: set[str] = set()
    labels: set[str] = set()
    if case == "hidden_output":
        secret = 'assert check("distinct-hidden-975319")'
        private.files[0].write_text(secret + "\n")
        item = {"type": "command_execution", "command": "cat opaque", "aggregated_output": secret}
        labels.add("private_line_fingerprint")
        expected_errors.update({"private_grader_manifest_mismatch", "retained_log_manifest_mismatch"})
    elif case in {"private_path", "grading_path", "workspace_path"}:
        target = (private_root if case == "private_path" else core.audit_roots(runtime)[0]
                  if case == "grading_path" else runtime / "workspace")
        item = {"type": "command_execution", "command": "cat " + str(target / "child.txt")}
        if case != "workspace_path":
            labels.add("protected_path")
        if case == "private_path":
            labels.add("private_root")
        expected_errors.add("retained_log_manifest_mismatch")
    else:
        item = None
    if item:
        log.write_text(json.dumps({"type": "item.completed", "item": item}) + '\n{"type":"turn.completed"}\n')
    if case == "unknown_record":
        log.write_text('{"type":"unknown-synthetic"}\n{"type":"turn.completed"}\n')
        expected_errors.update({"unsupported_event", "retained_log_manifest_mismatch"})
    if case == "missing_log":
        log.rename(runtime / "unlisted-log")
        expected_errors.update({"missing_log", "retained_log_manifest_mismatch"})
    if case == "changed_log":
        log.write_text(log.read_text() + '\n')
        expected_errors.update({"malformed_event", "retained_log_manifest_mismatch"})
    if case == "changed_grader":
        private.files[0].write_text("# changed synthetic grader\n")
        expected_errors.add("private_grader_manifest_mismatch")
    if case == "missing_native":
        native = runtime / "codex-home/sessions/native.jsonl"
        native.rename(runtime / "unlisted-native")
        expected_errors.add("retained_log_manifest_mismatch")
    if case == "missing_workspace":
        (runtime / "workspace").rename(runtime / "unlisted-workspace")
        expected_errors.add("missing_retained_workspace")
    before = snapshot(out.parent)
    row = reaudit.reaudit(private_root, out)[0]
    assert row == {"task_id": "unit-task", "status": "access_detected" if labels else "inconclusive",
                   "error_kinds": sorted(expected_errors), "match_labels": sorted(labels)}
    assert snapshot(out.parent) == before


def test_reaudit_keeps_all_tasks_and_errors_without_paths(finished: tuple[Path, Path, Path]) -> None:
    private, out, runtime = finished
    second_runtime = runtime.parent / "second-runtime"
    shutil.copytree(runtime, second_runtime)
    second_graders = private / "second-task"
    second_graders.mkdir()
    (second_graders / "test_second_synthetic.py").write_text("# synthetic second task\n")
    second_private = PrivateGraders.load(private, "second-task", core.REPOSITORY)
    second_audit = audit_logs([second_runtime / "exec-1.jsonl", second_runtime / "codex-home/sessions/native.jsonl"],
                             second_private, workspace=second_runtime / "workspace", repository=core.REPOSITORY,
                             grading_roots=core.audit_roots(second_runtime))
    checkpoint = out / "checkpoint.json"
    state = json.loads(checkpoint.read_text())
    state["tasks"]["second-task"] = {"phase": "finished", "runtime": str(second_runtime),
                                      "segments": [{"events": "exec-1.jsonl"}],
                                      "result": {"grader_access_audit": second_audit}}
    checkpoint.write_text(json.dumps(state))
    (out / "report.json").write_text(json.dumps({"tasks": [{"task_id": task} for task in state["tasks"]]}))
    log = runtime / "exec-1.jsonl"
    log.write_text('{"type":"unknown-one"}\n{"type":"unknown-two"}\n{"type":"turn.completed"}\n')
    before = snapshot(out.parent)
    rows = reaudit.reaudit(private, out)
    assert rows[0] == {"task_id": "second-task", "status": "clean", "error_kinds": [], "match_labels": []}
    row = rows[1]
    assert row["error_kinds"] == ["retained_log_manifest_mismatch", "unsupported_event"]
    assert set(row) == {"task_id", "status", "error_kinds", "match_labels"}
    assert snapshot(out.parent) == before


@pytest.mark.parametrize("case", ["running", "pid", "partial_report", "unsafe_task_id"])
def test_reaudit_rejects_unfinished_or_unsafe_manifest(finished: tuple[Path, Path, Path], case: str) -> None:
    private, out, _ = finished
    path = out / "checkpoint.json"
    state = json.loads(path.read_text())
    if case == "running":
        state["tasks"]["unit-task"]["phase"] = "running"
    elif case == "pid":
        state["tasks"]["unit-task"]["pid"] = 1234
    elif case == "unsafe_task_id":
        state["tasks"]["../unsafe"] = state["tasks"].pop("unit-task")
    else:
        (out / "report.json").write_text('{"tasks":[]}')
    path.write_text(json.dumps(state))
    with pytest.raises(ValueError):
        reaudit.reaudit(private, out)


def test_reaudit_unavailable_runtime_or_graders_is_sanitized(finished: tuple[Path, Path, Path]) -> None:
    private, out, _ = finished
    rows = reaudit.reaudit(private / "unavailable", out)
    assert rows == [{"task_id": "unit-task", "status": "inconclusive",
                     "error_kinds": ["reaudit_input_error"], "match_labels": []}]


def test_reaudit_manifest_error_preserves_detected_access(finished: tuple[Path, Path, Path]) -> None:
    private, out, runtime = finished
    path = out / "checkpoint.json"
    state = json.loads(path.read_text())
    state["tasks"]["unit-task"]["result"] = {}
    path.write_text(json.dumps(state))
    (runtime / "exec-1.jsonl").write_text(json.dumps({"type": "item.completed", "item": {
        "type": "command_execution", "command": "cat " + str(private / "child.txt")}}) +
        '\n{"type":"turn.completed"}\n')
    row = reaudit.reaudit(private, out)[0]
    assert row == {"task_id": "unit-task", "status": "access_detected",
                   "error_kinds": ["reaudit_input_error"], "match_labels": ["private_root", "protected_path"]}


def test_reaudit_argument_errors_do_not_echo_paths(monkeypatch: pytest.MonkeyPatch,
                                                  capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["reaudit", "--private-root", "/synthetic-private-location"])
    assert reaudit.main() == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert "/synthetic-private-location" not in captured.err
