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
        assert meta['frozen'] is True
        assert meta['version'] == 1
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
            assert meta['grader_status'] == expected['grader_status'] == 'validated_external'
            assert f'| {task.name} | validated |' in pending


def test_published_validation_counts_and_hashes_cover_every_task() -> None:
    import re
    summary = (REPOSITORY / 'eval/GRADERS-PENDING.md').read_text()
    rows = [line.split('|')[1:-1] for line in summary.splitlines() if '| validated |' in line]
    assert len(rows) == 120
    for cells in rows:
        task, status, original, reference, hashes = [cell.strip() for cell in cells]
        expected = json.loads((REPOSITORY / 'eval/tasks' / task / 'expected.json').read_text())
        passed, failed = map(int, original.split('/'))
        reference_passed, reference_failed = map(int, reference.split('/'))
        assert passed + failed == expected['expected_test_count']
        assert failed > 0
        assert reference_passed == expected['expected_test_count']
        assert reference_failed == 0
        assert all(re.fullmatch('[a-f0-9]{64}', value.strip()) for value in hashes.split(','))
