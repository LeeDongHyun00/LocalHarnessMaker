"""Offline cost-gate coverage for approved recovery subsets."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core


@pytest.fixture
def estimated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    config = json.loads((core.REPOSITORY / 'eval/configs/full-v2-harness.yaml').read_text())
    monkeypatch.setattr(core, 'REPOSITORY', tmp_path)
    (tmp_path / 'eval/configs').mkdir(parents=True)
    core.write_json(tmp_path / 'eval/configs/full-v2-harness.yaml', config)
    estimate = tmp_path / 'eval/reports/full-v2-harness-estimate.md'
    estimate.parent.mkdir(parents=True)
    estimate.write_text('Synthetic approved planning estimate.\n')
    day2 = tmp_path / config['task_root'] / config['tasks'][4] / 'day2.md'
    day2.parent.mkdir(parents=True)
    day2.write_text('Synthetic second session.\n')
    return config


def test_recovery_subset_matches_estimate_and_prints_own_bound(
        estimated: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    subset = dict(estimated, tasks=estimated['tasks'][:16])
    record = core.require_call_estimate(subset, recovery=True)
    bound = core.paid_call_bound(subset)
    assert bound >= 10 and bound < core.paid_call_bound(estimated)
    assert record == {'matched_estimate': 'eval/reports/full-v2-harness-estimate.md',
                      'paid_call_bound': bound, 'recovery_subset': True}
    output = capsys.readouterr().err
    assert f'batch upper bound {bound} paid calls' in output
    assert record['matched_estimate'] in output
    assert 'recovery subset of an approved configuration' in output
    with pytest.raises(ValueError, match='STOP-3'):
        core.require_call_estimate(subset)  # Ordinary run remains exact-match only.


@pytest.mark.parametrize('field,value', [
    ('model', 'other-model'), ('reasoning_effort', 'max'), ('harness', False),
    ('control_backend', 'cheap_api'), ('reinstruction_limit', 3), ('retry_limit', 1),
    ('service_tier', 'standard'), ('task_root', 'eval/other-tasks'), ('seed', 1),
    ('timeout_seconds', 42), ('codex_version', 'other-version'), ('extra_setting', True),
    ('task_population', ['different-task']), ('name', 'unestimated-name'),
])
def test_changed_subset_setting_is_refused(estimated: dict[str, Any], field: str, value: Any) -> None:
    subset = copy.deepcopy(estimated)
    subset.update(tasks=estimated['tasks'][:16])
    subset[field] = value
    with pytest.raises(ValueError, match='STOP-3'):
        core.require_call_estimate(subset, recovery=True)


@pytest.mark.parametrize('recovery', [False, True])
def test_unestimated_full_config_is_refused(estimated: dict[str, Any], recovery: bool) -> None:
    unestimated = dict(estimated, seed=999)
    with pytest.raises(ValueError, match='STOP-3'):
        core.require_call_estimate(unestimated, recovery=recovery)


def test_recovery_cannot_add_tasks(estimated: dict[str, Any]) -> None:
    subset = dict(estimated, tasks=estimated['tasks'][:16] + ['unapproved-task'])
    with pytest.raises(ValueError, match='STOP-3'):
        core.require_call_estimate(subset, recovery=True)


def test_recovery_small_batch_retains_optional_estimate(estimated: dict[str, Any]) -> None:
    subset = dict(estimated, tasks=estimated['tasks'][:1])
    record = core.require_call_estimate(subset, recovery=True)
    assert record['paid_call_bound'] == core.paid_call_bound(subset) < 10
    assert record['matched_estimate'] == 'eval/reports/full-v2-harness-estimate.md'


def install_estimate(config: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Exercise real estimate matching against synthetic files during recovery."""
    repository = tmp_path / 'estimate-repository'
    name = config['name']
    (repository / 'eval/configs').mkdir(parents=True)
    core.write_json(repository / f'eval/configs/{name}.yaml', config)
    estimate = repository / f'eval/reports/{name}-estimate.md'
    estimate.parent.mkdir(parents=True, exist_ok=True)
    estimate.write_text('Synthetic planning estimate.\n')
    for task in config['tasks']:
        if (core.task_directory(config) / task / 'day2.md').is_file():
            path = repository / config.get('task_root', 'eval/tasks') / task / 'day2.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic day 2.\n')
    from tests.eval.test_runner import require_call_estimate as original

    def guard(batch: dict[str, Any], judges: dict[str, int] | None = None, *,
              recovery: bool = False) -> dict[str, Any]:
        with monkeypatch.context() as context:
            context.setattr(core, 'REPOSITORY', repository)
            return original(batch, judges, recovery=recovery)

    monkeypatch.setattr(core, 'require_call_estimate', guard)
    return f'eval/reports/{name}-estimate.md'
