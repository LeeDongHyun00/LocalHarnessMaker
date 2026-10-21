"""Check that the initial evaluation fixture detects its intended defect."""

from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest


TASK = Path(__file__).resolve().parents[2] / "eval/tasks/bug-chunk-tail"


def grade_fixture(destination: Path, *, corrected: bool) -> subprocess.CompletedProcess[str]:
    """Grade a private copy, never placing tests into the initial workspace."""
    shutil.copytree(TASK / "workspace", destination)
    value = os.environ.get("LHM_PRIVATE_GRADERS")
    if not value:
        pytest.skip("External graders are not configured in this trusted test process")
    graders = list((Path(value) / TASK.name).glob("test_*.py"))
    assert graders, "External task graders are missing"
    for grader in graders:
        shutil.copy2(grader, destination)
    if corrected:
        source = destination / "chunking.py"
        source.write_text(source.read_text().replace("len(items) - 1", "len(items)"))
    return subprocess.run(
        [sys.executable, "-I", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py", "-v"],
        cwd=destination,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def test_buggy_fixture_fails_all_three_checks(tmp_path: Path) -> None:
    result = grade_fixture(tmp_path / "buggy", corrected=False)
    assert result.returncode == 1, result.stderr
    assert "Ran 3 tests" in result.stderr
    assert "FAILED (failures=3)" in result.stderr


def test_reference_fix_passes_all_three_checks(tmp_path: Path) -> None:
    result = grade_fixture(tmp_path / "corrected", corrected=True)
    assert result.returncode == 0, result.stderr
    assert "Ran 3 tests" in result.stderr
    assert "\nOK\n" in result.stderr
