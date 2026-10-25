"""Freeze identity checks use synthetic private inputs unless the host supplies a root."""

from collections import Counter
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from eval.runner import core
from eval.runner.audit import PrivateGraders
from eval.runner.frozen_v3 import taskset_digest_v3


@pytest.fixture
def snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, dict[str, PrivateGraders]]:
    repository = tmp_path / 'repository'
    public = repository / 'eval/tasks-v3/v3-synthetic'
    public.mkdir(parents=True)
    (public / 'prompt.md').write_text('Synthetic public request')
    private = tmp_path / 'trusted'
    task = private / 'v3-synthetic'
    task.mkdir(parents=True)
    (task / 'test_synthetic.py').write_text('synthetic grader')
    (task / 'coverage.json').write_text('{}')
    reference = private / '.references/v3-synthetic'
    reference.mkdir(parents=True)
    (reference / 'application.json').write_text('{"files":{"answer.py":"answer.py"}}')
    (reference / 'answer.py').write_text('synthetic reference')
    responder = private / 'responder-data/v3-synthetic'
    responder.mkdir(parents=True)
    (responder / 'note.md').write_text('synthetic reply')
    (responder / 'matcher.json').write_text('{}')
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    monkeypatch.setattr(core, 'public_files', lambda *args: sorted(public.glob('*')))
    graders = {'v3-synthetic': PrivateGraders.load(private, 'v3-synthetic', repository)}
    return public, private, graders


@pytest.mark.parametrize('target', [
    'public/prompt.md', 'v3-synthetic/test_synthetic.py', 'v3-synthetic/coverage.json',
    '.references/v3-synthetic/application.json', '.references/v3-synthetic/answer.py',
    'responder-data/v3-synthetic/note.md', 'responder-data/v3-synthetic/matcher.json',
])
def test_every_frozen_input_changes_digest(snapshot: tuple[Path, Path, dict[str, PrivateGraders]], target: str) -> None:
    public, private, graders = snapshot
    before = taskset_digest_v3(graders)
    path = public / 'prompt.md' if target.startswith('public/') else private / target
    path.write_text(path.read_text() + '\nchanged')
    assert core.configured_digest(graders, {'task_root': 'eval/tasks-v3'}) != before


def test_private_names_are_bound_and_caches_ignored(snapshot: tuple[Path, Path, dict[str, PrivateGraders]]) -> None:
    _, private, graders = snapshot
    before = taskset_digest_v3(graders)
    cache = private / '__pycache__'
    cache.mkdir()
    (cache / 'compiled.pyc').write_bytes(b'cache')
    assert taskset_digest_v3(graders) == before
    (private / 'responder-data/v3-synthetic/note.md').rename(private / 'responder-data/v3-synthetic/renamed.md')
    assert taskset_digest_v3(graders) != before


def test_private_symlinks_fail_closed(snapshot: tuple[Path, Path, dict[str, PrivateGraders]]) -> None:
    _, private, graders = snapshot
    (private / 'alias').symlink_to(private / 'v3-synthetic/coverage.json')
    with pytest.raises(ValueError, match='symlinks'):
        taskset_digest_v3(graders)


def test_frozen_inventory_and_config_readiness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    a_path = core.REPOSITORY / 'eval/configs/full-v3-a.yaml'
    h3_path = core.REPOSITORY / 'eval/configs/full-v3-h3.yaml'
    a = json.loads(a_path.read_text())
    h3 = json.loads(h3_path.read_text())
    metadata = [json.loads(path.read_text()) for path in (core.REPOSITORY / 'eval/tasks-v3').glob('*/meta.json')]
    assert len(metadata) == 54 and all(meta['frozen'] is True for meta in metadata)
    assert sorted(meta['id'] for meta in metadata) == a['tasks'] == h3['tasks']
    assert sorted(Counter(meta['type'] for meta in metadata).values()) == [9] * 6
    assert sum(meta['two_session'] for meta in metadata) == 9
    assert a['task_set_sha256'] == h3['task_set_sha256']
    assert re.fullmatch(r'[0-9a-f]{64}', a['task_set_sha256'])
    assert core.load_config(h3_path) == h3
    assert h3['mode'] == 'plugin' and h3['template_status'] == 'draft_not_approved'
    assert core.require_call_estimate(h3)['paid_call_bound'] == 261
    loaded = core.load_config(a_path)
    assert loaded == a and loaded['harness'] is False
    assert core.require_call_estimate(loaded)['matched_estimate'] == 'eval/reports/full-v3-a-estimate.md'

    monkeypatch.setattr(core.PrivateGraders, 'load', lambda *args, **kwargs: object())
    monkeypatch.setattr(core, 'configured_digest', lambda *args: '0' * 64 if a['task_set_sha256'] != '0' * 64 else '1' * 64)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError('No executor calls allowed')

    with pytest.raises(ValueError, match='pinned frozen digest'):
        core.run(a_path, tmp_path / 'out', tmp_path / 'unused', execute=forbidden, version=a['codex_version'])
    assert not (tmp_path / 'out').exists()

    # Keep the real frozen metadata/public-input checks; mock only private data
    # and its digest. Stop at checkpoint creation, before any executor work.
    monkeypatch.setattr(core.PrivateGraders, 'load',
                        lambda *args, **kwargs: SimpleNamespace(markers=lambda: ()))
    monkeypatch.setattr(core, 'configured_digest', lambda *args: a['task_set_sha256'])

    def accepted() -> str:
        raise AssertionError('Digest accepted; public input checks completed')

    monkeypatch.setattr(core, 'now', accepted)
    with pytest.raises(AssertionError, match='Digest accepted; public input checks completed'):
        core.run(a_path, tmp_path / 'accepted', tmp_path / 'unused',
                 execute=forbidden, version=a['codex_version'])
    assert not (tmp_path / 'accepted/checkpoint.json').exists()


@pytest.mark.skipif(not os.environ.get('LHM_PRIVATE_V3'), reason='Host private snapshot not supplied')
def test_host_freeze_digest_matches_configs() -> None:
    from eval.freeze_v3 import freeze_summary

    summary = freeze_summary(Path(os.environ['LHM_PRIVATE_V3']))
    for arm in ('a', 'h3'):
        document = json.loads((core.REPOSITORY / f'eval/configs/full-v3-{arm}.yaml').read_text())
        config = document.get('run_config', document)
        assert config['task_set_sha256'] == summary['task_set_sha256']
