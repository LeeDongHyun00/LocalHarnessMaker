"""Check that the initial evaluation fixture detects its intended defect."""

from pathlib import Path
import shutil
import subprocess
import sys


TASK = Path(__file__).resolve().parents[2] / "eval/tasks/bug-chunk-tail"


def grade_fixture(destination: Path, *, corrected: bool) -> subprocess.CompletedProcess[str]:
    """Grade a private copy, never placing tests into the initial workspace."""
    shutil.copytree(TASK / "workspace", destination)
    shutil.copy2(TASK / "hidden_tests/test_chunking.py", destination)
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
