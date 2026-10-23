"""Exercise the real runner/restart paths with aliased temporary ancestors."""

import json
from pathlib import Path
import tempfile
from typing import Any

import pytest

from eval.runner import core, republish, rerun_invalid
from eval.runner.audit import digest
from eval.runner.process import ProcessResult
from tests.eval.test_runner import Executor, setup
from tests.eval.test_restart_recovery import infrastructure_source, VERSION


@pytest.fixture
def aliased_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = tmp_path / 'real-temporary-parent'
    real.mkdir()
    alias = tmp_path / 'temporary-alias'
    alias.symlink_to(real, target_is_directory=True)
    original = tempfile.mkdtemp

    def create(*args: Any, **kwargs: Any) -> str:
        if kwargs.get('prefix') == 'lhm-eval-':
            kwargs['dir'] = alias
        return original(*args, **kwargs)

    monkeypatch.setattr(core.tempfile, 'mkdtemp', create)


@pytest.mark.parametrize('capture', ['exec-1.stderr', 'final-1.md'])
def test_runner_publishes_and_pins_captures_under_alias(setup: tuple[Path, Path, Path],
                                                       aliased_runtime: None, tmp_path: Path,
                                                       capture: str) -> None:
    root, config, out = setup
    executor = Executor()

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
            runtime = Path(entry['runtime'])
            # Pins are persisted before trusted grading, rather than backfilled later.
            for name in ('exec-1.stderr', 'final-1.md'):
                assert entry['segments'][0]['evidence_sha256'][name] == digest((runtime / name).read_bytes())
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            kwargs['stderr'].write_text('Executor diagnostics\n')
            Path(argv[argv.index('-o') + 1]).write_text('The task is done.\n')
        return result

    core.run(config, out, root, execute=execute, version=VERSION)
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    assert runtime.parent.is_symlink()
    pins = entry['segments'][0]['evidence_sha256']
    for name in ('exec-1.jsonl', 'exec-1.stderr', 'final-1.md'):
        assert pins[name] == digest((runtime / name).read_bytes())
        assert (out / 'bug-chunk-tail' / name).read_bytes() == (runtime / name).read_bytes()
    assert republish.republish(root, out)[0] == {
        'task_id': 'bug-chunk-tail', 'published': 0, 'existing': 3, 'unpinned': 0}
    target = out / 'bug-chunk-tail' / capture
    target.rename(tmp_path / 'previous-published-capture')
    assert republish.republish(root, out)[0] == {
        'task_id': 'bug-chunk-tail', 'published': 1, 'existing': 2, 'unpinned': 0}
    assert target.read_bytes() == (runtime / capture).read_bytes()
    assert 'republished_unpinned' not in (out / 'run-diagnostics.json').read_text()


def test_rerun_accepts_retained_runtime_parent_alias(setup: tuple[Path, Path, Path],
                                                    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                    aliased_runtime: None) -> None:
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    executor = Executor()
    executor.finished = True  # Regrade unselected tasks before the fresh executor.
    result = rerun_invalid.rerun_invalid(root, source, tmp_path / 'rerun', {'execution_interrupted'},
                                         execute=executor, version=VERSION)
    report = json.loads(result.read_text())
    assert executor.calls == 1
    assert all(task['outcome'] == 'pass' for task in report['tasks'])
