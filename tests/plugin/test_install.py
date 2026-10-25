"""Installation stays in temporary HOME/CODEX_HOME, using a fake version executable."""
from __future__ import annotations
import json
import os
import shlex
import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def test_fresh_snapshot_and_distinct_check_messages(tmp_path: Path) -> None:
    home = tmp_path / 'home'
    codex_home = home / '.codex'
    home.mkdir()
    fake = tmp_path / 'fake-codex'
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "codex-cli 9.0.0"\n')
    fake.chmod(0o755)
    env = {**os.environ, 'HOME': str(home), 'CODEX_HOME': str(codex_home),
           'HARNESS_CODEX': str(fake), 'HARNESS_PYTHON': sys.executable}
    command = ['bash', str(ROOT / 'plugin/install.sh'), '--codex-home', str(codex_home),
               '--project', str(tmp_path / 'project')]
    result = subprocess.run([*command, '--check'], env=env, capture_output=True, text=True)
    assert result.returncode == 1
    assert all(message in result.stderr for message in ('Codex version unverified', 'Hooks not registered', 'Skill missing'))
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "' + (ROOT / 'plugin/CODEX_VERSION').read_text().strip() + '"\n')
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'project/AGENTS.md').exists()
    (codex_home / 'auth.json').write_text('{}')
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

REAL_RESOLVE_CODEX = install.resolve_codex


@pytest.fixture(autouse=True)
def isolated_install_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HOME', str(tmp_path / 'isolated-home'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'isolated-home/.codex'))


