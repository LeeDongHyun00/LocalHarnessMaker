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
    assert call["timeout"] == 2400


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


def test_demo_records_unlisted_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'no-auth'))
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, "codex-cli 0.163.0-alpha.11.1\n", "")
    output = tmp_path / "evidence"
    metadata = prepare(output, run=run)
    assert metadata['version'] == 'codex-cli 0.163.0-alpha.11.1'
    assert json.loads((output / 'experiment.json').read_text())['version'] == metadata['version']


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


def test_real_mode_isolated_home_backend_and_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HARNESS_STUB', '1')
    monkeypatch.setenv('HOME', str(tmp_path / 'original-home'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'original-codex-home'))
    calls: list[dict[str, Any]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({'command': command, **kwargs})
        if '--version' in command:
            return subprocess.CompletedProcess(command, 0, (Path(__file__).resolve().parents[2] / 'plugin/CODEX_VERSION').read_text(), '')
        return subprocess.CompletedProcess(command, 0, '{"type":"thread.started","thread_id":"real-session"}\n', '')

    metadata = prepare(tmp_path / 'evidence', run=run, mode='real')
    launch(metadata, 'request', run=run)
    env = calls[-1]['env']
    assert env['HARNESS_BACKEND'] == 'codex_cli'
    assert 'HARNESS_STUB' not in env and 'HARNESS_NESTED' not in env
    assert env['HOME'] != os.environ['HOME']
    assert env['CODEX_HOME'] != os.environ['CODEX_HOME']
    assert calls[-1]['timeout'] > 3 * 600
    assert 'result.txt' in calls[-1]['input']
    assert 'workspace-write' in (Path(metadata['codex_home']) / 'config.toml').read_text()


@pytest.mark.parametrize('name,value', [('HARNESS_STOP_TIMEOUT', '660.0'), ('HARNESS_VERIFY_TIMEOUT', '86401'),
                                       ('HARNESS_HANDOFF_TIMEOUT', '0'), ('HARNESS_MAX_ATTEMPTS', 'bad')])
def test_demo_preflights_all_overrides_before_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> None:
    monkeypatch.setenv(name, value)
    def forbidden(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError('invalid settings must be rejected before any launch')
    with pytest.raises(ValueError):
        prepare(tmp_path / 'evidence', run=forbidden, mode='real')
    assert list(tmp_path.iterdir()) == []


def test_demo_writes_integer_hook_timeouts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HOME', str(tmp_path / 'home'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'source-codex-home'))
    monkeypatch.setenv('HARNESS_STOP_TIMEOUT', '700')
    def version(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        pin = Path(__file__).resolve().parents[2] / 'plugin/CODEX_VERSION'
        return subprocess.CompletedProcess(command, 0, pin.read_text(), '')
    metadata = prepare(tmp_path / 'evidence', run=version, mode='real')
    hooks = json.loads((Path(metadata['codex_home']) / 'hooks.json').read_text())
    for groups in hooks['hooks'].values():
        assert type(groups[0]['hooks'][0]['timeout']) is int
    assert hooks['hooks']['Stop'][0]['hooks'][0]['timeout'] == 700
    assert (Path(metadata['workspace']) / '.local-harness-maker').is_file()


def real_audit_fixture(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[2]
    destination = tmp_path / 'real-evidence'
    shutil.copytree(root / 'plugin/evidence/2026-10-21-d2-pass', destination)
    metadata = json.loads((destination / 'experiment.json').read_text())
    metadata['mode'] = 'real'
    (destination / 'experiment.json').write_text(json.dumps(metadata))
    shutil.copyfile(root / 'schemas/examples/handoff.json', destination / 'approval-state/handoff.json')
    (destination / 'result.txt').write_bytes(b'ok\n')
    for name in ('initial-workspace.json', 'request-workspace.json', 'before-approval-workspace.json'):
        (destination / name).write_text('{"files": {}}')
    return destination


@pytest.mark.parametrize('snapshot', ['initial-workspace.json', 'request-workspace.json', 'before-approval-workspace.json'])
def test_real_audit_rejects_task_files_before_approval(tmp_path: Path, snapshot: str) -> None:
    destination = real_audit_fixture(tmp_path)
    assert audit(destination)['approval_gate'] is True
    (destination / snapshot).write_text('{"files":{"result.txt":{"type":"file","sha256":"early"}}}')
    with pytest.raises(ValueError, match='task files changed before approval'):
        audit(destination)


def test_collect_records_early_task_write_and_rejects_approval_gate(tmp_path: Path) -> None:
    from plugin.demo import collect
    source = Path(__file__).resolve().parents[2] / 'plugin/evidence/2026-10-21-d2-pass'
    workspace = tmp_path / 'workspace'
    out = tmp_path / 'evidence'
    out.mkdir()
    workspace.mkdir()
    shutil.copytree(source / 'request-state', workspace / '.harness')
    transcript = source / 'request-transcript.jsonl'
    events = []
    submitted = 0
    for line in (source / 'hooks.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event['event'] == 'UserPromptSubmit':
            submitted += 1
        if submitted == 2:
            break
        event['input']['transcript_path'] = str(transcript)
        events.append(event)
    (out / 'hooks.jsonl').write_text('\n'.join(json.dumps(event) for event in events))
    (out / 'initial-workspace.json').write_text('{"files": {}}')
    (workspace / 'result.txt').write_bytes(b'ok\n')
    with pytest.raises(ValueError, match='task files changed before approval'):
        collect({'out': str(out), 'workspace': str(workspace), 'mode': 'real'}, 'request')
    assert 'result.txt' in json.loads((out / 'request-workspace.json').read_text())['files']
    assert not (out / 'request-summary.json').exists()


def test_workspace_inventory_includes_unexpected_harness_task_files(tmp_path: Path) -> None:
    from plugin.demo import workspace_files
    directory = tmp_path / '.harness'
    directory.mkdir()
    (directory / 'state.json').write_text('{}')
    assert workspace_files(tmp_path) == {}
    (directory / 'early-task.py').write_text('written before approval')
    assert '.harness/early-task.py' in workspace_files(tmp_path)
