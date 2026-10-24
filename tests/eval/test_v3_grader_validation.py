"""V3 candidate validation is strict without requiring any held-out content."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core, validate_graders
from eval.runner.audit import PrivateGraders


@pytest.fixture
def candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repository = tmp_path / 'repository'
    public = repository / 'eval/tasks-v3/v3-synthetic'
    (public / 'workspace').mkdir(parents=True)
    (public / 'workspace/answer.py').write_text('def answer() -> int: return 0\n')
    (public / 'prompt.md').write_text('XY1. Return the synthetic value.\n')
    (public / 'expected.json').write_text(json.dumps({'expected_test_count': 1}))
    private = tmp_path / 'trusted'
    grader = private / 'v3-synthetic'
    grader.mkdir(parents=True)
    (grader / 'test_synthetic.py').write_text(
        'import unittest\nfrom answer import answer\nclass Checks(unittest.TestCase):\n'
        ' def test_answer(self) -> None: self.assertEqual(answer(), 24)\n')
    (grader / 'coverage.json').write_text(json.dumps({'XY1':['Checks.test_answer']}))
    reference = private / '.references/v3-synthetic'
    reference.mkdir(parents=True)
    (reference / 'answer.py').write_text('def answer() -> int: return 24\n')
    (reference / 'application.json').write_text(json.dumps({'files':{'answer.py':'answer.py'}}))
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    return private, public


def test_v3_location_coverage_and_candidate_digest(candidate: tuple[Path, Path]) -> None:
    private, public = candidate
    row = validate_graders.validate_task(private, 'v3-synthetic')
    assert (row['valid_count'],row['requirement_count'],row['covered_requirement_count']) == (1,1,1)
    grader = PrivateGraders.load(private, 'v3-synthetic', core.REPOSITORY)
    assert grader.public_root == public.parent
    config = {'task_root':'eval/tasks-v3'}
    first = validate_graders.validation_digest({'v3-synthetic':grader}, config)
    (public / 'meta.json').write_text('{"frozen":false}\n')
    assert first != validate_graders.validation_digest({'v3-synthetic':grader}, config)


def test_v3_missing_day2_coverage_and_empty_inventory_fail(candidate: tuple[Path, Path]) -> None:
    private, public = candidate
    (public / 'day2.md').write_text('NEXT1. Preserve the value.\n')
    assert validate_graders.validate_task(private, 'v3-synthetic')['valid_count'] == 0
    (public / 'day2.md').write_text('No numbered requirements.\n')
    (public / 'prompt.md').write_text('No numbered requirements.\n')
    assert validate_graders.validate_task(private, 'v3-synthetic')['valid_count'] == 0


def test_v3_assertion_overlap_across_public_population(candidate: tuple[Path, Path]) -> None:
    private, _ = candidate
    other = core.REPOSITORY / 'eval/tasks-v2/v2-other'
    other.mkdir(parents=True)
    (other / 'prompt.md').write_text('def test_answer(self) -> None: self.assertEqual(answer(), 24)\n')
    row = validate_graders.validate_task(private, 'v3-synthetic')
    assert row['valid_count'] == 0 and row['shared_assertion_line_count'] == 1
    with pytest.raises(ValueError, match='independent'):
        validate_graders.mutate_task(private, 'v3-synthetic', 100)


def test_v3_all_mutations_and_targeted_population(candidate: tuple[Path, Path]) -> None:
    private, _ = candidate
    targeted = private / '.mutants/v3-synthetic'
    targeted.mkdir(parents=True)
    (targeted / 'wrong.py').write_text('def answer() -> int: return -99\n')
    (targeted / 'manifest.json').write_text(json.dumps({'mutations':[{'source':'wrong.py','target':'answer.py'}]}))
    row = validate_graders.mutate_task(private, 'v3-synthetic', 100)
    assert (row['generated'],row['targeted'],row['executed'],row['killed']) == (2,1,3,3)
    assert row['unexecuted'] == row['error_count'] == row['survived'] == 0
    partial = validate_graders.mutate_task(private, 'v3-synthetic', 1)
    assert partial['unexecuted'] == 2


def test_v3_timeout_is_unresolved(candidate: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    private, _ = candidate
    original = core.grade
    calls = 0
    def grade(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return original(*args, **kwargs)
        return {'result':'error','timed_out':True,'failed_tests':0,'total_tests':0}
    monkeypatch.setattr(core, 'grade', grade)
    row = validate_graders.mutate_task(private, 'v3-synthetic', 100)
    assert (row['killed'],row['executed'],row['error_count']) == (0,0,2)


@pytest.mark.parametrize('changes', [{'survived':1}, {'unexecuted':1}, {'error_count':1}])
def test_v3_cli_rejects_incomplete_population(candidate: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
                                             changes: dict[str, int], capsys: pytest.CaptureFixture[str]) -> None:
    private, _ = candidate
    row = {'task_id':'v3-synthetic','killed':99,'survived':0,'recorded_equivalent':0,
           'generated':100,'unexecuted':0,'error_count':0,**changes}
    monkeypatch.setattr(validate_graders, 'mutate_task', lambda *args: row)
    monkeypatch.setattr('sys.argv', ['validate_graders','--private-root',str(private),'--tasks','v3-synthetic','--mutants','100'])
    assert validate_graders.main() == 1
    assert str(private) not in capsys.readouterr().out


def test_v3_equivalence_is_bound_to_workspace_and_grader(candidate: tuple[Path, Path]) -> None:
    private, public = candidate
    grader = private / 'v3-synthetic/test_synthetic.py'
    grader.write_text(grader.read_text().replace('self.assertEqual(answer(), 24)',
                                               'self.assertIsInstance(answer(), int)'))
    first = validate_graders.mutate_task(private, 'v3-synthetic', 100)
    assert first['survived'] == 1
    records = private / '.mutation-records'
    survivor = next(row for row in json.loads((records / 'v3-synthetic.review.json').read_text())
                    if row['outcome'] == 'survived')
    review = records / 'v3-synthetic.equivalences.json'
    review.write_text(json.dumps({survivor['id']:{'reason':'Synthetic equivalence review', 'reviewer':'fixture'}}))
    assert validate_graders.mutate_task(private, 'v3-synthetic', 100)['recorded_equivalent'] == 1
    (public / 'workspace/extra.txt').write_text('Changed public specification bytes.\n')
    assert validate_graders.mutate_task(private, 'v3-synthetic', 100)['recorded_equivalent'] == 0


@pytest.mark.parametrize('source,target', [('../escape.py','answer.py'), ('wrong.py','../answer.py')])
def test_v3_targeted_mutations_are_confined(candidate: tuple[Path, Path], source: str, target: str) -> None:
    private, _ = candidate
    root = private / '.mutants/v3-synthetic'
    root.mkdir(parents=True)
    (root / source).write_text('def answer() -> int: return 77\n')
    (root / 'manifest.json').write_text(json.dumps({'mutations':[{'source':source,'target':target}]}))
    with pytest.raises(ValueError, match='Unsafe targeted'):
        validate_graders.mutate_task(private, 'v3-synthetic', 100)
