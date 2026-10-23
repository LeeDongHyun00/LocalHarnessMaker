"""Offline audit tests use synthetic copies, never live Codex/model calls."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
import sys
from typing import Any

import pytest

from plugin.demo import write_json, workspace_files
from plugin.two_session_demo import FOLLOWUP, audit, check_version


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / 'two-session'
    source = Path(__file__).resolve().parents[2] / 'plugin/evidence/2026-10-22-real'
    shutil.copytree(source, root / 'day1')
    first = json.loads((root / 'day1/experiment.json').read_text())
    first['release_label'] = 'release-a914e'
    write_json(root / 'day1/experiment.json', first)
    handoff_path = root / 'day1/approval-state/handoff.json'
    handoff = json.loads(handoff_path.read_text())
    handoff['decisions'].append({'what': first['release_label'], 'why': 'user selected next-day release label'})
    write_json(handoff_path, handoff)
    command = [sys.executable, '-m', 'verifier', 'validate-handoff', '--handoff', str(handoff_path)]
    write_json(root / 'handoff-validation.json', {'command': command, 'exit_code': 0, 'stdout': str(handoff_path) + '\n',
                                                   'sha256': hashlib.sha256(handoff_path.read_bytes()).hexdigest()})
    (root / 'day1-artifact').mkdir()
    shutil.copyfile(source / 'result.txt', root / 'day1-artifact/result.txt')
    second = root / 'day2'
    shutil.copytree(source, second)
    second_meta = {**first, 'thread_id': 'fresh-day2', 'prompt': FOLLOWUP}
    write_json(second / 'experiment.json', second_meta)
    shutil.copyfile(handoff_path, second / 'incoming-handoff.json')
    context = 'HARNESS_HANDOFF\n' + handoff_path.read_text()
    events = [json.loads(line) for line in (second / 'hooks.jsonl').read_text().splitlines()]
    for event in events:
        event['input']['session_id'] = second_meta['thread_id']
    events[0]['output'] = {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}}
    next(e for e in events if e['event'] == 'UserPromptSubmit')['input']['prompt'] = FOLLOWUP
    (second / 'hooks.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
    for stage in ('request', 'approval'):
        state = second / f'{stage}-state/session.json'
        session = json.loads(state.read_text())
        session['session_id'] = second_meta['thread_id']
        write_json(state, session)
        transcript = second / f'{stage}-transcript.jsonl'
        with transcript.open('a') as stream:
            stream.write(json.dumps({'type': 'response_item', 'payload': {'role': 'developer', 'content': [{'text': context}]}}) + '\n')
        result_path = second / f'{stage}-result.json'
        result = json.loads(result_path.read_text())
        if stage == 'approval':
            command = result['command']
            command[command.index('resume') + 1] = second_meta['thread_id']
        write_json(result_path, result)
    for name in ('initial-workspace.json', 'request-workspace.json', 'before-approval-workspace.json'):
        write_json(second / name, {'files': workspace_files(root / 'day1-artifact')})
    (second / 'followup.txt').write_text(first['release_label'] + '\n')
    return root


def test_two_session_audit_accepts_complete_evidence(tmp_path: Path) -> None:
    assert audit(fixture(tmp_path)) == {
        'saved_handoff_validated': True, 'session_start_injected': True, 'context_visible': True,
        'new_session': True, 'user_restatement_needed': False, 'approval_gates': True, 'overall': 'pass'}


@pytest.mark.parametrize('damage', ['validation', 'handoff', 'injection', 'visibility', 'restatement',
                                  'same_session', 'early_write', 'followup', 'verdict', 'resume', 'error'])
def test_two_session_audit_rejects_missing_or_conflicting_evidence(tmp_path: Path, damage: str) -> None:
    root = fixture(tmp_path)
    day2 = root / 'day2'
    if damage == 'validation':
        path = root / 'handoff-validation.json'
        data = json.loads(path.read_text()); data['exit_code'] = 1; write_json(path, data)
    elif damage == 'handoff':
        (day2 / 'incoming-handoff.json').write_text('{}')
    elif damage in {'injection', 'restatement', 'error'}:
        events = [json.loads(line) for line in (day2 / 'hooks.jsonl').read_text().splitlines()]
        if damage == 'injection':
            events[0]['output']['hookSpecificOutput']['additionalContext'] = 'wrong'
        elif damage == 'error':
            events[0]['error'] = 'ValueError'
        else:
            next(e for e in events if e['event'] == 'UserPromptSubmit')['input']['prompt'] += ' release-a914e'
        (day2 / 'hooks.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
    elif damage == 'visibility':
        (day2 / 'request-transcript.jsonl').write_text('')
    elif damage == 'same_session':
        path = day2 / 'experiment.json'
        data = json.loads(path.read_text())
        data['thread_id'] = json.loads((root / 'day1/experiment.json').read_text())['thread_id']
        write_json(path, data)
    elif damage == 'early_write':
        write_json(day2 / 'before-approval-workspace.json', {'files': {}})
    elif damage == 'followup':
        (day2 / 'followup.txt').write_text('unknown\n')
    elif damage == 'verdict':
        path = day2 / 'approval-state/verdict.json'
        data = json.loads(path.read_text()); data['overall'] = 'fail'; data['items'][0]['status'] = 'fail'; write_json(path, data)
    else:
        path = day2 / 'request-result.json'
        data = json.loads(path.read_text()); data['command'].insert(4, 'resume'); write_json(path, data)
    with pytest.raises((ValueError, KeyError)):
        audit(root)


def test_version_check_is_mockable_and_nested(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    from plugin import demo
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        assert kwargs['shell'] is False
        return subprocess.CompletedProcess(command, 0, 'codex-cli changed\n', '')
    monkeypatch.setattr(demo, 'run_group', run)
    with pytest.raises(ValueError, match='version changed'):
        check_version({'codex': 'fake-codex', 'version': 'codex-cli original'})


def test_day_two_launches_fresh_thread_then_approves_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from plugin import demo, two_session_demo
    root, workspace = tmp_path / 'capture', tmp_path / 'workspace'
    first_out = root / 'day1/approval-state'
    first_out.mkdir(parents=True)
    (workspace / '.harness').mkdir(parents=True)
    (workspace / '.harness/handoff.json').write_text('{}')
    (first_out / 'handoff.json').write_text('{}')
    (workspace / 'result.txt').write_bytes(b'ok\n')
    write_json(root / 'day1/experiment.json', {'out': str(root / 'day1'), 'workspace': str(workspace),
               'codex_home': str(tmp_path / 'isolated-codex'), 'thread_id': 'day-one-thread',
               'release_label': 'release-test', 'version': 'codex-cli test', 'mode': 'real', 'max_attempts': 3})
    monkeypatch.setattr(two_session_demo, 'audit_day_one', lambda path: {})
    monkeypatch.setattr(two_session_demo, 'check_version', lambda metadata: None)
    calls: list[tuple[str, str | None, str]] = []
    def launch(metadata: dict[str, Any], stage: str) -> None:
        assert 'release_label' not in metadata
        calls.append((stage, metadata.get('thread_id'), metadata['prompt']))
        metadata['thread_id'] = 'day-two-thread'
        (Path(metadata['out']) / f'{stage}-reply.txt').write_text('contract summary')
        if stage == 'approval':
            (workspace / 'followup.txt').write_text('release-test\n')
    def capture(metadata: dict[str, Any], stage: str) -> None:
        out = Path(metadata['out'])
        demo.write_json(out / f'{stage}-workspace.json', {'files': demo.workspace_files(workspace)})
        if stage == 'request':
            (out / 'request-state').mkdir()
            write_json(out / 'request-state/session.json', {'phase': 'awaiting_approval'})
    monkeypatch.setattr(demo, 'launch', launch)
    monkeypatch.setattr(two_session_demo, 'capture', capture)
    monkeypatch.setattr(two_session_demo, 'audit', lambda path: {'synthetic_test_only': True})
    two_session_demo.day_two(root, scripted=True)
    assert calls == [('request', None, FOLLOWUP), ('approval', 'day-two-thread', FOLLOWUP)]
    assert (root / 'day2/incoming-handoff.json').read_bytes() == b'{}'
