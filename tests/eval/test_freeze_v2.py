"""Freeze host procedure uses synthetic graders, tracked public inputs and no models."""

import json
from pathlib import Path
import sys
from typing import Any

import pytest

from eval import freeze_v2
from eval.runner import core
from eval.runner.audit import PrivateGraders


def test_full_v2_configurations_share_population_digest(tmp_path: Path) -> None:
    configs = [core.load_config(core.REPOSITORY / f'eval/configs/full-v2-{name}.yaml')
               for name in ('a', 'b', 'harness')]
    tasks = configs[0]['tasks']
    assert len(tasks) == len(set(tasks)) == 100
    assert configs[1]['task_population'] == tasks == configs[2]['tasks']
    single_session = [task for task in tasks if not json.loads(
        (core.task_directory(configs[0]) / task / 'meta.json').read_text())['two_session']]
    assert configs[1]['tasks'] == single_session and len(single_session) == 80

    # Use synthetic grader bytes only; never load the host's private grader root.
    source = tmp_path / 'test_synthetic.py'
    source.write_text('# synthetic population digest fixture\n')
    graders = {task: PrivateGraders(tmp_path, (source,)) for task in tasks}
    population_digests = [core.configured_digest(
        {task: graders[task] for task in config.get('task_population', config['tasks'])}, config,
    ) for config in configs]
    assert len(set(population_digests)) == 1
    selected_b = {task: graders[task] for task in configs[1]['tasks']}
    assert core.configured_digest(selected_b, configs[1]) != population_digests[1]


def test_host_digest_matches_runner_and_changes_with_private_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = core.load_config(core.REPOSITORY / 'eval/configs/full-v2-a.yaml')
    graders = {}
    for task in config['tasks']:
        directory = tmp_path / task
        directory.mkdir()
        source = directory / 'test_private.py'
        source.write_text(f'# synthetic grader for {task}\n')
        graders[task] = PrivateGraders(directory, (source,))
    monkeypatch.setattr(PrivateGraders, 'load', lambda root, task, repo, **kw: graders[task])
    summary = freeze_v2.freeze_summary(tmp_path)
    assert summary['task_set_sha256'] == core.configured_digest(graders, config)
    assert summary['task_count'] == 100 and summary['two_session_count'] == 20
    assert summary['counts_by_type'] == {'bug_fix': 20, 'feature_plus_test': 20,
                                         'multiple_requirements': 40, 'constrained_refactoring': 20}
    assert len(summary['counts_by_family']) == 20
    assert set(summary['counts_by_family'].values()) == {5}
    selections = summary['configurations']
    assert [selections[f'full-v2-{name}']['task_count'] for name in ('a', 'b', 'harness')] == [100, 80, 100]
    assert selections['full-v2-a']['selected_task_set_sha256'] == summary['task_set_sha256']
    assert selections['full-v2-harness']['selected_task_set_sha256'] == summary['task_set_sha256']
    assert selections['full-v2-b']['selected_task_set_sha256'] != summary['task_set_sha256']
    assert str(tmp_path) not in json.dumps(summary)
    next(iter(graders.values())).files[0].write_text('# changed private contents\n')
    assert freeze_v2.freeze_summary(tmp_path)['task_set_sha256'] != summary['task_set_sha256']


def test_host_failure_does_not_publish_private_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(root: Path) -> dict[str, Any]:
        raise ValueError(f'Sensitive private location {root}')

    monkeypatch.setattr(freeze_v2, 'freeze_summary', fail)
    monkeypatch.setattr(sys, 'argv', ['freeze_v2', '--private-root', '/synthetic-secret'])
    assert freeze_v2.main() == 1
    captured = capsys.readouterr()
    assert not captured.out and '/synthetic-secret' not in captured.err
