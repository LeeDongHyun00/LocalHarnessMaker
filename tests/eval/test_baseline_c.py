"""Metadata-only C selection and standalone config invariants."""

from collections import Counter
import json

import pytest

from eval.runner.core import REPOSITORY, load_config
from eval.runner.static_templates import PLACEHOLDER, load_templates
from eval.tools.prepare_c import select


def test_subset_reproducible_balanced_disjoint_and_unfilled() -> None:
    manifest = json.loads((REPOSITORY / 'eval/baselines/c-subset.json').read_text())
    rows = manifest['tasks']
    assert rows == select(REPOSITORY / 'eval/tasks', 0)
    assert len(rows) == 20
    assert set(Counter(r['type'] for r in rows).values()) == {5}
    assert len({r['family'] for r in rows}) == 20
    config = load_config(REPOSITORY / 'eval/configs/full-c.yaml')
    assert config['tasks'] == sorted(r['task_id'] for r in rows)
    a = load_config(REPOSITORY / 'eval/configs/full-a.yaml')
    assert config['task_population'] == a['tasks']
    assert len(load_config(REPOSITORY / 'eval/configs/full-b.yaml')['task_population']) == 120
    for key in a.keys() - {'name', 'tasks', 'task_timeout_seconds'}:
        assert config[key] == a[key]
    template = (REPOSITORY / 'eval/baselines/template.md').read_text()
    assert template.count(PLACEHOLDER) == 6
    for row in rows:
        skeleton = (REPOSITORY / f"eval/baselines/c/{row['task_id']}.md").read_text()
        assert skeleton.endswith(template)
        assert f"eval/tasks/{row['task_id']}/prompt.md" in skeleton
    with pytest.raises(ValueError, match='Unfilled'):
        load_templates(config, REPOSITORY)
