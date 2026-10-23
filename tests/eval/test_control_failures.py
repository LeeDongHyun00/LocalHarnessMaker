"""Classify structured control failures without guessing from configured budgets."""

from pathlib import Path
from typing import Any

import pytest

from eval.runner import harness
from eval.runner.core import REPOSITORY
from eval.runner.process import ProcessResult


@pytest.mark.parametrize('stderr,process,expected', [
    ('control_failure {"reason":"deadline"}\n', ProcessResult(2), harness.ControlTimeout),
    ('control_failure {"reason":"transport"}\n', ProcessResult(2), harness.HarnessError),
    ('deadline exceeded\n', ProcessResult(2), harness.HarnessError),
    ('control_failure {broken\n', ProcessResult(2), harness.HarnessError),
    ('control_failure []\n', ProcessResult(2), harness.HarnessError),
    ('control_failure {"message":"deadline", "reason":"transport"}\n', ProcessResult(2), harness.HarnessError),
    ('other diagnostic\n', ProcessResult(-9, timed_out=True), harness.ControlTimeout),
])
def test_control_failure_requires_deadline_evidence(tmp_path: Path, stderr: str,
                                                    process: ProcessResult,
                                                    expected: type[harness.HarnessError]) -> None:
    guard = harness.ControlFiles(tmp_path, {}, lambda: None)

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        kwargs['stdout'].write_text('')
        kwargs['stderr'].write_text(stderr)
        return process

    with pytest.raises(harness.HarnessError) as raised:
        harness.invoke('controller', 'contract', [], tmp_path / 'contract.json', repository=REPOSITORY,
                       timeout=98765, execute=execute, guard=guard)
    assert type(raised.value) is expected
    guard.verify()
    assert 'contract.stderr' in guard.hashes and 'contract.control.json' in guard.hashes
