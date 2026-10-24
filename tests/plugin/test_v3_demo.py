"""Host-demo preparation never launches an executor automatically."""
from __future__ import annotations

from pathlib import Path
import shlex
import subprocess
from typing import Any

import pytest

from plugin import v3_demo
from plugin.artifacts import ROOT, read


def test_scripts_keep_hooks_active_and_do_not_restate_label(tmp_path: Path) -> None:
    metadata = {'out': str(tmp_path / 'capture with spaces'), 'home': '/isolated/home',
                'codex_home': '/isolated/codex', 'workspace': '/isolated/project',
                'python': '/venv/python', 'codex': '/bundle/codex'}
    scripts = v3_demo.scripts(metadata)
    assert set(scripts) == {'session1.sh', 'session2.sh'}
    for content in scripts.values():
        command = shlex.split(content.split('exec ', 1)[1])
        assert command[:2] == ['/usr/bin/script', '-q']
        assert 'HARNESS_INTERFACE_VERSION=3' in command
        assert command[command.index('-u') + 1] == 'HARNESS_NESTED'
        assert '--dangerously-bypass-hook-trust' not in command
        assert 'exec' not in command and 'resume' not in command
    assert 'unspecified' in scripts['session1.sh']
    assert 'choose-a-unique-release-label' not in scripts['session2.sh']


def test_prepare_missing_other_role_cli_stops_before_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v3_demo, 'resolve_codex', lambda: '/fake/codex')
    def runner(command: list[str], **kwargs: Any) -> Any:
        assert command[-1] == '--help'
        return subprocess.CompletedProcess(command, 0, 'historical operations only', '')
    out = tmp_path / 'capture'
    with pytest.raises(ValueError, match='not integrated'):
        v3_demo.prepare(out, runner=runner)
    assert not out.exists()


def test_prepare_isolated_host_commands_with_mock_installer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v3_demo, 'resolve_codex', lambda: '/fake/codex')
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'no-login'))
    calls = []
    def runner(command: list[str], **kwargs: Any) -> Any:
        calls.append(command)
        assert '-m' in command and 'exec' not in command
        return subprocess.CompletedProcess(command, 0, 'requirements claim-audit ledger-validate', '')
    v3_demo.prepare(tmp_path / 'capture', runner=runner)
    assert len(calls) == 3
    assert (tmp_path / 'capture/session1.sh').is_file()
    metadata = read(tmp_path / 'capture/experiment.json')
    assert metadata['workspace'] != str(ROOT)
    assert (Path(metadata['codex_home'])).is_dir()
