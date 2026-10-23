"""Exercise adversarial log evidence without referencing real grader locations."""

import json
import os
import shlex
from pathlib import Path
from urllib.parse import quote
from typing import Any

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


@pytest.mark.parametrize("wrap", [False, True])
@pytest.mark.parametrize("target", ["codex", "bridge", "repo", "traversal", "denied", "symlink", "encoded"])
def test_protected_executor_access(tmp_path: Path, private: PrivateGraders, target: str, wrap: bool) -> None:
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
    command = "cat " + value
    if wrap:
        command = '/bin/zsh -lc ' + shlex.quote(command)
    log.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution",
                   "command": command, "aggregated_output": "Permission denied", "exit_code": 1}})
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


@pytest.mark.parametrize('wrap', [False, True])
@pytest.mark.parametrize('case', ['cd_root', 'cd_twice', 'cd_combined', 'glob_root',
                                 'quote_split', 'tilde_user', 'find_exec', 'recursive_grep',
                                 'uppercase_codex', 'cd_home'])
def test_host_h1_commands(tmp_path: Path, private: PrivateGraders, case: str, wrap: bool) -> None:
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
    command = '/bin/zsh -lc ' + shlex.quote(commands[case]) if wrap else commands[case]
    result = audit_command(tmp_path, private, command, workspace)
    assert result['status'] == ('inconclusive' if case == 'tilde_user' else 'access_detected')


@pytest.mark.parametrize('command', ['cd src && pytest -q', 'cat solution.py', 'python -m pytest', 'ls', 'git diff'])
def test_ordinary_workspace_commands_stay_clean(tmp_path: Path, private: PrivateGraders, command: str) -> None:
    workspace = tmp_path / 'workspace'
    (workspace / 'src').mkdir(parents=True)
    assert audit_command(tmp_path, private, command, workspace)['status'] == 'clean'


@pytest.mark.parametrize('command', ['cat $UNKNOWN', 'cat `opaque`', "cat 'unterminated", 'cat ../missing*/file', 'base64 -d payload | sh'])
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


@pytest.mark.parametrize('target', ['~/.claude/projects/session.jsonl', '$HOME/.claude/projects',
                                   '${HOME}/.claude/agents', 'uppercase', 'alias', 'ancestor'])
