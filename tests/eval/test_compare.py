"""Paired comparison rejects incompatible reports and preserves cluster pairing."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from eval.runner.compare import compare, main, markdown


def report() -> dict[str, Any]:
    return {'metadata': {'codex_version': 'codex-cli unit', 'task_set_sha256': 'a' * 64,
                         'seed': 0, 'executor_model': 'sol', 'cost_basis': 'api_equivalent_usd',
                         'pricing': {}, 'reasoning_effort': 'medium'},
            'accounting': {'attempted_tasks': 2},
            'tasks': [{'task_id': str(i), 'task_type': 'bug_fix', 'two_session': False,
                       'outcome': 'pass', 'attempts': 1, 'costs': {'total_usd': 2}, 'handoff': None}
                      for i in range(2)]}


def test_identical_pairs_are_exact_and_different_effort_allowed() -> None:
    left, right = report(), report()
    right['metadata']['reasoning_effort'] = 'max'
    result = compare(left, right)
    assert result['status'] == 'valid'
    for name, expected in [('pass_rate_difference', 0), ('cost_per_pass_difference', 0), ('cost_per_pass_ratio', 1)]:
        m = result['overall']['paired'][name]
        assert m['value'] == m['ci95']['lower'] == m['ci95']['upper'] == expected
        assert m['sample_size'] == 2
    assert result == compare(left, right)
    assert result['by_task_type']['bug_fix'] == result['overall']
    assert 'cost_per_pass ratio' in markdown(result)


@pytest.mark.parametrize('field', ['codex_version', 'task_set_sha256', 'seed', 'executor_model', 'pricing'])
def test_mismatched_provenance_refused(field: str) -> None:
    left, right = report(), report()
    right['metadata'][field] = 'different'
    with pytest.raises(ValueError, match='different'):
        compare(left, right)


def test_matched_valid_intersection_and_diagnostic() -> None:
    left, right = report(), report()
    left['tasks'].append({**deepcopy(left['tasks'][0]), 'task_id': 'unmatched'})
    left['accounting']['attempted_tasks'] += 1
    right['tasks'][0]['outcome'] = 'invalid'
    result = compare(left, right)
    assert result['status'] == 'diagnostic'
    assert result['invalid_matched_tasks'] == ['0']
    assert result['excluded_left'] == ['unmatched']
    assert result['overall']['left']['cost_per_pass']['sample_size'] == 1
    assert result['overall']['left']['cost_per_pass']['value'] == 2


@pytest.mark.parametrize('mode', ['missing_cost', 'zero_passes', 'zero_bootstrap', 'zero_ratio'])
def test_undefined_accounting_and_denominators(mode: str) -> None:
    left, right = report(), report()
    if mode == 'missing_cost':
        right['tasks'][0]['costs']['total_usd'] = None
    elif mode == 'zero_passes':
        for task in right['tasks']:
            task['outcome'] = 'fail'
    elif mode == 'zero_bootstrap':
        right['tasks'][0]['outcome'] = 'fail'
    else:
        for task in right['tasks']:
            task['costs']['total_usd'] = 0
    item = compare(left, right)['overall']['paired']['cost_per_pass_ratio']
    assert item['value'] is None and item['ci95']['lower'] is None
    assert item['undefined_reason']


def test_handoff_and_type_splits() -> None:
    left, right = report(), report()
    for side in (left, right):
        side['tasks'][0].update(two_session=True, task_type='feature_plus_test',
            handoff={'day2_pass': True, 'user_restated_day1_context': False})
    right['tasks'][0]['handoff']['user_restated_day1_context'] = True
    result = compare(left, right)
    assert result['overall']['left']['handoff_success']['value'] == 1
    assert result['overall']['right']['handoff_success']['value'] == 0
    assert set(result['by_task_type']) == {'bug_fix', 'feature_plus_test'}


def test_cli_input_error_stdout_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                      capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, 'argv', ['compare', str(tmp_path / 'missing'), 'missing', '--out', str(tmp_path / 'out')])
    assert main() == 1
    captured = capsys.readouterr()
    assert captured.out == '' and 'Input error' in captured.err


def test_cli_schema_validation_and_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    # Generate a schema-valid report through the mocked runner fixture helper.
    from tests.eval.test_runner import Executor
    from eval.runner.core import REPOSITORY, run
    home = tmp_path / 'home'
    home.mkdir()
    (home / 'auth.json').write_text('{}')
    monkeypatch.setenv('CODEX_HOME', str(home))
    private = tmp_path / 'private/bug-chunk-tail'
    private.mkdir(parents=True)
    (private / 'test_private_synthetic.py').write_text(
        'import unittest\nclass Test(unittest.TestCase):\n def test_one(self): pass\n def test_two(self): pass\n def test_three(self): pass\n')
    cfg = tmp_path / 'config.yaml'
    cfg.write_text((REPOSITORY / 'eval/configs/pilot.yaml').read_text())
    source = run(cfg, tmp_path / 'run', private.parent, execute=Executor(), version='codex-cli 0.162.0-alpha.17.2')
    capsys.readouterr()
    destination = tmp_path / 'comparison'
    monkeypatch.setattr(sys, 'argv', ['compare', str(source), str(source), '--out', str(destination)])
    assert main() == 0
    assert capsys.readouterr().out == str(destination) + '\n'
    result = json.loads((destination / 'comparison.json').read_text())
    assert len(result['sources'][0]['sha256']) == 64
    assert (destination / 'comparison.md').is_file()
