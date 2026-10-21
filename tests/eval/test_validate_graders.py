"""Use synthetic private roots to verify reference validation and safe output."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core, validate_graders


@pytest.fixture
def synthetic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repository = tmp_path / 'repository'
    public = repository / 'eval/tasks/synthetic'
    (public / 'workspace').mkdir(parents=True)
    (public / 'workspace/example.py').write_text('def answer() -> int: return 0\n')
    (public / 'expected.json').write_text(json.dumps({'expected_test_count': 1}))
    private = tmp_path / 'trusted'
    (private / 'synthetic').mkdir(parents=True)
    (private / 'synthetic/test_private_abc123.py').write_text(
        'import unittest\nfrom example import answer\n'
        'class Checks(unittest.TestCase):\n'
        ' def test_answer(self) -> None: self.assertEqual(answer(), 42)\n')
    reference = private / '.references/synthetic'
    reference.mkdir(parents=True)
    (reference / 'example.py').write_text('def answer() -> int: return 42\n')
    (reference / 'application.json').write_text(json.dumps({'files': {'example.py': 'example.py'}}))
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    return private, public


def test_validates_through_real_grading_on_copies(synthetic: tuple[Path, Path]) -> None:
    private, public = synthetic
    before = {p.relative_to(public): p.read_bytes() for p in public.rglob('*') if p.is_file()}
    row = validate_graders.validate_task(private, 'synthetic')
    assert row['valid_count'] == 1
    assert (row['public_passed'], row['public_failed']) == (0, 1)
    assert (row['reference_passed'], row['reference_failed']) == (1, 0)
    assert len(row['grader_sha256'][0]) == 64
    assert str(private) not in json.dumps(row)
    assert before == {p.relative_to(public): p.read_bytes() for p in public.rglob('*') if p.is_file()}


@pytest.mark.parametrize('broken', ['no-negative', 'reference', 'count'])
def test_rejects_invalid_grader_validation(synthetic: tuple[Path, Path], broken: str) -> None:
    private, public = synthetic
    if broken == 'no-negative':
        (public / 'workspace/example.py').write_text('def answer() -> int: return 42\n')
    elif broken == 'reference':
        (private / '.references/synthetic/example.py').write_text('def answer() -> int: return 0\n')
    else:
        (public / 'expected.json').write_text(json.dumps({'expected_test_count': 2}))
    assert validate_graders.validate_task(private, 'synthetic')['valid_count'] == 0


@pytest.mark.parametrize('source,target', [('example.py', '../escape.py'), ('../escape.py', 'example.py'),
                                        ('test_reference.py', 'example.py')])
def test_rejects_unsafe_reference_overlay(synthetic: tuple[Path, Path], source: str, target: str) -> None:
    private, public = synthetic
    reference = private / '.references/synthetic'
    (reference / source).write_text('value = 42\n')
    (reference / 'application.json').write_text(json.dumps({'files': {source: target}}))
    with pytest.raises(ValueError, match='Unsafe'):
        validate_graders.apply_reference(reference, public / 'workspace')


def test_cli_never_prints_private_paths_on_failure(synthetic: tuple[Path, Path],
                                                monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    private, _ = synthetic
    monkeypatch.setattr('sys.argv', ['validate_graders', '--private-root', str(private), '--tasks', 'all'])
    def error(*args: Any) -> None:
        raise RuntimeError(str(private))
    monkeypatch.setattr(validate_graders, 'validate_task', error)
    assert validate_graders.main() == 1
    output = capsys.readouterr()
    assert str(private) not in output.out + output.err
    assert json.loads(output.out.splitlines()[-1])['invalid_count'] == 1


def test_cli_success_includes_runner_taskset_hash(synthetic: tuple[Path, Path],
                                                monkeypatch: pytest.MonkeyPatch,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    private, public = synthetic
    monkeypatch.setattr('sys.argv', ['validate_graders', '--private-root', str(private), '--tasks', 'all'])
    monkeypatch.setattr(core, 'public_files', lambda task: sorted(p for p in public.rglob('*') if p.is_file()))
    assert validate_graders.main() == 0
    output = capsys.readouterr()
    rows = [json.loads(line) for line in output.out.splitlines()]
    assert rows[-1]['valid_count'] == 1
    assert rows[-1]['invalid_count'] == 0
    from eval.runner.audit import PrivateGraders
    assert rows[-1]['task_set_sha256'] == core.taskset_digest({
        'synthetic': PrivateGraders.load(private, 'synthetic', core.REPOSITORY)})
    assert str(private) not in output.out + output.err
