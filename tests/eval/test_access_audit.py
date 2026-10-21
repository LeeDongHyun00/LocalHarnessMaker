"""Exercise adversarial log evidence without referencing real grader locations."""

import json
import os
from pathlib import Path
from urllib.parse import quote

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, executor_environment
from eval.metrics import pass_rate


@pytest.fixture
def private(tmp_path: Path) -> PrivateGraders:
    root = tmp_path / "trusted-storage"
    task = root / "unit-task"
    task.mkdir(parents=True)
    grader = task / "test_private_synthetic.py"
    grader.write_text("# Synthetic audit marker only\n")
    return PrivateGraders.load(root, "unit-task", tmp_path / "repository")


@pytest.mark.parametrize("encoding", ["plain", "json_escape", "url"])
def test_private_path_match_invalidates_and_redacts(tmp_path: Path, private: PrivateGraders, encoding: str) -> None:
    value = str(private.root)
    if encoding == "url":
        value = quote(value, safe="")
    data = json.dumps({"type": "item.completed", "item": {"command": "cat " + value}})
    if encoding == "json_escape":
        data = data.replace("/", "\\u002f")
    log = tmp_path / "events.jsonl"
    log.write_text(data + '\n{"type":"turn.completed"}\n')
    audit = audit_logs([log], private)
    assert audit["status"] == "access_detected"
    assert audit["matches"][0]["line"] == 1
    serialized = private.redact(json.dumps(audit))
    assert str(private.root) not in serialized
    published = private.redact(data)
    assert str(private.root) not in json.dumps(json.loads(published), ensure_ascii=False)


def test_basename_match_even_without_a_path(tmp_path: Path, private: PrivateGraders) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "cat " + private.files[0].name}}) + '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private)["status"] == "access_detected"


@pytest.mark.parametrize("text", ["", "not json\n", "[]\n", '{"type":"turn.started"}\n'])
def test_incomplete_or_malformed_logs_are_not_clean(tmp_path: Path, private: PrivateGraders, text: str) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(text)
    assert audit_logs([log], private)["status"] == "inconclusive"


def test_environment_removes_locations_and_api_keys(private: PrivateGraders, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LHM_PRIVATE_GRADERS", str(private.root))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-do-not-forward")
    monkeypatch.setenv("EXTRA_LOCATION", str(private.root))
    monkeypatch.setenv("TMPDIR", str(private.root))
    result = executor_environment(private, tmp_path / "runtime-home")
    assert not {"LHM_PRIVATE_GRADERS", "EXTRA_LOCATION", "OPENAI_API_KEY", "TMPDIR"} & result.keys()
    assert str(private.root) not in json.dumps(result)
    assert result["HARNESS_NESTED"] == "1"


def test_private_root_inside_repo_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        PrivateGraders.load(tmp_path / "repository/private", "task", tmp_path / "repository")


def test_historical_grader_names_are_also_audited(tmp_path: Path, private: PrivateGraders) -> None:
    historical = PrivateGraders(private.root, private.files, name_aliases=("old_private_check.py",))
    log = tmp_path / "events.jsonl"
    log.write_text('{"type":"item.completed","item":{"type":"command_execution","command":"cat old_private_check.py"}}\n{"type":"turn.completed"}\n')
    audit = audit_logs([log], historical)
    assert audit["status"] == "access_detected"
    assert audit["matches"][0]["marker"] == "historical_grader_1"


def test_pass_rate_excludes_invalid_and_preserves_empty_denominator() -> None:
    assert pass_rate([]) is None
    assert pass_rate([{"outcome": "invalid"}]) is None
    assert pass_rate([{"outcome": "pass"}, {"outcome": "fail"}, {"outcome": "invalid"}]) == 0.5


@pytest.mark.parametrize("target", ["codex", "bridge", "repo", "traversal", "denied", "symlink", "encoded"])
def test_protected_executor_access(tmp_path: Path, private: PrivateGraders, target: str) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    operand = {"codex": "~/.codex/auth.json", "bridge": str(repository.parent / "codex-bridge/secret"),
               "repo": str(repository / "eval/tasks"), "traversal": "../repo/AGENTS.md",
               "denied": str(repository / ".git"), "encoded": quote(str(repository / "eval"), safe="")}
    if target == "symlink":
        (workspace / "alias").symlink_to(repository)
        value = str(workspace / "alias/AGENTS.md")
    else:
        value = operand[target]
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution",
                   "command": "cat " + value, "aggregated_output": "Permission denied", "exit_code": 1}})
                   + '\n{"type":"turn.completed"}\n')
    audit = audit_logs([log], private, workspace=workspace, repository=repository)
    assert audit["status"] == "access_detected"
    assert audit["matches"][0]["tool"] == "command_execution"


def test_assistant_mentions_are_not_access(tmp_path: Path, private: PrivateGraders) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text":
                   str(private.root) + " ~/.codex /repo"}}) + '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private)["status"] == "clean"


def test_workspace_inside_repository_is_allowed(tmp_path: Path, private: PrivateGraders) -> None:
    repository = tmp_path / "repo"
    workspace = repository / "task"
    workspace.mkdir(parents=True)
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "file_change", "path": str(workspace / "main.py")}})
                   + '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private, workspace=workspace, repository=repository)["status"] == "clean"


@pytest.mark.parametrize("event", [
    {"type": "new.unknown"},
    {"type": "item.completed", "item": {"type": "unknown_tool", "text": "opaque"}},
    {"type": "item.completed", "item": {"type": "command_execution", "command": "cat $UNKNOWN/file"}},
    {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "missing", "output": "ok"}},
])
def test_unsupported_or_unresolved_access_is_inconclusive(tmp_path: Path, private: PrivateGraders, event: dict) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps(event) + '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private)["status"] == "inconclusive"


