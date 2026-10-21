"""Verify the fixed CLI's input-error and stream conventions."""

import subprocess
import sys


def test_missing_arguments_are_input_errors() -> None:
    result = subprocess.run([sys.executable, "-m", "eval", "run"], capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Input error" in result.stderr