@pytest.fixture
def installer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    home, project = tmp_path / 'codex-home', tmp_path / 'project'
    executable = tmp_path / 'ChatGPT App/codex'
    executable.parent.mkdir()
    executable.write_text('#!/bin/sh\nexit 0\n')
    executable.chmod(0o755)
    monkeypatch.setattr(install, 'resolve_codex', lambda: str(executable))
    def version(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['timeout'] == 5 and kwargs['env']['HARNESS_NESTED'] == '1'
        return subprocess.CompletedProcess(command, 0, (ROOT / 'plugin/CODEX_VERSION').read_text(), '')
    monkeypatch.setattr(_process, 'run_group', version)
    def run(check: bool = False, codex: Path | None = None) -> int:
        monkeypatch.setattr(sys, 'argv', ['install', '--codex-home', str(home), '--project', str(project),
                                        *(['--check'] if check else []),
                                        *(['--codex', str(codex)] if codex is not None else [])])
        result = install.main()
        if not check and result == 0:
            (home / 'auth.json').write_text('{}')
        return result
    return {'home': home, 'project': project, 'run': run, 'executable': executable}


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
    assert install.resolve_codex() == str(Path('codex').absolute())
    available.remove('codex')
    assert install.resolve_codex() == install.APP_CODEX
    available.clear()
    assert install.resolve_codex() is None


def test_explicit_codex_overrides_discovery(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden() -> str | None:
        raise AssertionError('explicit executable must bypass discovery')
    monkeypatch.setattr(install, 'resolve_codex', forbidden)
    assert installer['run'](codex=installer['executable']) == 0
    assert installer['run'](True, codex=installer['executable']) == 0
    hooks = json.loads((installer['home'] / 'hooks.json').read_text())
    for event in install.EVENTS:
        tokens = shlex.split(hooks['hooks'][event][0]['hooks'][0]['command'])
        assert f"HARNESS_CODEX={installer['executable']}" in tokens


@pytest.mark.parametrize('check', [False, True])
@pytest.mark.parametrize('exists', [False, True])
def test_invalid_explicit_codex_never_falls_back(installer: dict[str, Any], tmp_path: Path,
        capsys: pytest.CaptureFixture[str], check: bool, exists: bool) -> None:
    executable = tmp_path / 'invalid-codex'
    if exists:
        executable.write_text('not executable')
        executable.chmod(0o644)
    assert installer['run'](check, codex=executable) == 1
    assert 'Codex CLI not found or not executable' in capsys.readouterr().err
    assert not installer['home'].exists() and not installer['project'].exists()


def test_no_codex_discovery_rejects_install_and_check(installer: dict[str, Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv('HARNESS_CODEX', raising=False)
    monkeypatch.setenv('PATH', str(tmp_path))
    monkeypatch.setattr(install, 'APP_CODEX', str(tmp_path / 'missing-app/codex'))
    # Restore actual discovery instead of the installer fixture's fake resolver.
    monkeypatch.setattr(install, 'resolve_codex', REAL_RESOLVE_CODEX)
    assert install.resolve_codex() is None
    with pytest.raises(ValueError, match='Codex CLI not found'):
        installer['run']()
    assert installer['run'](True) == 1
    assert 'Codex CLI not found' in capsys.readouterr().err
    assert not installer['home'].exists() and not installer['project'].exists()


def test_version_probe_failure_writes_nothing(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def failed(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired('fake', 5)
    monkeypatch.setattr(_process, 'run_group', failed)
    assert installer['run']() == 1
    assert 'Codex version probe failed' in capsys.readouterr().err
    assert not installer['home'].exists() and not installer['project'].exists()


def test_unverified_version_installs_but_check_requires_evidence(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def version(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, 'codex-cli 9.0.0\n', '')
    monkeypatch.setattr(_process, 'run_group', version)
    assert installer['run']() == 0
    assert installer['run'](True) == 1
    errors = capsys.readouterr().err
    assert 'Codex version unverified: codex-cli 9.0.0' in errors
    assert 'plugin.probe' in errors and 'then add the version' in errors
    assert 'Hooks not registered' not in errors and 'Skill missing' not in errors


def test_new_host_verified_version_passes_check(installer: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    def version(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, 'codex-cli 0.163.0-alpha.11.1\n', '')
    monkeypatch.setattr(_process, 'run_group', version)
    assert installer['run']() == 0
    assert installer['run'](True) == 0


def test_check_reports_missing_auth_and_unknown_trust(installer: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    assert installer['run']() == 0
    (installer['home'] / 'auth.json').rename(installer['home'] / 'saved-login')
    assert installer['run'](True) == 1
    errors = capsys.readouterr().err
    assert 'auth.json missing' in errors
    assert 'Hook trust for CODEX_HOME: unknown' in errors
    assert '--dangerously-bypass-hook-trust' in errors


@pytest.mark.parametrize('status', ['managed', 'trusted', 'untrusted', 'modified', None])
def test_hook_trust_discovery_scoped_to_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                           capsys: pytest.CaptureFixture[str], status: str | None) -> None:
    home, project = tmp_path / 'codex-home', tmp_path
    def discovery(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command == ['/fake/codex', 'app-server']
        assert kwargs['env']['CODEX_HOME'] == str(home)
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        assert kwargs['timeout'] == 5 and kwargs['shell'] is False
        messages = [json.loads(line) for line in kwargs['input'].splitlines()]
        assert [m['method'] for m in messages] == ['initialize', 'initialized', 'hooks/list']
        assert messages[-1]['params'] == {'cwds': [str(project)]}
        hooks = [{'sourcePath': str(home / 'hooks.json'), 'trustStatus': status},
                 {'sourcePath': '/other/home/hooks.json', 'trustStatus': 'trusted'}]
        return subprocess.CompletedProcess(command, 0, json.dumps({'id': 2, 'result': {'data': [
            {'cwd': str(project), 'errors': [], 'warnings': [], 'hooks': hooks}]}}), '')
    monkeypatch.setattr(_process, 'run_group', discovery)
    install.hook_trust(home, project, '/fake/codex')
    errors = capsys.readouterr().err
    assert f'Hook trust for CODEX_HOME: {status or "unknown"}' in errors
    assert ('--dangerously-bypass-hook-trust' in errors) == (status not in ('trusted', 'managed'))


@pytest.mark.parametrize('directory_source', [False, True])
def test_link_auth_is_symlink_and_idempotent(tmp_path: Path, installer: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch, directory_source: bool) -> None:
    source = tmp_path / 'login'
    source.mkdir()
    login = source / 'auth.json'
    login.write_text('credential contents stay outside snapshot')
    home, project = installer['home'], installer['project']
    monkeypatch.setattr(sys, 'argv', ['install', '--codex-home', str(home), '--project', str(project),
                                    '--link-auth', str(source if directory_source else login)])
    assert install.main() == 0
    assert install.main() == 0
    assert (home / 'auth.json').is_symlink()
    assert (home / 'auth.json').resolve() == login
    assert not (home / 'local-harness-maker/auth.json').exists()


def test_link_auth_refuses_existing_login_and_missing_source(tmp_path: Path) -> None:
    home = tmp_path / 'home'
    home.mkdir()
    existing = home / 'auth.json'
    existing.write_text('existing')
    source = tmp_path / 'auth.json'
    source.write_text('other')
    with pytest.raises(ValueError, match='refusing to replace'):
        install.auth_source(source, home)
    with pytest.raises(FileNotFoundError):
        install.auth_source(tmp_path / 'absent', home)
    assert existing.read_text() == 'existing'


@pytest.mark.parametrize('worktree', [False, True])
def test_marker_excluded_locally_without_gitignore(tmp_path: Path, installer: dict[str, Any], worktree: bool) -> None:
    project = installer['project']
    project.mkdir()
    gitdir = project / '.git'
    if worktree:
        common = tmp_path / 'common-git'
        gitdir = common / 'worktrees/project'
        gitdir.mkdir(parents=True)
        (gitdir / 'commondir').write_text('../..')
        (project / '.git').write_text('gitdir: ' + str(gitdir))
        gitdir = common
    (gitdir / 'info').mkdir(parents=True)
    exclude = gitdir / 'info/exclude'
    exclude.write_text('# keep\nother')
    (project / '.gitignore').write_text('tracked rule\n')
    assert installer['run']() == 0
    assert installer['run']() == 0
    assert exclude.read_text() == '# keep\nother\n.local-harness-maker\n'
    assert (project / '.gitignore').read_text() == 'tracked rule\n'


@pytest.mark.parametrize('mode', ['timeout', 'error', 'malformed', 'other-home'])
def test_trust_probe_failures_print_operator_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str], mode: str) -> None:
    def discovery(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if mode == 'timeout':
            raise subprocess.TimeoutExpired(command, 5)
        if mode == 'error':
            return subprocess.CompletedProcess(command, 1, '', 'unsupported')
        if mode == 'malformed':
            return subprocess.CompletedProcess(command, 0, '{', '')
        return subprocess.CompletedProcess(command, 0, json.dumps({'id': 2, 'result': {
            'data': [{'cwd': str(tmp_path), 'errors': [], 'warnings': [],
                      'hooks': [{'sourcePath': '/other/hooks.json', 'trustStatus': 'trusted'}]}]}}), '')
    monkeypatch.setattr(_process, 'run_group', discovery)
    install.hook_trust(tmp_path / 'home', tmp_path, '/fake/codex')
    errors = capsys.readouterr().err
    assert 'Hook trust for CODEX_HOME: unknown' in errors
    assert '--dangerously-bypass-hook-trust' in errors


def test_rendered_codex_path_and_check_output(installer: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    assert installer['run']() == 0
    hooks = json.loads((installer['home'] / 'hooks.json').read_text())
    executable = str(installer['executable'])
    for event in install.EVENTS:
        handler = hooks['hooks'][event][0]['hooks'][0]
        tokens = shlex.split(handler['command'])
        assert tokens[0] == 'env'
        assert tokens[2] == f'HARNESS_CODEX={executable}'
    assert installer['run'](True) == 0
    errors = capsys.readouterr().err
    assert f'Codex executable: {executable}' in errors
    for event in install.EVENTS:
        assert f'{event} Codex executable: {executable}' in errors
    installer['executable'].rename(installer['executable'].with_name('moved-codex'))
    assert installer['run'](True) == 1
    assert 'embedded Codex executable missing or invalid' in capsys.readouterr().err


def test_installed_v3_pin_uses_embedded_codex_with_empty_path(installer: dict[str, Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    assert installer['run']() == 0
    home, project = installer['home'], installer['project']
    executable = installer['executable']
    version = (ROOT / 'plugin/CODEX_VERSION').read_text().strip()
    executable.write_text('#!/bin/sh\nprintf "%s\\n" ' + shlex.quote(version) + '\n')
    hooks = json.loads((home / 'hooks.json').read_text())
    tokens = shlex.split(hooks['hooks']['SessionStart'][0]['hooks'][0]['command'])
    command = [shutil.which('env'), *tokens[1:]]
    monkeypatch.delenv('HARNESS_CODEX', raising=False)
    payload = {'cwd': str(project), 'session_id': 'installed-v3', 'hook_event_name': 'SessionStart'}
    result = subprocess.run(command, input=json.dumps(payload), cwd=tmp_path,
        env={**os.environ, 'PATH': '', 'HARNESS_INTERFACE_VERSION': '3', 'HARNESS_NESTED': '0'},
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    pins = list((project / '.localharness/v3/sessions').glob('*/pin-check.json'))
    assert len(pins) == 1, result.stdout + result.stderr
    pin = json.loads(pins[0].read_text())
    assert pin['codex_version'] == version
    assert f'Codex executable: {executable}' in pin['advisory']
    assert str(executable) in result.stdout
