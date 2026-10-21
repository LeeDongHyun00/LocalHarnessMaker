"""Check real local timeout handling without any model call."""

import os
from pathlib import Path
import sys

from eval.runner.process import run_process


def test_timeout_reaps_process_and_retains_output(tmp_path: Path) -> None:
    output, error = tmp_path / "stdout", tmp_path / "stderr"
    result = run_process(
        [sys.executable, "-I", "-c", "import time; print('started', flush=True); time.sleep(10)"],
        cwd=tmp_path, env={"PATH": os.defpath}, stdin="", stdout=output, stderr=error, timeout=0.2,
    )
    assert result.timed_out
    assert result.returncode < 0
    assert output.read_text() == "started\n"
