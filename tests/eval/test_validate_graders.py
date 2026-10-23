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
    (public / 'prompt.md').write_text('Return the specified synthetic answer.')
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


def test_validation_keeps_grading_and_runtime_inside_private_root(
    synthetic: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    private, _ = synthetic
    original = core.grade
    copies = []

    def inspect(*args: Any, **kwargs: Any) -> dict[str, Any]:
        assert Path(args[2]).is_relative_to(private)
        assert kwargs['retention_root'].is_relative_to(private)
        result = original(*args, **kwargs)
        copies.append(Path(result['copy_path']))
        assert copies[-1].is_relative_to(private)
        return result

    monkeypatch.setattr(core, 'grade', inspect)
    assert validate_graders.validate_task(private, 'synthetic')['valid_count'] == 1
    assert len(copies) == 2
    assert all(not path.exists() for path in copies)


def test_mutation_counts_and_stale_equivalence(synthetic: tuple[Path, Path]) -> None:
    private, public = synthetic
    row = validate_graders.mutate_task(private, 'synthetic', 10)
    assert row == {'task_id': 'synthetic', 'killed': 2, 'survived': 0, 'recorded_equivalent': 0}
    # A deliberately weak synthetic oracle permits the increment mutant.
    grader = next((private / 'synthetic').glob('test_*.py'))
    grader.write_text(grader.read_text().replace('self.assertEqual(answer(), 42)', 'self.assertIsInstance(answer(), int)'))
    row = validate_graders.mutate_task(private, 'synthetic', 10)
    assert row['survived'] == 1
    records = private / '.mutation-records'
    survivor = next(item for item in json.loads((records / 'synthetic.review.json').read_text())
                    if item['outcome'] == 'survived')
    (records / 'synthetic.equivalences.json').write_text(json.dumps({survivor['id']: {'reason': 'Synthetic review only'}}))
    assert validate_graders.mutate_task(private, 'synthetic', 10)['recorded_equivalent'] == 1
    (public / 'prompt.md').write_text('Changed synthetic contract')
    assert validate_graders.mutate_task(private, 'synthetic', 10)['recorded_equivalent'] == 0


def test_mutation_cli_counts_only_and_private_cleanup(synthetic: tuple[Path, Path],
                                                      monkeypatch: pytest.MonkeyPatch,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
    private, _ = synthetic
    original = core.grade
    copies = []

    def inspect(*args: Any, **kwargs: Any) -> dict[str, Any]:
        assert Path(args[2]).is_relative_to(private)
        assert kwargs['retention_root'].is_relative_to(private)
        result = original(*args, **kwargs)
        copies.append(Path(result['copy_path']))
        return result

    monkeypatch.setattr(core, 'grade', inspect)
    monkeypatch.setattr('sys.argv', ['validate_graders', '--private-root', str(private),
                                    '--tasks', 'all', '--mutants', '10'])
    assert validate_graders.main() == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == {'task_id': 'synthetic', 'killed': 2,
                                      'survived': 0, 'recorded_equivalent': 0}
    assert str(private) not in output.out + output.err
    assert all(path.is_relative_to(private) and not path.exists() for path in copies)


def test_mutation_requires_passing_reference_control(synthetic: tuple[Path, Path]) -> None:
    private, _ = synthetic
    (private / '.references/synthetic/example.py').write_text('def answer() -> int: return 0\n')
    with pytest.raises(ValueError, match='control'):
        validate_graders.mutate_task(private, 'synthetic', 10)


@pytest.fixture
def synthetic_v2(synthetic: tuple[Path, Path]) -> tuple[Path, Path]:
    import shutil
    private, old = synthetic
    public = core.REPOSITORY / 'eval/tasks-v2/v2-synthetic'
    shutil.copytree(old, public)
    shutil.copytree(private / 'synthetic', private / 'v2-synthetic')
    shutil.copytree(private / '.references/synthetic', private / '.references/v2-synthetic')
    (public / 'prompt.md').write_text('R1. Return the specified synthetic answer.\n')
    (private / 'v2-synthetic/coverage.json').write_text(json.dumps({'R1': ['Checks.test_answer']}))
    return private, public


def test_v2_validation_checks_executed_requirement_mapping(synthetic_v2: tuple[Path, Path]) -> None:
    private, public = synthetic_v2
    row = validate_graders.validate_task(private, 'v2-synthetic')
    assert row['valid_count'] == 1
    assert row['covered_requirement_count'] == row['requirement_count'] == 1
    assert row['uncovered_requirement_count'] == 0
    (public / 'day2.md').write_text('D1. Preserve the earlier answer.\n')
    row = validate_graders.validate_task(private, 'v2-synthetic')
    assert row['valid_count'] == 0 and row['uncovered_requirement_count'] == 1
    coverage = private / 'v2-synthetic/coverage.json'
    coverage.write_text(json.dumps({'R1':['Checks.test_answer'], 'D1':['Checks.never_executed']}))
    assert validate_graders.validate_task(private, 'v2-synthetic')['valid_count'] == 0
    coverage.write_text(json.dumps({'R1':['Checks.test_answer'], 'D1':['Checks.test_answer']}))
    assert validate_graders.validate_task(private, 'v2-synthetic')['valid_count'] == 1


def test_candidate_validation_hash_tracks_uncommitted_bytes(synthetic_v2: tuple[Path, Path]) -> None:
    from eval.runner.audit import PrivateGraders
    private, public = synthetic_v2
    graders = {'v2-synthetic': PrivateGraders.load(private, 'v2-synthetic', core.REPOSITORY)}
    config = {'task_root':'eval/tasks-v2'}
    first = validate_graders.validation_digest(graders, config)
    (public / 'prompt.md').write_text('R1. Changed specification.\n')
    assert first != validate_graders.validation_digest(graders, config)
    (public / 'untracked.txt').write_text('candidate bytes')
    second = validate_graders.validation_digest(graders, config)
    (public / 'untracked.txt').write_text('changed bytes')
    assert second != validate_graders.validation_digest(graders, config)


def test_v2_mutation_equivalence_expires_when_day2_changes(synthetic_v2: tuple[Path, Path]) -> None:
    private, public = synthetic_v2
    grader = next((private / 'v2-synthetic').glob('test_*.py'))
    grader.write_text(grader.read_text().replace('self.assertEqual(answer(), 42)', 'self.assertIsInstance(answer(), int)'))
    (public / 'day2.md').write_text('D1. Keep the answer.\n')
    assert validate_graders.mutate_task(private, 'v2-synthetic', 10)['survived'] == 1
    records = private / '.mutation-records'
    survivor = next(item for item in json.loads((records / 'v2-synthetic.review.json').read_text())
                    if item['outcome'] == 'survived')
    (records / 'v2-synthetic.equivalences.json').write_text(json.dumps({survivor['id']:{'reason':'Synthetic equivalence only'}}))
    assert validate_graders.mutate_task(private, 'v2-synthetic', 10)['recorded_equivalent'] == 1
    (public / 'day2.md').write_text('D1. Changed specification.\n')
    assert validate_graders.mutate_task(private, 'v2-synthetic', 10)['recorded_equivalent'] == 0
