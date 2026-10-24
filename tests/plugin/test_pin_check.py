"""Installed CLI/model/pricing pin preflight, using non-generating fake probes."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from plugin import pin_check
from plugin.artifacts import ROOT, read, session_directory, validate


@pytest.mark.parametrize('outcome', ['enabled', 'version', 'missing', 'renamed', 'unobservable', 'pricing', 'timeout', 'rpc', 'rpc_missing', 'rpc_truncated'])
def test_pin_outcomes(tmp_path: Path, outcome: str) -> None:
    directory = session_directory(tmp_path, 'pin-session')
    calls: list[list[str]] = []
    def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        assert kwargs['shell'] is False and kwargs['timeout'] <= 5
        if outcome == 'timeout':
            raise subprocess.TimeoutExpired(command, kwargs['timeout'])
        if command[1] == '--version':
            version = 'codex-cli 99.0.0' if outcome == 'version' else 'codex-cli 0.163.0-alpha.11.1'
            return subprocess.CompletedProcess(command, 0, version + '\n', '')
        if command[1] == '--help':
            return subprocess.CompletedProcess(command, 0, 'Commands:\n  app-server\n' if outcome.startswith('rpc') else 'Commands:\n  models\n', '')
        if command[1] == 'app-server':
            assert 'thread/start' not in kwargs['input']
            assert 'model/list' in kwargs['input']
            data = [{'id': 1, 'result': {}}, {'id': 2, 'result': {
                'data': [{'id': 'opaque', 'model': 'gpt-6-luna', 'displayName': 'other'}],
                'nextCursor': 'next' if outcome == 'rpc_truncated' else None}}]
            if outcome == 'rpc_missing':
                data.pop()
            return subprocess.CompletedProcess(command, 0, ''.join(json.dumps(r) + '\n' for r in data), '')
        if outcome == 'unobservable':
            return subprocess.CompletedProcess(command, 1, '', 'unsupported')
        models = [] if outcome == 'missing' else ['gpt-6-luna-new'] if outcome == 'renamed' else ['gpt-6-luna', 'gpt-6.1-sol']
        return subprocess.CompletedProcess(command, 0, json.dumps(models), '')
    value = pin_check.check('pin-session', directory, '/mock/codex', runner=runner,
                            pricing=tmp_path / 'missing-prices' if outcome == 'pricing' else pin_check.PRICES)
    validate(value, 'pin-check.schema.json')
    assert value == read(directory / 'pin-check.json')
    assert (value['status'] == 'enabled') == (outcome in {'enabled', 'rpc'})
    if value['status'] == 'disabled':
        assert value['reason_codes'] and 'cannot be represented as H3' in value['advisory']
    assert all('exec' not in command for command in calls)


def test_cli_exit_codes_and_exact_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    monkeypatch.setattr('sys.argv', ['pin-check', '--session-id', 'native', '--artifacts', str(tmp_path), '--codex', '/missing'])
    assert pin_check.main() == 2
    assert 'internal error' in capsys.readouterr().err
    monkeypatch.setattr(pin_check, 'check', lambda *args: {'status': 'disabled', 'advisory': 'Disabled pin'})
    assert pin_check.main() == 1
    assert capsys.readouterr().out == 'Disabled pin\n'
    monkeypatch.setattr(pin_check, 'check', lambda *args: {'status': 'enabled', 'advisory': 'Enabled pin'})
    assert pin_check.main() == 0


def test_no_display_name_or_prefix_match(tmp_path: Path) -> None:
    def invoke(command: list[str], **kwargs: Any) -> Any:
        output = 'models\n' if command[1] == '--help' else json.dumps([{'id': 'gpt-6-luna-new', 'displayName': 'gpt-6-luna'}])
        return subprocess.CompletedProcess(command, 0, output, '')
    _, listed = pin_check.inspect_models('/fake', invoke)
    assert listed is False


def test_install_check_runs_pin_against_installed_prices(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                        capsys: Any) -> None:
    from plugin import install
    from plugin.hooks import _process
    home, project = tmp_path / 'codex-home', tmp_path / 'project'
    monkeypatch.delenv('HARNESS_INTERFACE_VERSION')
    monkeypatch.setattr('sys.argv', ['install', '--codex-home', str(home), '--project', str(project), '--check'])
    monkeypatch.setattr(install, 'resolve_codex', lambda: '/fake/codex')
    monkeypatch.setattr(install, 'check_install', lambda *args: True)
    monkeypatch.setattr(_process, 'run_group', lambda *args, **kwargs:
                        subprocess.CompletedProcess(args[0], 0, 'codex-cli 0.163.0-alpha.11.1\n', ''))
    def checked(session_id: str, directory: Path, codex: str, **kwargs: Any) -> dict[str, Any]:
        assert kwargs['pricing'] == home / 'local-harness-maker/controller/prices.yaml'
        assert not directory.is_relative_to(project)
        return {'status': 'disabled', 'advisory': 'Luna disabled: model_missing, pricing_missing'}
    monkeypatch.setattr(pin_check, 'check', checked)
    assert install.main() == 1
    assert 'model_missing, pricing_missing' in capsys.readouterr().err
