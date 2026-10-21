"""Inspect public candidates without generating or loading hidden graders."""

import ast
import json
from pathlib import Path

from eval.runner.core import REPOSITORY


def test_public_inventory_contains_100_single_and_20_two_session_tasks() -> None:
    root = REPOSITORY / 'eval/tasks'
    tasks = sorted(p for p in root.iterdir() if p.is_dir())
    metas = [json.loads((p / 'meta.json').read_text()) for p in tasks]
    assert sum(not m['two_session'] for m in metas) == 100
    assert sum(m['two_session'] for m in metas) == 20
    assert len({m['id'] for m in metas}) == 120
    assert {m['type'] for m in metas} == {'bug_fix', 'feature_plus_test', 'multiple_requirements', 'constrained_refactoring'}
    pending = (REPOSITORY / 'eval/GRADERS-PENDING.md').read_text()
    for task, meta in zip(tasks, metas):
        assert meta['id'] == task.name
        assert meta['frozen'] is False
        assert (task / 'prompt.md').read_text().strip()
        expected = json.loads((task / 'expected.json').read_text())
        assert expected['expected_exit_code'] == 0
        assert (task / 'workspace').is_dir()
        for source in (task / 'workspace').rglob('*.py'):
            ast.parse(source.read_text())
        assert not list(task.rglob('test_*'))
        if meta['two_session']:
            day2 = (task / meta['day2_prompt']).read_text()
            assert 'Day 2' in day2 and 'day-1 API compatible' in day2
        if task.name != 'bug-chunk-tail':
            assert meta['grader_status'] == expected['grader_status'] == 'pending'
            assert f'| {task.name} | pending |' in pending
