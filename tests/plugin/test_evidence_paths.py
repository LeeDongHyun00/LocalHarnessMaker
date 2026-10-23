"""Recorded evidence must have the same meaning on every checking host."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from plugin import demo
from plugin.check_demo_evidence import audit as single_audit
from plugin.evidence_paths import recorded_path
from plugin.export_demo_evidence import export
from plugin.handoff_failure_demo import audit as failure_audit
from plugin.two_session_demo import audit as two_audit
from tests.plugin.test_handoff_failure_demo import fixture as failure_fixture


@pytest.mark.parametrize('value,expected', [
    ('/private/var/a/./b/../c/', '/var/a/c'),
    ('/private/tmp/work', '/tmp/work'), ('/private/etc/config', '/etc/config'),
    ('/private/variable/work', '/private/variable/work'),
    ('/other/private/var/work', '/other/private/var/work'),
    ('${WORKSPACE}', '${WORKSPACE}'),
    ('${WORKSPACE}/a/../b', '${WORKSPACE}/a/../b'),
    ('/tmp/${WORKSPACE}/../b', '/tmp/${WORKSPACE}/../b'),
])
def test_recorded_path_never_resolves(
    value: str, expected: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> Path:
        raise AssertionError('recorded paths must not use filesystem resolution')
    monkeypatch.setattr(Path, 'resolve', forbidden)
    assert recorded_path(value) == expected


@pytest.mark.parametrize('kind', ['single', 'two', 'exhaustion', 'generation', 'validation'])
def test_checkers_and_export_without_host_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    # Linux does not have the macOS /var -> /private/var symlink. Force that
    # behavior on macOS too, including while exporting committed evidence.
    monkeypatch.setattr(Path, 'resolve', lambda self, *args, **kwargs: self)
    if kind in {'single', 'two'}:
        source = demo.PLUGIN / 'evidence' / (
            '2026-10-22-real' if kind == 'single' else '2026-10-23-two-session')
        root = tmp_path / 'raw'
        shutil.copytree(source, root)
        audit = single_audit if kind == 'single' else two_audit
    else:
        root = failure_fixture(tmp_path, kind)
        audit = failure_audit
    assert audit(root)['overall'] == 'pass'
    portable = tmp_path / 'portable'
    export(root, portable)
    assert audit(portable)['overall'] == 'pass'
    days = [portable] if kind == 'single' else [portable / 'day1', portable / 'day2']
    for day in days:
        assert json.loads((day / 'experiment.json').read_text())['workspace'] == '${WORKSPACE}'
        events = [json.loads(line) for line in (day / 'hooks.jsonl').read_text().splitlines()]
        assert all(e['input']['cwd'] == '${WORKSPACE}' for e in events)


@pytest.mark.parametrize('kind', ['single', 'two', 'exhaustion', 'generation', 'validation'])
@pytest.mark.parametrize('damage', ['different', 'mac_alias_elsewhere', 'symlink_elsewhere', 'placeholder'])
def test_checkers_reject_unrelated_recorded_workspaces(
    tmp_path: Path, kind: str, damage: str,
) -> None:
    if kind in {'single', 'two'}:
        root = tmp_path / 'raw'
        shutil.copytree(demo.PLUGIN / 'evidence' / (
            '2026-10-22-real' if kind == 'single' else '2026-10-23-two-session'), root)
        audit = single_audit if kind == 'single' else two_audit
    else:
        root = failure_fixture(tmp_path, kind)
        audit = failure_audit
    folder = root if kind == 'single' else root / 'day2'
    meta = json.loads((folder / 'experiment.json').read_text())
    workspace = recorded_path(meta['workspace'])
    if damage == 'different':
        unrelated = workspace + '-different'
    elif damage == 'mac_alias_elsewhere':
        unrelated = '/private' + workspace + '-different'
    elif damage == 'symlink_elsewhere':
        alias = tmp_path / 'alias'
        alias.symlink_to(workspace + '-different', target_is_directory=True)
        unrelated = str(alias)
    else:
        unrelated = '${WORKSPACE}/../other'
    path = folder / 'hooks.jsonl'
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[0]['input']['cwd'] = unrelated
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))
    with pytest.raises(ValueError, match='unrelated'):
        audit(root)
