"""Installation stays in temporary HOME/CODEX_HOME, using a fake version executable."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_fresh_snapshot_and_distinct_check_messages(tmp_path: Path) -> None:
    home = tmp_path / 'home'
    codex_home = home / '.codex'
    home.mkdir()
    fake = tmp_path / 'fake-codex'
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "codex-cli wrong"\n')
    fake.chmod(0o755)
    env = {**os.environ, 'HOME': str(home), 'CODEX_HOME': str(codex_home),
           'HARNESS_CODEX': str(fake), 'HARNESS_PYTHON': sys.executable}
    command = ['bash', str(ROOT / 'plugin/install.sh'), '--codex-home', str(codex_home),
               '--project', str(tmp_path / 'project')]
    result = subprocess.run([*command, '--check'], env=env, capture_output=True, text=True)
    assert result.returncode == 1
    assert all(message in result.stderr for message in ('Codex version mismatch', 'Hooks not registered', 'Skill missing'))
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "' + (ROOT / 'plugin/CODEX_VERSION').read_text().strip() + '"\n')
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'project/AGENTS.md').exists()
    result = subprocess.run([*command, '--check'], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    hooks = json.loads((codex_home / 'hooks.json').read_text())
    assert hooks['hooks']['Stop'][0]['hooks'][0]['timeout'] == 660
    script = codex_home / 'local-harness-maker/plugin/hooks/session_start.py'
    payload = {'cwd': str(tmp_path / 'project'), 'session_id': 'installed', 'hook_event_name': 'SessionStart'}
    result = subprocess.run([sys.executable, str(script)], input=json.dumps(payload),
                            cwd=tmp_path, env={**env, 'HARNESS_NESTED': '0'}, capture_output=True, text=True)
    assert result.returncode == 0 and 'warning' not in result.stderr
    # The copied controller/verifier import independently of the source checkout.
    for module in ('controller', 'verifier'):
        result = subprocess.run([sys.executable, '-m', module, '--help'],
                                cwd=codex_home / 'local-harness-maker', env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

    transcript = tmp_path / 'transcript.jsonl'
    transcript.write_text('{}\n')
    for event, prompt in [('UserPromptSubmit', 'request'), ('UserPromptSubmit', 'approve'),
                          ('Stop', ''), ('Stop', ''), ('SessionStart', '')]:
        payload.update(hook_event_name=event, prompt=prompt, transcript_path=str(transcript))
        script_name = {'UserPromptSubmit': 'user_prompt_submit.py', 'Stop': 'stop.py',
                       'SessionStart': 'session_start.py'}[event]
        result = subprocess.run([sys.executable, str(script.with_name(script_name))], input=json.dumps(payload),
                                cwd=tmp_path, env={**env, 'HARNESS_STUB': '1', 'HARNESS_NESTED': '0'},
                                capture_output=True, text=True)
        assert result.returncode == 0 and 'warning:' not in result.stderr, result.stderr
    assert 'HARNESS_HANDOFF' in result.stdout


import pytest
from typing import Any
from plugin import install
from plugin.hooks import _process


@pytest.fixture(autouse=True)
def isolated_install_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HOME', str(tmp_path / 'isolated-home'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'isolated-home/.codex'))


@pytest.fixture
def installer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    home, project = tmp_path / 'codex-home', tmp_path / 'project'
    monkeypatch.setattr(install, 'resolve_codex', lambda: '/fake/codex')
    def version(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['timeout'] == 5 and kwargs['env']['HARNESS_NESTED'] == '1'
        return subprocess.CompletedProcess(command, 0, (ROOT / 'plugin/CODEX_VERSION').read_text(), '')
    monkeypatch.setattr(_process, 'run_group', version)
    def run(check: bool = False) -> int:
        monkeypatch.setattr(sys, 'argv', ['install', '--codex-home', str(home), '--project', str(project), *(['--check'] if check else [])])
        return install.main()
    return {'home': home, 'project': project, 'run': run}


@pytest.mark.parametrize('bad', ['10.0', '1.5', '0', '-1', '86401', 'nan', 'inf', 'true'])
def test_installer_rejects_timeout_before_any_target_write(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setenv('HARNESS_HANDOFF_TIMEOUT', bad)
    with pytest.raises(ValueError, match='timeout type or value mismatch'):
        installer['run']()
    assert not installer['home'].exists() and not installer['project'].exists()


def test_installer_repairs_partial_and_is_idempotent(installer: dict[str, Any]) -> None:
    home, project = installer['home'], installer['project']
    (home / 'local-harness-maker').mkdir(parents=True)
    (home / 'config.toml').write_text('model = "preserve"\n[features]\nhooks = false\nother = true\n')
    unrelated = {'type': 'command', 'command': 'unrelated-plugin', 'timeout': 12}
    (home / 'hooks.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [unrelated]}]}}))
    project.mkdir()
    (project / 'AGENTS.md').write_text('Existing instructions\n')
    assert installer['run']() == 0
    # Model a partial install missing one required script; rerun repairs it.
    script = home / 'local-harness-maker/plugin/hooks/stop.py'
    script.rename(script.with_suffix('.old'))
    assert installer['run'](True) == 1
    assert installer['run']() == 0
    assert installer['run']() == 0
    assert installer['run'](True) == 0
    hooks = json.loads((home / 'hooks.json').read_text())
    assert len(hooks['hooks']['Stop']) == 2
    assert hooks['hooks']['Stop'][0]['hooks'] == [unrelated]
    assert (project / 'AGENTS.md').read_text().count('Existing instructions') == 1
    assert (project / 'AGENTS.md').read_text().count('# LocalHarnessMaker') == 1
    assert (project / '.local-harness-maker').is_file()
    assert 'model = "preserve"' in (home / 'config.toml').read_text()


@pytest.mark.parametrize('broken', ['hooks', 'config'])
def test_malformed_existing_config_does_not_start_partial_install(installer: dict[str, Any], broken: str) -> None:
    home = installer['home']
    home.mkdir()
    filename = 'hooks.json' if broken == 'hooks' else 'config.toml'
    target = home / filename
    target.write_text('malformed[')
    with pytest.raises(ValueError):
        installer['run']()
    assert list(home.iterdir()) == [target]
    assert not installer['project'].exists()


def test_check_is_interpreter_and_environment_independent_and_rejects_float(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv('HARNESS_STOP_TIMEOUT', '700')
    assert installer['run']() == 0
    monkeypatch.delenv('HARNESS_STOP_TIMEOUT')
    home = installer['home']
    path = home / 'hooks.json'
    hooks = json.loads(path.read_text())
    handler = hooks['hooks']['Stop'][0]['hooks'][0]
    assert type(handler['timeout']) is int and handler['timeout'] == 700
    handler['command'] = handler['command'].replace(sys.executable, '/another/python')
    path.write_text(json.dumps(hooks))
    assert installer['run'](True) == 0
    for bad in (700.0, 701, True, "700"):
        handler['timeout'] = bad
        path.write_text(json.dumps(hooks))
        assert installer['run'](True) == 1
        assert 'timeout type or value mismatch' in capsys.readouterr().err


def test_cli_not_found_has_own_diagnostic(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(install, 'resolve_codex', lambda: None)
    assert installer['run'](True) == 1
    assert 'Codex CLI not found' in capsys.readouterr().err
    assert not installer['home'].exists()


def test_binary_resolution_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HARNESS_CODEX', '/explicit/codex')
    available = {'/explicit/codex', 'codex', install.APP_CODEX}
    monkeypatch.setattr(install.shutil, 'which', lambda name: name if name in available else None)
    assert install.resolve_codex() == '/explicit/codex'
    available.remove('/explicit/codex')
    assert install.resolve_codex() == 'codex'
    available.remove('codex')
    assert install.resolve_codex() == install.APP_CODEX
    available.clear()
    assert install.resolve_codex() is None


def test_version_probe_failure_writes_nothing(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def failed(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired('fake', 5)
    monkeypatch.setattr(_process, 'run_group', failed)
    assert installer['run']() == 1
    assert 'Codex version probe failed' in capsys.readouterr().err
    assert not installer['home'].exists() and not installer['project'].exists()
