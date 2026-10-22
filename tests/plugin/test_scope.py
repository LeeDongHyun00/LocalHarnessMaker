"""Project opt-in is silent and precedes runtime imports, logs and state writes."""
from __future__ import annotations
import builtins
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import pytest
from plugin.hooks._scope import marked_project

HOOKS = Path(__file__).resolve().parents[2] / 'plugin/hooks'


@pytest.mark.parametrize('script', ['session_start.py', 'user_prompt_submit.py', 'stop.py', 'probe.py'])
def test_unmarked_hook_is_silent_before_runtime_import(script: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(HOOKS))
    monkeypatch.delenv('HARNESS_NESTED', raising=False)
    monkeypatch.setenv('HARNESS_EVENT_LOG', str(tmp_path / 'must-not-exist'))
    monkeypatch.setenv('HARNESS_PROBE_DIR', str(tmp_path / 'must-not-exist'))
    payload = {'cwd': str(tmp_path), 'prompt': 'costly request', 'session_id': 'test',
               'hook_event_name': {'session_start.py': 'SessionStart', 'user_prompt_submit.py': 'UserPromptSubmit',
                                   'stop.py': 'Stop', 'probe.py': 'Stop'}[script]}
    importing = builtins.__import__
    def guarded(name: str, *args: object, **kwargs: object) -> object:
        assert name != '_runtime', 'unmarked hook imported runtime'
        return importing(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(payload)))
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), pytest.raises(SystemExit) as result:
        runpy.run_path(str(HOOKS / script), run_name='__main__')
    assert result.value.code == 0
    assert stdout.getvalue() == stderr.getvalue() == ''
    assert list(tmp_path.iterdir()) == []


def test_scope_uses_marked_canonical_ancestors(tmp_path: Path) -> None:
    project, outside = tmp_path / 'project', tmp_path / 'sibling'
    child = project / 'subdirectory'
    child.mkdir(parents=True)
    outside.mkdir()
    (project / '.local-harness-maker').touch()
    (project / 'escape').symlink_to(outside, target_is_directory=True)
    assert marked_project({'cwd': str(project)})
    assert marked_project({'cwd': str(child)})
    assert not marked_project({'cwd': str(outside)})
    assert not marked_project({'cwd': str(project / 'escape')})
