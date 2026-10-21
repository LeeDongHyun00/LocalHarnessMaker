"""Fixture output bytes must remain identical to the shared schema examples."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("module,operation,args,fixture", [
    ("controller", "contract", [], "contract.json"),
    ("controller", "handoff", [], "handoff.json"),
    ("verifier", "check", ["--attempt", "1"], "verdict_fail.json"),
    ("verifier", "check", ["--attempt", "2"], "verdict_pass.json"),
])
def test_adapter_copies_examples_unchanged(
    module: str, operation: str, args: list[str], fixture: str, tmp_path: Path,
) -> None:
    output = tmp_path / "artifact.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "plugin/hooks/_stub.py"), module, operation, *args, "--out", str(output)],
        env={**os.environ, "HARNESS_NESTED": "1"}, capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == str(output) + "\n"
    assert output.read_bytes() == (ROOT / "schemas/examples" / fixture).read_bytes()
    assert "SYNTHETIC" in result.stderr
