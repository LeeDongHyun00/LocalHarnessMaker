"""Synthetic evidence and injected process tests; no live Codex/model calls."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import shutil
import sys
from typing import Any

import pytest

from plugin import demo
from plugin.handoff_failure_demo import EXHAUST, NEXT, SEED, audit, shim
from plugin.export_demo_evidence import export


def write_events(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def fixture(tmp_path: Path, scenario: str) -> Path:
    root = tmp_path / 'capture'
    shutil.copytree(demo.PLUGIN / 'evidence/2026-10-23-two-session', root)
    (root / 'handoff-validation.json').rename(tmp_path / 'unused-pass-validation.json')
    for day in ('day1', 'day2'):
        folder = root / day
        meta = json.loads((folder / 'experiment.json').read_text())
        meta.update(scenario=scenario, max_attempts=1)
        meta['prompt'] = (EXHAUST if scenario == 'exhaustion' else demo.REAL_PROMPT) if day == 'day1' else NEXT
        demo.write_json(folder / 'experiment.json', meta)
        events = [json.loads(line) for line in (folder / 'hooks.jsonl').read_text().splitlines()]
        if day == 'day2':
            events = events[:2]
        next(e for e in events if e['event'] == 'UserPromptSubmit')['input']['prompt'] = meta['prompt']
        contract = json.loads((folder / 'request-state/contract.json').read_text())
        if scenario == 'exhaustion' and day == 'day1':
            contract['success_criteria'] = [{'id': 'SC-X', 'description': 'Deliberately impossible', 'check': {
                'type': 'command', 'command': "python -c 'raise SystemExit(1)'", 'expected': {'exit_code': 0}}}]
            for stage in ('request', 'approval'):
                demo.write_json(folder / f'{stage}-state/contract.json', contract)
        contract_text = (folder / 'request-state/contract.json').read_text()
        context = 'HARNESS_CONTRACT\n' + contract_text
        next(e for e in events if e['event'] == 'UserPromptSubmit')['output']['hookSpecificOutput']['additionalContext'] = context
        write_events(folder / 'request-transcript.jsonl', [{'type': 'response_item', 'payload': {
            'role': 'developer', 'content': [{'text': context}]}}])
        for name in ('initial-workspace.json', 'request-workspace.json', 'before-approval-workspace.json'):
            demo.write_json(folder / name, {'files': {}})
        if day == 'day1':
            saved = folder / 'approval-state'
            session = json.loads((saved / 'session.json').read_text())
            session['phase'] = 'exhausted' if scenario == 'exhaustion' else 'complete'
            demo.write_json(saved / 'session.json', session)
            if scenario == 'exhaustion':
                demo.write_json(saved / 'verdict.json', {'items': [{'id': 'SC-X', 'status': 'fail', 'evidence': 'exit 1', 'reason': 'expected 0'}],
                    'overall': 'fail', 'reinstruct_message': None, 'attempt': 1})
                demo.write_json(saved / 'handoff.json', {**SEED, 'remaining': [{'criterion_id': 'SC-X', 'state': 'Command still fails'}]})
                events[-1]['output'] = {'systemMessage': 'Harness ended after attempt 1; unmet items: SC-X (fail)'}
            else:
                # Rename the fixture current, then replace archive bytes with the known seed.
                (saved / 'handoff.json').rename(saved / 'handoff.stale.fixture.json')
                demo.write_json(saved / 'handoff.stale.fixture.json', SEED)
                demo.write_json(root / 'previous-handoff.json', SEED)
                demo.write_json(root / 'day2/request-state/handoff.stale.fixture.json', SEED)
                (root / 'day2/request-state/handoff.json').rename(root / 'unused-fixture-handoff.json')
                events[-1]['error'] = 'RuntimeError'
                events[-1]['output'] = None
                args = ['-m', 'controller', 'handoff'] if scenario == 'generation' else ['-m', 'verifier', 'validate-handoff']
                write_events(root / 'faults.jsonl', [{'mode': scenario, 'args': args + ['--out', 'handoff.pending.fixture.json'], 'exit_code': 2}])
                if scenario == 'validation':
                    demo.write_json(saved / 'handoff.pending.fixture.json', SEED)
        else:
            if scenario == 'exhaustion':
                context = 'HARNESS_HANDOFF\n' + (root / 'day1/approval-state/handoff.json').read_text()
                events[0]['output'] = {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}}
                with (folder / 'request-transcript.jsonl').open('a') as stream:
                    stream.write(json.dumps({'type': 'response_item', 'payload': {'role': 'developer', 'content': [{'text': context}]}}) + '\n')
            else:
                events[0]['output'] = None
        write_events(folder / 'hooks.jsonl', events)
    return root


@pytest.mark.parametrize('scenario', ['exhaustion', 'generation', 'validation'])
def test_offline_checks(tmp_path: Path, scenario: str) -> None:
    root = fixture(tmp_path, scenario)
    assert audit(root)['overall'] == 'pass'
    portable = tmp_path / 'portable'
    export(root, portable)
    assert audit(portable)['overall'] == 'pass'
    assert str(demo.ROOT) not in ''.join(p.read_text() for p in portable.rglob('*') if p.is_file())


@pytest.mark.parametrize('scenario,damage', [
    ('exhaustion', 'remaining'), ('exhaustion', 'context'), ('exhaustion', 'attempt'),
    ('generation', 'current'), ('validation', 'archive'), ('validation', 'fault'),
    ('generation', 'stale_context'), ('exhaustion', 'early_write'), ('validation', 'same_session')])
def test_rejects_bad_evidence(tmp_path: Path, scenario: str, damage: str) -> None:
    root = fixture(tmp_path, scenario)
    if damage == 'remaining':
        demo.write_json(root / 'day1/approval-state/handoff.json', SEED)
    elif damage == 'context':
        (root / 'day2/request-transcript.jsonl').write_text('')
    elif damage == 'attempt':
        path = root / 'day1/approval-state/state.json'
        data = json.loads(path.read_text()); data['attempt'] = 2; demo.write_json(path, data)
    elif damage == 'current':
        demo.write_json(root / 'day2/request-state/handoff.json', SEED)
    elif damage == 'archive':
        demo.write_json(root / 'day1/approval-state/handoff.stale.fixture.json', {})
    elif damage == 'fault':
        (root / 'faults.jsonl').write_text('')
    elif damage == 'stale_context':
        with (root / 'day2/request-transcript.jsonl').open('a') as stream:
            stream.write(json.dumps({'type': 'response_item', 'payload': {'role': 'developer', 'content': [{'text': 'HARNESS_HANDOFF stale'}]}}) + '\n')
    elif damage == 'early_write':
        demo.write_json(root / 'day1/before-approval-workspace.json', {'files': {'unexpected': {}}})
    else:
        path = root / 'day2/experiment.json'
        data = json.loads(path.read_text()); data['thread_id'] = json.loads((root / 'day1/experiment.json').read_text())['thread_id']; demo.write_json(path, data)
    with pytest.raises(ValueError):
        audit(root)


@pytest.mark.parametrize('mode,args,blocked', [
    ('generation', ['-m', 'controller', 'handoff'], True),
    ('validation', ['-m', 'verifier', 'validate-handoff', '--handoff', 'handoff.pending.x.json'], True),
    ('validation', ['-c', 'print("delegated")'], False),
    ('generation', ['-c', 'print("delegated")'], False)])
def test_fault_wrapper(tmp_path: Path, mode: str, args: list[str], blocked: bool) -> None:
    import os
    wrapper = tmp_path / 'python'
    shim(wrapper)
    result = subprocess.run([sys.executable, str(wrapper), *args], capture_output=True, text=True,
        env={**os.environ, 'HANDOFF_DEMO_FAULT': mode, 'HANDOFF_DEMO_FAULT_LOG': str(tmp_path / 'fault.jsonl')}, timeout=5)
    assert result.returncode == (2 if blocked else 0)
    assert (tmp_path / 'fault.jsonl').exists() == blocked


def test_portable_pass_demo_remains_auditable(tmp_path: Path) -> None:
    from plugin.two_session_demo import audit as pass_audit
    raw = tmp_path / 'raw'
    shutil.copytree(demo.PLUGIN / 'evidence/2026-10-23-two-session', raw)
    original = (raw / 'day1/approval-state/handoff.json').read_bytes()
    export(raw, tmp_path / 'portable')
    assert pass_audit(tmp_path / 'portable')['overall'] == 'pass'
    assert (raw / 'day1/approval-state/handoff.json').read_bytes() == original
    with pytest.raises(ValueError):
        export(raw, tmp_path / 'portable')


def test_expected_stop_failure_capture(tmp_path: Path) -> None:
    from plugin.two_session_demo import capture
    workspace, out = tmp_path / 'workspace', tmp_path / 'evidence'
    (workspace / '.harness').mkdir(parents=True)
    out.mkdir()
    transcript = tmp_path / 'transcript.jsonl'
    transcript.write_text('{}\n')
    write_events(out / 'hooks.jsonl', [{'event': 'Stop', 'error': 'RuntimeError',
        'input': {'transcript_path': str(transcript)}}])
    meta = {'out': str(out), 'workspace': str(workspace)}
    with pytest.raises(ValueError):
        capture(meta, 'approval')
    capture(meta, 'approval', allow_stop_error=True)
    assert (out / 'approval-transcript.jsonl').read_text() == '{}\n'


def test_fault_environment_reaches_child_only(tmp_path: Path) -> None:
    import os
    meta = {'out': str(tmp_path), 'workspace': str(tmp_path), 'codex_home': str(tmp_path / 'isolated'),
            'mode': 'real', 'prompt': 'demo'}
    parent = os.environ.copy()
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        env = kwargs['env']
        assert env['HARNESS_PYTHON'] == '/demo/fault-wrapper'
        assert env['HARNESS_MAX_ATTEMPTS'] == '1'
        assert env['HARNESS_BACKEND'] == 'codex_cli'
        assert 'HARNESS_STUB' not in env and 'HARNESS_NESTED' not in env
        return subprocess.CompletedProcess(command, 0, '{"type":"thread.started","thread_id":"demo-thread"}\n', '')
    demo.launch(meta, 'request', run=run, extra_env={'HARNESS_PYTHON': '/demo/fault-wrapper', 'HARNESS_MAX_ATTEMPTS': '1'})
    assert os.environ == parent
