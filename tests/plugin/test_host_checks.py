"""Synthetic host captures exercise procedure boundaries and offline rejection."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
from typing import Any
import pytest
from plugin import host_checks as checks


@pytest.fixture
def host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Any]:
    monkeypatch.setattr(checks.install, 'resolve_codex', lambda: checks.install.APP_CODEX)
    temporary = tmp_path / 'isolated'
    temporary.mkdir()
    monkeypatch.setattr(checks.tempfile, 'mkdtemp', lambda **kwargs: str(temporary))
    monkeypatch.setenv('HARNESS_NESTED', '1')
    out = tmp_path / 'evidence'
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['shell'] is False
        assert 'HARNESS_NESTED' not in kwargs['env']
        if '--version' in command:
            return subprocess.CompletedProcess(command, 0, 'codex-cli 0.163.0-alpha.11.1\n', '')
        if '-c' in command and 'resolve_codex' in command[-1]:
            assert kwargs['env']['PATH'] == '' and 'HARNESS_CODEX' not in kwargs['env']
            return subprocess.CompletedProcess(command, 0, checks.install.APP_CODEX + '\n', '')
        if 'plugin.install' in command:
            home = Path(command[command.index('--codex-home') + 1])
            project = Path(command[command.index('--project') + 1])
            for target, data in checks.install.plan_install(home, project).items():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            if checks.read(out / 'experiment.json')['scenario'] == 'bundle':
                assert kwargs['env']['PATH'] == ''
                assert 'HARNESS_CODEX' not in kwargs['env']
            return subprocess.CompletedProcess(command, 0, 'Installed\n', '')
        assert 'exec' in command and 'resume' not in command
        assert '--dangerously-bypass-hook-trust' not in command
        metadata = checks.read(out / 'experiment.json')
        records(out, metadata, 'second')
        events = '\n'.join(json.dumps({'type': event, 'thread_id': 'second'}) for event in ('thread.started', 'turn.completed'))
        return subprocess.CompletedProcess(command, 0, events + '\n', '')
    return out, run


def records(out: Path, metadata: dict[str, Any], session: str) -> None:
    for event in checks.install.EVENTS:
        checks.write(out / 'hooks' / f'{session}-{event}.json', {
            'input': {'session_id': session, 'cwd': metadata['workspace'], 'hook_event_name': event},
            'stdout': 'HARNESS_CONTRACT' if metadata['scenario'] == 'trust' and event == 'UserPromptSubmit' else '',
            'stderr': '', 'returncode': 0})


def complete(out: Path, run: Any, scenario: str) -> None:
    checks.prepare(out, scenario, runner=run)
    if scenario != 'bundle':
        metadata = checks.read(out / 'experiment.json')
        records(out, metadata, 'first')
        (out / 'first-session.terminal').write_text('Synthetic interactive trust transcript\n')
        checks.run_second(out, runner=run)


@pytest.mark.parametrize('scenario', checks.SCENARIOS)
def test_prepared_procedure_and_offline_checker(host: tuple[Path, Any], scenario: str) -> None:
    out, run = host
    complete(out, run, scenario)
    assert checks.check(out)['overall'] == 'pass'
    if scenario != 'bundle':
        script = (out / 'first-session.sh').read_text()
        assert 'env -i' in script and 'HARNESS_NESTED=' not in script
        assert '--dangerously-bypass-hook-trust' not in script


@pytest.mark.parametrize('corruption', ['bypass', 'same-session', 'missing-hook', 'nonzero', 'truncated',
                                      'changed-config', 'version-drift', 'changed-first', 'noise', 'harness', 'marker'])
def test_rejects_incomplete_or_false_silence(host: tuple[Path, Any], corruption: str) -> None:
    out, run = host
    complete(out, run, 'silence')
    if corruption == 'bypass':
        value = checks.read(out / 'second.json')
        value['command'].insert(1, '--dangerously-bypass-hook-trust')
        checks.write(out / 'second.json', value)
    elif corruption in ('same-session', 'missing-hook', 'nonzero', 'noise'):
        for path in (out / 'hooks').glob('second-*.json'):
            value = checks.read(path)
            if corruption == 'same-session':
                value['input']['session_id'] = 'first'
            elif corruption == 'missing-hook':
                value['input']['hook_event_name'] = 'Unknown'
            elif corruption == 'nonzero':
                value['returncode'] = 1
            else:
                value['stderr'] = 'unexpected output'
            checks.write(path, value)
    elif corruption == 'truncated':
        (out / 'second.stdout').write_text('{')
    elif corruption == 'changed-config':
        (out / 'config-after-second.toml').write_text('changed = true')
    elif corruption == 'version-drift':
        (out / 'version-after.stdout').write_text('codex-cli 99.1.2')
    elif corruption == 'changed-first':
        (out / 'hooks/first-Stop.json').write_text('{}')
    else:
        value = checks.read(out / 'after.json')
        value['harness_paths' if corruption == 'harness' else 'markers'] = ['unexpected']
        checks.write(out / 'after.json', value)
    with pytest.raises((ValueError, KeyError)):
        checks.check(out)


def test_bundle_rejects_discovery_override(host: tuple[Path, Any]) -> None:
    out, run = host
    complete(out, run, 'bundle')
    value = checks.read(out / 'install.json')
    value['codex_override'] = checks.install.APP_CODEX
    checks.write(out / 'install.json', value)
    with pytest.raises(ValueError, match='overridden'):
        checks.check(out)


def test_second_requires_completed_first(host: tuple[Path, Any]) -> None:
    out, run = host
    checks.prepare(out, 'trust', runner=run)
    with pytest.raises(ValueError, match='interactive first'):
        checks.run_second(out, runner=run)