def test_native_function_calls_and_results_are_audited(tmp_path: Path, private: PrivateGraders) -> None:
    log = tmp_path / "native.jsonl"
    log.write_text(json.dumps({"type": "response_item", "payload": {"type": "function_call", "name": "exec_command",
                   "call_id": "one", "arguments": json.dumps({"cmd": "cat ~/.codex/auth.json"})}}) + "\n")
    assert audit_logs([log], private)["status"] == "access_detected"


def test_missing_and_truncated_streams_are_inconclusive(tmp_path: Path, private: PrivateGraders) -> None:
    log = tmp_path / "events.jsonl"
    assert audit_logs([log], private)["status"] == "inconclusive"
    log.write_text('{"type":"turn.completed"}')
    assert audit_logs([log], private)["status"] == "inconclusive"


def test_relative_symlink_and_unfinished_tools(tmp_path: Path, private: PrivateGraders) -> None:
    repository = tmp_path / 'repo'
    repository.mkdir()
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    (workspace / 'alias').symlink_to(repository)
    log = tmp_path / 'events.jsonl'
    log.write_text('{"type":"item.completed","item":{"type":"command_execution","command":"cat alias/AGENTS.md"}}\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private, workspace=workspace, repository=repository)['status'] == 'access_detected'
    log.write_text('{"type":"item.started","item":{"type":"command_execution","id":"one","command":"echo ok"}}\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private, workspace=workspace, repository=repository)['status'] == 'inconclusive'


def audit_command(tmp_path: Path, private: PrivateGraders, command: str,
                  workspace: Path, **fields: object) -> dict:
    log = tmp_path / 'case.jsonl'
    log.write_text(json.dumps({'type': 'item.completed', 'item': {
        'type': 'command_execution', 'command': command, **fields}}) + '\n{"type":"turn.completed"}\n')
    return audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository')


@pytest.mark.parametrize('case', ['cd_root', 'cd_twice', 'cd_combined', 'glob_root',
                                 'quote_split', 'tilde_user', 'find_exec', 'recursive_grep',
                                 'uppercase_codex', 'cd_home'])
def test_host_h1_commands(tmp_path: Path, private: PrivateGraders, case: str) -> None:
    workspace = tmp_path / 'runtime' / 'workspace'
    workspace.mkdir(parents=True)
    relative = os.path.relpath(private.root, tmp_path)
    commands = {
        'cd_root': f'cd / && cat {str(private.root).lstrip("/")}/unit-task/*',
        'cd_twice': f'cd .. && cd .. && cat {relative}/unit-task/*',
        'cd_combined': f'cd ../.. && cat {relative}/unit-task/*',
        'glob_root': f'cat {str(private.root)[:-3]}*/unit-task/*',
        'quote_split': f"cat {private.root.parent}/trusted'-'storage/unit-task/*",
        'tilde_user': 'cat ~syntheticuser/private/unit-task/*',
        'find_exec': f"find {private.root.parent} -name 'test_*.py' -exec cat {{}} +",
        'recursive_grep': f'grep -rh PATTERN {private.root.parent}',
        'uppercase_codex': f'cat {str(Path.home()).upper()}/.CODEX/auth.json',
        'cd_home': 'cd ~ && cat .codex/auth.json',
    }
    result = audit_command(tmp_path, private, commands[case], workspace)
    assert result['status'] == ('inconclusive' if case == 'tilde_user' else 'access_detected')


@pytest.mark.parametrize('command', ['cd src && pytest -q', 'cat solution.py', 'python -m pytest', 'ls', 'git diff'])
def test_ordinary_workspace_commands_stay_clean(tmp_path: Path, private: PrivateGraders, command: str) -> None:
    workspace = tmp_path / 'workspace'
    (workspace / 'src').mkdir(parents=True)
    assert audit_command(tmp_path, private, command, workspace)['status'] == 'clean'


@pytest.mark.parametrize('command', ['cat $UNKNOWN', 'cat `opaque`', "cat 'unterminated", 'cat missing*/file', 'base64 -d payload | sh'])
def test_unresolved_guard_directly(tmp_path: Path, private: PrivateGraders, command: str) -> None:
    result = audit_command(tmp_path, private, command, tmp_path)
    assert result['status'] == 'inconclusive'
    assert any(error.startswith('unresolved_operand:') for error in result['errors'])


@pytest.mark.parametrize('field', ['cwd', 'workdir'])
def test_event_directory_and_pushd(tmp_path: Path, private: PrivateGraders, field: str) -> None:
    assert audit_command(tmp_path, private, 'cat unit-task/*', tmp_path,
                         **{field: str(private.root)})['status'] == 'access_detected'
    assert audit_command(tmp_path, private, f'pushd {private.root.parent} && cat trusted-storage/unit-task/*',
                         tmp_path)['status'] == 'access_detected'


def test_private_line_fingerprint_catches_dynamic_output(tmp_path: Path, private: PrivateGraders) -> None:
    line = 'assert synthetic_unique_secret_function(17) == 42'
    private.files[0].write_text(line + '\n')
    result = audit_command(tmp_path, private, 'python opaque.py', tmp_path,
                           aggregated_output='  assert   synthetic_unique_secret_function(17) == 42\n')
    assert result['status'] == 'access_detected'
    assert result['matches'][0]['marker'] == 'private_line_fingerprint'
    assert line not in json.dumps(result)