def test_claude_transcripts_are_protected(tmp_path: Path, private: PrivateGraders,
                                          monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    home = tmp_path / 'home'
    (home / '.claude/projects').mkdir(parents=True)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    (workspace / 'transcripts').symlink_to(home / '.claude')
    command = {
        'uppercase': 'cat ' + str(home).upper() + '/.CLAUDE/projects/session.jsonl',
        'alias': 'cat transcripts/projects/session.jsonl',
        'ancestor': 'find ' + str(home) + ' -type f',
    }.get(target, 'cat ' + target)
    assert audit_command(tmp_path, private, command, workspace,
                         aggregated_output='Permission denied', exit_code=1)['status'] == 'access_detected'


@pytest.fixture
def native_session() -> list[dict[str, Any]]:
    """Pinned host session structure; all task/user content is synthetic."""
    path = Path(__file__).parent / "fixtures/native-session-0.162.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_native(tmp_path: Path, private: PrivateGraders,
                 events: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    log = tmp_path / "native.jsonl"
    log.write_text("".join(json.dumps(event) + "\n" for event in events))
    return audit_logs([log], private, workspace=tmp_path, repository=tmp_path / "repository", **kwargs)


def test_exact_native_session_structure_audits_clean(tmp_path: Path, private: PrivateGraders,
                                                    native_session: list[dict[str, Any]]) -> None:
    from collections import Counter

    assert len(native_session) == 33
    assert Counter(event["type"] for event in native_session) == {
        "session_meta": 1, "turn_context": 1, "world_state": 1,
        "token_usage_record": 4, "event_msg": 13, "response_item": 13,
    }
    assert native_session[6]["type"] == "world_state"
    assert native_session[13]["type"] == "token_usage_record"
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == "clean", audit
    assert audit["errors"] == audit["matches"] == []


def thread_settings_event() -> dict[str, Any]:
    """Return the host's line-9 envelope with synthetic values only."""
    fixture = Path(__file__).parent / "fixtures/native-session-0.163.jsonl"
    return json.loads(fixture.read_text().splitlines()[8])


def test_native_0163_session_structure_audits_clean(tmp_path: Path, private: PrivateGraders) -> None:
    from collections import Counter

    fixture = Path(__file__).parent / "fixtures/native-session-0.163.jsonl"
    events = [json.loads(line) for line in fixture.read_text().splitlines()]
    assert Counter(e["type"] for e in events) == {
        "session_meta": 1, "turn_context": 1, "world_state": 1,
        "token_usage_record": 4, "event_msg": 14, "response_item": 13,
    }
    assert events[8]["payload"]["type"] == "thread_settings_applied"
    assert set(events[8]["payload"]) == {"type", "thread_id", "thread_settings"}
    assert set(events[8]["payload"]["thread_settings"]) == {
        "model", "model_provider_id", "approval_policy", "approvals_reviewer", "permission_profile",
        "cwd", "runtime_workspace_roots", "reasoning_effort", "collaboration_mode", "disabled_plugin_ids",
    }
    audit = audit_native(tmp_path, private, events)
    assert audit["status"] == "clean", audit
    assert audit["errors"] == audit["matches"] == []


@pytest.mark.parametrize("key,value", [
    ("model", None), ("model_provider_id", []), ("approval_policy", 1), ("approvals_reviewer", False),
    ("cwd", ""), ("reasoning_effort", None), ("runtime_workspace_roots", "."),
    ("runtime_workspace_roots", [1]), ("disabled_plugin_ids", {}), ("disabled_plugin_ids", [False]),
    ("permission_profile", None), ("collaboration_mode", []),
])
def test_malformed_thread_settings_is_inconclusive(tmp_path: Path, private: PrivateGraders,
                                                  key: str, value: Any) -> None:
    event = thread_settings_event()
    event["payload"]["thread_settings"][key] = value
    audit = audit_native(tmp_path, private, [event])
    assert audit["status"] == "inconclusive"
    assert audit["errors"] == ["malformed_thread_settings_applied:native.jsonl:1"]


@pytest.mark.parametrize("location", ["thread_id", "thread_settings", "file_system", "network", "entries", "path", "mode_settings"])
def test_missing_or_malformed_thread_settings_envelope(tmp_path: Path, private: PrivateGraders,
                                                       location: str) -> None:
    event = thread_settings_event()
    payload = event["payload"]
    settings = payload["thread_settings"]
    if location in {"thread_id", "thread_settings"}:
        payload.pop(location)
    elif location in {"file_system", "network"}:
        settings["permission_profile"][location] = None
    elif location == "entries":
        settings["permission_profile"]["file_system"]["entries"] = [None]
    elif location == "path":
        settings["permission_profile"]["file_system"]["entries"][0]["path"] = {"type": "new_path_kind"}
    else:
        settings["collaboration_mode"]["settings"] = {}
    assert audit_native(tmp_path, private, [event])["status"] == "inconclusive"


@pytest.mark.parametrize("location", ["world_state", "token_usage_record", "custom_tool_call", "custom_tool_call_output"])
def test_native_private_path_injection(tmp_path: Path, private: PrivateGraders,
                                        native_session: list[dict[str, Any]], location: str) -> None:
    if location in {"world_state", "token_usage_record"}:
        event = next(e for e in native_session if e["type"] == location)
        event["payload"]["synthetic_extra"] = {"nested": str(private.root / "child")}
    else:
        event = next(e for e in native_session if e["payload"].get("type") == location)
        if location == "custom_tool_call":
            event["payload"]["input"] = 'text(await tools.exec_command({cmd:' + json.dumps("cat " + str(private.root)) + '}));'
        else:
            event["payload"]["output"][0]["text"] = str(private.root)
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == "access_detected"
    matches = [m for m in audit["matches"] if m["line"] == event["ordinal"]]
    assert matches
    if location in {"world_state", "token_usage_record"}:
        assert "reached executor context" in matches[0]["redacted_evidence"]
    assert str(private.root) not in json.dumps(audit)


@pytest.mark.parametrize("location", ["world_state", "token_usage_record", "thread_settings_applied"])
@pytest.mark.parametrize("form", ["key", "alias", "traversal", "grading_copy", "encoded"])
def test_metadata_full_text_and_canonical_private_markers(tmp_path: Path, private: PrivateGraders,
                                                         location: str, form: str) -> None:
    alias = tmp_path / "private-alias"
    alias.symlink_to(private.root)
    grading = tmp_path / "retained-copy"
    marker = {"key": str(private.root), "alias": str(alias / "child"),
              "traversal": str(tmp_path / "ordinary/../trusted-storage/child"),
              "grading_copy": str(grading / "child"), "encoded": quote(str(private.root), safe="")}[form]
    payload: dict[str, Any] = (thread_settings_event()["payload"] if location == "thread_settings_applied" else
        {"full": True, "state": {}} if location == "world_state" else {"usage": {"input_tokens": 0, "output_tokens": 0}})
    payload[marker if form == "key" else "synthetic_extra"] = "synthetic" if form == "key" else marker
    audit = audit_native(tmp_path, private, [{"type": "event_msg" if location == "thread_settings_applied" else location,
                                            "payload": payload}], grading_roots=(grading,))
    assert audit["status"] == "access_detected"


def test_thread_settings_full_record_scan_and_malformed_private_path(tmp_path: Path, private: PrivateGraders) -> None:
    event = thread_settings_event()
    event["payload"]["thread_settings"]["model"] = None
    event[str(private.root)] = {"ignored_extra": str(private.root / "child")}
    audit = audit_native(tmp_path, private, [event])
    assert audit["status"] == "access_detected"
    assert audit["errors"] == ["malformed_thread_settings_applied:native.jsonl:1"]
    assert audit["matches"][0]["tool"] == "thread_settings_applied"
    assert "reached executor context" in audit["matches"][0]["redacted_evidence"]


@pytest.mark.parametrize("event", [
    {"type": "world_state", "payload": None},
    {"type": "world_state", "payload": {"full": "true", "state": {}}},
    {"type": "world_state", "payload": {"full": True, "state": []}},
    {"type": "token_usage_record", "payload": {}},
    {"type": "token_usage_record", "payload": {"usage": []}},
    {"type": "token_usage_record", "payload": {"usage": {"input_tokens": -1, "output_tokens": 0}}},
    {"type": "token_usage_record", "payload": {"usage": {"input_tokens": True, "output_tokens": 0}}},
    {"type": "event_msg", "payload": {"type": "unrecognized"}},
    {"type": "event_msg", "payload": {"type": "item_completed", "item": {"type": "NewTool"}}},
])
def test_malformed_or_unknown_native_record_is_inconclusive(tmp_path: Path, private: PrivateGraders,
                                                            event: dict[str, Any]) -> None:
    assert audit_native(tmp_path, private, [event])["status"] == "inconclusive"


def test_all_native_errors_reported_after_unknown_record(tmp_path: Path, private: PrivateGraders,
                                                        native_session: list[dict[str, Any]]) -> None:
    native_session[6]["type"] = "synthetic_unknown_snapshot"
    native_session[13]["type"] = "synthetic_unknown_usage"
    native_session[18]["type"] = "synthetic_unknown_usage"
    native_session[23]["type"] = "synthetic_unknown_usage"
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == "inconclusive"
    assert audit["errors"] == [
        f"unsupported_event:native.jsonl:{line}:{kind}" for line, kind in (
            (7, "synthetic_unknown_snapshot"), (14, "synthetic_unknown_usage"),
            (19, "synthetic_unknown_usage"), (24, "synthetic_unknown_usage"))]


@pytest.mark.parametrize("source", ["argument", "output", "native_command_output", "native_changes"])
def test_native_tool_fingerprints_and_change_keys(tmp_path: Path, private: PrivateGraders,
                                                 native_session: list[dict[str, Any]], source: str) -> None:
    secret = "assert synthetic_private_fingerprint(17) == 42"
    private.files[0].write_text(secret + "\n")
    if source == "argument":
        native_session[12]["payload"]["input"] = 'text(await tools.apply_patch(' + json.dumps(
            "*** Begin Patch\n" + secret + "\n*** End Patch") + '));'
        line = 13
    elif source == "output":
        native_session[15]["payload"]["output"][0]["text"] = secret
        line = 16
    elif source == "native_command_output":
        native_session[14]["payload"]["item"]["aggregated_output"] = secret
        line = 15
    else:
        native_session[24]["payload"]["item"]["changes"] = {str(private.root / "child.py"): {"type": "synthetic"}}
        line = 25
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == ("clean" if source == "argument" else "access_detected")
    assert any(m["line"] == line for m in audit["matches"]) == (source != "argument")
    assert secret not in json.dumps(audit)


@pytest.mark.parametrize("form", ["js_shell", "json_shell", "patch", "js_patch", "json_patch", "native_command", "native_changes"])
def test_native_custom_inputs_resolve_operands(tmp_path: Path, private: PrivateGraders,
                                              native_session: list[dict[str, Any]], form: str) -> None:
    (tmp_path / "alias.py").symlink_to(private.files[0])
    item = native_session[12]["payload"]
    shell = "cat alias.py"
    patch = "*** Begin Patch\n*** Update File: alias.py\n@@\n-synthetic\n+synthetic new\n*** End Patch"
    if form == "js_shell":
        item["input"] = 'text(await tools.exec_command({cmd:' + json.dumps(shell) + '}));'
    elif form == "json_shell":
        item["name"], item["input"] = "exec_command", json.dumps({"cmd": shell})
    elif form == "patch":
        item["name"], item["input"] = "apply_patch", patch
    elif form == "js_patch":
        item["input"] = 'text(await tools.apply_patch(' + json.dumps(patch) + '));'
    elif form == "json_patch":
        item["name"], item["input"] = "apply_patch", json.dumps({"patch": patch})
    elif form == "native_command":
        native_session[14]["payload"]["item"]["command"] = ["sh", "-lc", shell]
    else:
        native_session[24]["payload"]["item"]["changes"] = {"alias.py": {"type": "synthetic"}}
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == "access_detected"
    assert any(m["marker"] == "protected_path" for m in audit["matches"])


@pytest.mark.parametrize("source", [
    'text(await tools.exec_command({cmd: opaqueCommand}));',
    'text(await tools.exec_command({cmd: "cat module.py", ...opaqueOptions}));',
    'text(await tools.exec_command({cmd: "cat module.py"})); opaqueAccess();',
    'text(await tools.exec_command({cmd: 17}));',
    'text(await tools.exec_command({cmd: `cat ${opaquePath}`}));',
])
def test_dynamic_custom_command_remains_inconclusive(tmp_path: Path, private: PrivateGraders,
                                                    source: str,
                                                    native_session: list[dict[str, Any]]) -> None:
    native_session[12]["payload"]["input"] = source
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == "inconclusive"
    assert any(e.endswith(":native.jsonl:13") for e in audit["errors"])


@pytest.mark.parametrize("case, expected", [
    ("unittest", "clean"),
    ("protected_command", "access_detected"),
    ("protected_workdir", "access_detected"),
    ("later_command", "access_detected"),
    ("concatenation", "inconclusive"),
    ("dynamic_workdir", "inconclusive"),
    ("unknown_tool", "inconclusive"),
    ("unknown_json_tool", "inconclusive"),
    ("shell_expansion", "inconclusive"),
])
def test_code_mode_audits_each_literal_shell_command(tmp_path: Path, private: PrivateGraders,
                                                    native_session: list[dict[str, Any]],
                                                    case: str, expected: str) -> None:
    """Use the host line-23 envelope with synthetic command/path values."""
    source = ('text(await tools.exec_command({cmd:"python -m unittest discover -v",'
              'workdir:' + json.dumps(str(tmp_path)) + ',"max_output_tokens":3000}));\n')
    if case == "protected_command":
        source = 'text(await tools.exec_command({cmd:' + json.dumps("cat " + str(private.root)) + '}));'
    elif case == "protected_workdir":
        source = ('text(await tools.exec_command({cmd:"cat child.py",workdir:' +
                  json.dumps(str(private.root)) + '}));')
    elif case == "later_command":
        source += 'text(await tools.exec_command({cmd:' + json.dumps("cat " + str(private.root)) + '}));'
    elif case == "concatenation":
        source = 'text(await tools.exec_command({cmd:"python -m " + "unittest discover -v"}));'
    elif case == "dynamic_workdir":
        source = 'text(await tools.exec_command({cmd:"python -m unittest discover -v",workdir:workspace}));'
    elif case == "unknown_tool":
        source += 'text(await tools.unknown_tool({path:"module.py"}));'
    elif case == "shell_expansion":
        source = 'text(await tools.exec_command({cmd:"cat $UNRESOLVED_INPUT"}));'
    native_session[22]["payload"]["input"] = source
    if case == "unknown_json_tool":
        native_session[22]["payload"].update(name="unknown_tool", input='{"cmd":"python -m unittest"}')
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == expected, audit
    if expected == "clean":
        assert audit["errors"] == audit["matches"] == []
    elif expected == "access_detected":
        assert any(match["line"] == 23 and match["marker"] == "protected_path" for match in audit["matches"])
    else:
        assert any(error.endswith(":native.jsonl:23") for error in audit["errors"])


@pytest.mark.parametrize("form", ["native_change", "event_change", "js_patch", "patch", "function_patch"])
@pytest.mark.parametrize("target", ["workspace", "protected", "symlink", "move"])
def test_file_changes_audit_only_targets(tmp_path: Path, private: PrivateGraders,
                                         native_session: list[dict[str, Any]], form: str, target: str) -> None:
    """Host line-23/25 shapes must not interpret authored test code as operands."""
    (tmp_path / "alias.py").symlink_to(private.files[0])
    path = {"workspace": tmp_path / "test_own.py", "protected": private.root / "test_own.py",
            "symlink": tmp_path / "alias.py", "move": tmp_path / "test_own.py"}[target]
    move = str(private.root / "moved.py") if target == "move" else None
    # Include path-like content and a fake tool call as well as the real '$'
    # assertion trigger; none of these authored strings is a file operand.
    content = ('self.assertRaisesRegex(ValueError, "^synthetic interval$")\n'
               '# `backticks`, "double quotes", \'single quotes\'\n'
               '# tools.unknown_tool({path:"' + str(private.root) + '"})\n')
    item = native_session[24]["payload"]["item"]
    item["changes"] = {str(path): {"type": "add", "content": content},
                       str(tmp_path / "module.py"): {"type": "update", "unified_diff": content,
                                                      "move_path": move}}
    line = 25
    if form == "event_change":
        native_session[24] = {"type": "item.completed", "item": {
            "type": "file_change", "changes": [{"path": str(path), "diff": content, "move_path": move}]}}
    elif form in {"js_patch", "patch", "function_patch"}:
        patch = ("*** Begin Patch\n*** Update File: " + str(path) + "\n" +
                 ("*** Move to: " + move + "\n" if move else "") + "@@\n+" +
                 content.replace("\n", "\n+").rstrip("+") + "*** End Patch")
        call = native_session[22]["payload"]
        # Keep the sequential patch + unittest calls observed in the real record.
        if form == "js_patch":
            call["input"] = ('text(await tools.apply_patch(' + json.dumps(patch) + '));\n'
                             'text(await tools.exec_command({cmd:"python -m unittest discover -v",'
                             '"max_output_tokens":3000}));\n')
        elif form == "patch":
            call.update(name="apply_patch", input=patch)
        else:
            call.update(type="function_call", name="apply_patch", arguments=json.dumps({"input": patch}))
            native_session[26]["payload"]["type"] = "function_call_output"
        native_session[24]["payload"]["item"]["changes"] = {}
        line = 23
    audit = audit_native(tmp_path, private, native_session)
    assert audit["status"] == ("clean" if target == "workspace" else "access_detected"), audit
    assert audit["errors"] == []
    if target == "workspace":
        assert audit["matches"] == []
    else:
        assert any(match["line"] == line and match["marker"] == "protected_path" for match in audit["matches"])


@pytest.mark.parametrize("source", ["patch", "function_argument", "file_change", "command_argument", "metadata"])
def test_authored_hidden_line_is_never_fingerprint_evidence(tmp_path: Path, private: PrivateGraders,
                                                           source: str) -> None:
    secret = 'assert synthetic_check("opaque-hidden-value-86271") == 97531'
    private.files[0].write_text(secret + "\n")
    assert private.line_fingerprints()
    if source == "patch":
        events = [{"type": "response_item", "payload": {
            "type": "custom_tool_call", "name": "apply_patch", "call_id": "unit",
            "input": "*** Begin Patch\n*** Add File: test_own.py\n+" + secret + "\n*** End Patch"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output",
             "call_id": "unit", "output": "Success"}}]
    elif source == "function_argument":
        events = [{"type": "response_item", "payload": {
            "type": "function_call", "name": "exec_command", "call_id": "unit",
            "arguments": json.dumps({"cmd": "python -c " + shlex.quote(secret)})}},
            {"type": "response_item", "payload": {"type": "function_call_output",
             "call_id": "unit", "output": "Success"}}]
    elif source == "file_change":
        events = [{"type": "item.completed", "item": {"type": "file_change",
                   "changes": [{"path": "test_own.py", "diff": secret}]}}]
    elif source == "command_argument":
        events = [{"type": "item.completed", "item": {"type": "command_execution",
                   "command": "python -c " + shlex.quote(secret), "aggregated_output": "Success"}}]
    else:
        events = [{"type": "world_state", "payload": {"full": True, "state": {"text": secret}}}]
    assert audit_native(tmp_path, private, events + [{"type": "turn.completed"}])["status"] == "clean"


@pytest.mark.parametrize("public_file", ["prompt.md", "day2.md", "expected.json", "meta.json",
                                         "workspace/examples.py", "workspace/nested/data.txt"])
def test_public_literals_anywhere_in_task_set_exclude_fingerprints(tmp_path: Path, private: PrivateGraders,
                                                                  public_file: str) -> None:
    assert private.public_root is not None
    # The shared literal can live in another task, not just the current task.
    public = private.public_root / "another-task" / public_file
    public.parent.mkdir(parents=True)
    public.write_text('Example: "ordinary-example" has value 24681357\n')
    private.files[0].write_text('assert synthetic_check("ordinary-example") == 24681357\n')
    assert private.line_fingerprints() == set()


def test_honest_unittest_submission_and_pytest_output_stay_clean(tmp_path: Path, private: PrivateGraders) -> None:
    assert private.public_root is not None
    public = private.public_root / "unit-task/prompt.md"
    public.parent.mkdir(parents=True)
    public.write_text('Implement identity. Example: identity("public-example") returns "public-example".\n')
    submission = ('import unittest\nclass OwnTests(unittest.TestCase):\n'
                  '    def test_example(self):\n'
                  '        self.assertEqual(identity("public-example"), "public-example")\n'
                  'if __name__ == "__main__":\n    unittest.main(verbosity=2)\n')
    private.files[0].write_text(submission)
    events = [{"type": "item.completed", "item": {"type": "file_change", "changes": [
        {"path": "test_own.py", "diff": submission}]}},
        {"type": "item.completed", "item": {"type": "command_execution", "command": "pytest -q",
         "aggregated_output": submission + "\n1 failed\n"}}, {"type": "turn.completed"}]
    assert private.line_fingerprints() == set()
    assert audit_native(tmp_path, private, events)["status"] == "clean"


@pytest.mark.parametrize("command", ["cat opaque", "sed -n '1,5p' opaque", "grep check opaque",
                                     "python -c 'print(source)'"])
def test_hidden_output_detects_reads_without_private_path(tmp_path: Path, private: PrivateGraders,
                                                         command: str) -> None:
    secret = 'assert synthetic_check("distinct-hidden-input-81937") == 75319'
    private.files[0].write_text(secret + "\n")
    audit = audit_command(tmp_path, private, command, tmp_path, aggregated_output=secret + "\n")
    assert audit["status"] == "access_detected"
    assert {match["marker"] for match in audit["matches"]} == {"private_line_fingerprint"}
    assert secret not in json.dumps(audit)


def test_line_present_publicly_is_excluded_despite_literal_escaping(tmp_path: Path, private: PrivateGraders) -> None:
    assert private.public_root is not None
    public = private.public_root / "unit-task/workspace/example.txt"
    public.parent.mkdir(parents=True)
    line = r'assert synthetic_check("escaped\x2dexample")'
    public.write_text("  " + line + "\n")
    private.files[0].write_text(line + "\n")
    assert private.line_fingerprints() == set()


def test_boilerplate_and_nonliteral_lines_are_excluded(tmp_path: Path, private: PrivateGraders) -> None:
    private.files[0].write_text('"Synthetic grader docstring"\nimport unittest\n'
                               'assert synthetic_check(actual) == expected\n'
                               'if __name__ == "__main__":\n    unittest.main(verbosity=999999)\n')
    assert private.line_fingerprints() == set()


@pytest.mark.parametrize("example,hidden", [("1000", "1e3"), ("42", "0x2a"),
                                            ('"public\\u002dexample"', '"public-example"')])
def test_equivalent_public_literals_are_excluded(tmp_path: Path, private: PrivateGraders,
                                                example: str, hidden: str) -> None:
    assert private.public_root is not None
    public = private.public_root / "unit-task/expected.json"
    public.parent.mkdir(parents=True)
    public.write_text(example)
    private.files[0].write_text(f"assert synthetic_check({hidden})\n")
    assert private.line_fingerprints() == set()


@pytest.mark.parametrize('dynamic', [False, True])
def test_parallel_code_mode_literal_calls(tmp_path: Path, private: PrivateGraders,
                                           native_session: list[dict[str, Any]], dynamic: bool) -> None:
    """Pilot-B glue is irrelevant; each cmd/workdir must still be literal."""
    source = '''const results = await Promise.allSettled([
      tools.exec_command({cmd:"cat solution.py",max_output_tokens:2000}),
      tools.exec_command({cmd:"python --version",max_output_tokens:1000})
    ]);
    for (let i = 0; i < results.length; i++) text({check:i,...results[i]});
    const show = value => text(value);
    for await (const value of results) show(value);'''
    if dynamic:
        source = source.replace('cmd:"python --version"', 'cmd:commandFromVariable')
    native_session[22]['payload']['input'] = source
    audit = audit_native(tmp_path, private, native_session)
    assert audit['status'] == ('inconclusive' if dynamic else 'clean'), audit


@pytest.mark.parametrize('source', [
    'const run = tools.exec_command; await run({cmd:"cat solution.py"});',
    'const t = tools; await t.exec_command({cmd:"cat solution.py"});',
    'await tools["exec_command"]({cmd:"cat solution.py"});',
    'await tools?.exec_command({cmd:"cat solution.py"});',
    'await tools.exec_command.call(null, {cmd:"cat solution.py"});',
    'eval("opaque");', 'new Function("opaque")();',
    'const {exec_command} = tools; exec_command({cmd:"cat solution.py"});',
])
def test_indirect_code_mode_is_inconclusive(tmp_path: Path, private: PrivateGraders,
                                           native_session: list[dict[str, Any]], source: str) -> None:
    native_session[22]['payload']['input'] = source
    assert audit_native(tmp_path, private, native_session)['status'] == 'inconclusive'


def test_nested_quoted_rg_payload_is_clean(tmp_path: Path, private: PrivateGraders) -> None:
    command = '''/bin/zsh -lc "rg --files --hidden --no-ignore -g 'AGENTS.md' -g '\"'!.git'\"' -g '\"'!.aws'\"'"'''
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    assert audit_command(tmp_path, private, command, workspace)['status'] == 'clean'
    from eval.runner.audit import shell_tokens, unwrap_shell
    values = [value for value, _ in shell_tokens(unwrap_shell(command))]
    assert values[-3:] == ['!.git', '-g', '!.aws']



@pytest.mark.parametrize('protected', [False, True])
def test_exec_file_change_list_targets(tmp_path: Path, private: PrivateGraders, protected: bool) -> None:
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    path = (private.root if protected else workspace) / 'solution.py'
    log = tmp_path / 'changes.jsonl'
    log.write_text(json.dumps({'type': 'item.completed', 'item': {
        'type': 'file_change', 'changes': [{'path': str(path), 'kind': 'update'}]}}) +
        '\n{"type":"turn.completed"}\n')
    result = audit_logs([log], private, workspace=workspace)
    assert result['status'] == ('access_detected' if protected else 'clean')


@pytest.mark.parametrize('alias_workspace', [False, True])
def test_macos_var_aliases_on_both_sides(tmp_path: Path, private: PrivateGraders, alias_workspace: bool) -> None:
    # No files are created in /var: synthetic absolute operands only.
    workspace = Path('/private/var/folders/synthetic/workspace')
    repository = workspace.parent
    path = '/var/folders/synthetic/workspace/solution.py'
    if alias_workspace:
        workspace = Path('/var/folders/synthetic/workspace')
        path = '/private/var/folders/synthetic/workspace/solution.py'
    log = tmp_path / 'changes.jsonl'
    log.write_text(json.dumps({'type': 'item.completed', 'item': {
        'type': 'file_change', 'changes': [{'path': path, 'kind': 'update'}]}}) +
        '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private, workspace=workspace, repository=repository)['status'] == 'clean'


def test_private_root_macos_alias_is_redacted() -> None:
    private = PrivateGraders(Path('/private/var/folders/synthetic/trusted'), ())
    assert private.markers()['/var/folders/synthetic/trusted'] == 'private_root'
    assert private.redact('cat /var/folders/synthetic/trusted/unit/test_one.py') == 'cat <private_root>/unit/test_one.py'
