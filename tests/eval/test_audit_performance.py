"""Bound audit work using synthetic corpora and large native tool payloads."""

import ast
import json
from pathlib import Path
import time
from typing import Any

import pytest

from eval.runner.audit import FingerprintCache, PrivateGraders, audit_logs, digest


def test_task_only_fingerprints_ignore_5000_quarantine_copies(tmp_path: Path,
                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "trusted"
    repository = tmp_path / "repository"
    sources = [f'assert synthetic_check("hidden-example-{index:04}") == {9876540 + index}\n'
               for index in range(12)]
    for index in range(120):
        task = root / f"task-{index:03}"
        task.mkdir(parents=True)
        (task / "test_private_synthetic.py").write_text(sources[index % len(sources)])
    private = PrivateGraders.load(root, "task-000", repository)
    expected = {digest(source.strip().encode()) for source in sources}
    assert private.line_fingerprints() == expected
    for index in range(5000):
        copy = root / ".quarantine" / f"copy-{index:04}"
        copy.mkdir(parents=True)
        (copy / "test_solution.py").write_text(sources[index % len(sources)])
    for directory in (".quarantine", ".references", ".bridge-logs", ".arbitrary"):
        (root / directory).mkdir(exist_ok=True)
        (root / directory / "test_reference.py").write_text('assert check("not-a-grader-953871")\n')
    (root / "test_root.py").write_text("invalid root-level Python: never parse\n")
    nested = root / "task-000/nested"
    nested.mkdir()
    (nested / "test_nested.py").write_text("invalid nested Python: never parse\n")
    (root / "visible-alias").symlink_to(root / ".references", target_is_directory=True)
    alias_task = root / "alias-task"
    alias_task.mkdir()
    (alias_task / "test_alias.py").symlink_to(root / ".references/test_reference.py")

    parsed: list[str] = []
    original_parse, original_read = ast.parse, Path.read_bytes

    def counted_parse(source: str, *args: Any, **kwargs: Any) -> ast.AST:
        parsed.append(source)
        return original_parse(source, *args, **kwargs)

    def no_dot_reads(path: Path) -> bytes:
        assert not any(part.startswith(".") for part in path.relative_to(root).parts)
        return original_read(path)

    monkeypatch.setattr(ast, "parse", counted_parse)
    monkeypatch.setattr(Path, "read_bytes", no_dot_reads)
    cache = FingerprintCache()
    start = time.monotonic()
    # One invocation shares analysis across all 120 tasks, despite distinct
    # PrivateGraders instances and per-task manifests.
    for index in range(120):
        task_private = PrivateGraders.load(root, f"task-{index:03}", repository)
        assert task_private.line_fingerprints(cache) == expected
    assert len(parsed) == len(set(parsed)) == len(sources)
    elapsed = time.monotonic() - start
    assert elapsed < 5, f"Task-only fingerprint analysis took {elapsed:.3f}s"

    # Excluding dot content must never weaken protection of paths under it.
    log = root / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution",
        "command": "cat " + str(root / ".quarantine/copy-0000/test_solution.py")}}) +
        '\n{"type":"turn.completed"}\n')
    result = audit_logs([log], private, workspace=tmp_path, repository=repository, fingerprint_cache=cache)
    assert result["status"] == "access_detected"
    assert len(parsed) == len(sources)


def test_fingerprint_cache_is_scoped_to_one_invocation(tmp_path: Path) -> None:
    task = tmp_path / "trusted/task"
    task.mkdir(parents=True)
    grader = task / "test_private_synthetic.py"
    grader.write_text('assert check("first-hidden-example-678431")\n')
    private = PrivateGraders.load(task.parent, task.name, tmp_path / "repository")
    cache = FingerprintCache()
    before = private.line_fingerprints(cache)
    private.line_fingerprints(cache).clear()  # Callers cannot mutate the snapshot.
    assert private.line_fingerprints(cache) == before
    grader.write_text('assert check("second-hidden-example-983175")\n')
    assert private.line_fingerprints(cache) == before
    assert private.line_fingerprints(FingerprintCache()) != before
    assert private.line_fingerprints() != before


@pytest.mark.parametrize("shape", ["large_patch", "large_command", "many_calls", "malformed_literal"])
def test_large_code_mode_and_file_change_are_bounded(tmp_path: Path, shape: str) -> None:
    task = tmp_path / "trusted/task"
    task.mkdir(parents=True)
    (task / "test_private_synthetic.py").write_text("# Synthetic grader\n")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    private = PrivateGraders.load(task.parent, task.name, tmp_path / "repository")
    if shape == "large_patch":
        patch = ("*** Begin Patch\n*** Add File: own.py\n+# " + "x" * 200_000 +
                 " $ `quoted`\n*** End Patch")
        code = 'text(await tools.apply_patch(' + json.dumps(patch) + '));\n'
        code += 'text(await tools.exec_command({cmd:"python -m unittest discover -v"}));'
    elif shape == "large_command":
        # A long flag is not a path. An unbounded path regex used to retry
        # its slash-free suffix at every position.
        code = 'text(await tools.exec_command({cmd:' + json.dumps("python --data=" + "x" * 200_000) + '}));'
    elif shape == "many_calls":
        code = 'text(await tools.exec_command({cmd:"python -m unittest discover -v"}));\n' * 3000
    else:
        code = 'text(await tools.exec_command({cmd:"' + "x" * 200_000
    assert len(code.encode()) >= 200_000
    content = ("$ `backticks` 'single' \"double\" " * 40_000)[:1_000_000]
    assert len(content.encode()) == 1_000_000
    events = [{"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec",
               "call_id": "synthetic", "input": code}},
              {"type": "event_msg", "payload": {"type": "item_completed", "item": {
                  "type": "FileChange", "changes": {str(workspace / "own.py"): {
                      "type": "add", "content": content}}}}},
              {"type": "response_item", "payload": {"type": "custom_tool_call_output",
               "call_id": "synthetic", "output": "Success"}}]
    log = tmp_path / "large-native.jsonl"
    log.write_text("".join(json.dumps(event) + "\n" for event in events))
    start = time.monotonic()
    result = audit_logs([log], private, workspace=workspace, repository=tmp_path / "repository")
    elapsed = time.monotonic() - start
    assert result["status"] == ("inconclusive" if shape == "malformed_literal" else "clean"), result
    assert elapsed < 5, f"Large {shape} audit took {elapsed:.3f}s"


@pytest.mark.parametrize("task_id", [".quarantine", "task/nested", "../task"])
def test_private_load_rejects_non_task_directory(tmp_path: Path, task_id: str) -> None:
    root = tmp_path / "trusted"
    (root / task_id).mkdir(parents=True)
    (root / task_id / "test_fake.py").write_text("# Not a task grader\n")
    with pytest.raises(ValueError, match="Private task graders are unavailable"):
        PrivateGraders.load(root, task_id, tmp_path / "repository")
