"""Version advisories are bounded, advisory and scoped to the persisted session."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
from typing import Any
import pytest
from plugin import versions
from plugin.hooks._runtime import Runtime

# Preserve the actual function before the offline autouse fixture replaces it.
PROBE = versions.cli_version


def test_probe_uses_fake_executable_and_bounded_nested_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HARNESS_CODEX', '/fake/codex')
    monkeypatch.setattr(versions.shutil, 'which', lambda candidate: candidate)
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command == ['/fake/codex', '--version']
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        assert kwargs['timeout'] == 0.25 and kwargs['shell'] is False
        return subprocess.CompletedProcess(command, 0, 'codex-cli 99.1.2\n', '')
    assert PROBE(runner=run, timeout=0.25) == 'codex-cli 99.1.2'


def runtime(root: Path, session: str = 'one') -> Runtime:
    return Runtime({'cwd': str(root), 'session_id': session, 'hook_event_name': 'SessionStart'})


def test_unlisted_warns_once_and_detects_update_on_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert runtime(tmp_path).dispatch('SessionStart') is None
    monkeypatch.setattr(versions, 'cli_version', lambda **kwargs: 'codex-cli 99.1.2')
    response = runtime(tmp_path).dispatch('SessionStart')
    text = response['hookSpecificOutput']['additionalContext']
    assert 'codex-cli 99.1.2' in text and 'python -m plugin.probe --mode exec --out' in text
    assert len(text.splitlines()) == 1
    assert runtime(tmp_path).dispatch('SessionStart') is None
    assert runtime(tmp_path, 'two').dispatch('SessionStart') is not None
    assert json.loads((tmp_path / '.harness/session.json').read_text())['cli_version'] == 'codex-cli 99.1.2'


def test_probe_failure_is_nonblocking_and_can_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(**kwargs: Any) -> str:
        raise TimeoutError('fake deadline')
    monkeypatch.setattr(versions, 'cli_version', fail)
    assert runtime(tmp_path).dispatch('SessionStart') is None
    monkeypatch.setattr(versions, 'cli_version', lambda **kwargs: 'codex-cli 99.1.2')
    assert runtime(tmp_path).dispatch('SessionStart') is not None


def test_warning_survives_bad_handoff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(versions, 'cli_version', lambda **kwargs: 'codex-cli 99.1.2')
    hook = runtime(tmp_path)
    (tmp_path / '.harness/handoff.json').write_text('{}')
    monkeypatch.setattr(hook, 'call', lambda *args: (_ for _ in ()).throw(ValueError('invalid handoff')))
    response = hook.dispatch('SessionStart')
    assert 'unverified' in response['hookSpecificOutput']['additionalContext']
    assert 'HARNESS_HANDOFF' not in str(response)
