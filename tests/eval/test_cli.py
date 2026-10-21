"""Verify the fixed CLI's input-error and stream conventions."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_missing_arguments_are_input_errors() -> None:
    result = subprocess.run([sys.executable, "-m", "eval", "run"], capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Input error" in result.stderr


def test_success_prints_supplied_directory_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import eval.__main__ as cli
    output = tmp_path / 'report'
    monkeypatch.setenv('LHM_PRIVATE_GRADERS', '/synthetic-trusted-parent')
    monkeypatch.setattr(sys, 'argv', ['eval', 'run', '--config', 'synthetic.yaml', '--out', str(output)])
    monkeypatch.setattr(cli, 'run', lambda *args: output / 'report.json')
    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.out == str(output) + '\n'
    assert captured.err == ''
