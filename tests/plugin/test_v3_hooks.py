"""V3 native-session lifecycle with mocked CLI producers, never live Codex."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from plugin.artifacts import (ROOT, confined, digest, read, session_directory, snapshot,
                              validate, workspace_hash, write)
from plugin.hooks._v3_runtime import Runtime
from plugin.v3_adapter import Adapter


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setenv('HARNESS_INTERFACE_VERSION', '3')
    monkeypatch.delenv('HARNESS_STUB', raising=False)
    monkeypatch.delenv('HARNESS_NESTED', raising=False)
    monkeypatch.setenv('HARNESS_CODEX', '/mock/codex')
    monkeypatch.setattr('plugin.install.resolve_codex', lambda: '/mock/codex')
    project = tmp_path / 'project'
    project.mkdir()
    (project / '.local-harness-maker').touch()
    transcript = tmp_path / 'transcript.jsonl'
    transcript.write_text('')
    control: dict[str, Any] = {'failed': [], 'questions': False, 'pin': True, 'calls': [],
                               'ledger_valid': True, 'controller_error': False}

    def append_call(directory: Path, session_id: str, phase: str) -> None:
        row = read(ROOT / 'schemas/examples/luna-call.json')
        row.update(session_id=session_id, phase=phase, call_id=phase + '-1',
                   pricing_ref=read(directory / 'pin-check.json')['pricing_ref'])
        if control.get('mismatch'):
            row['model'] = 'gpt-6-luna-newer'
            row['status'] = 'pin_mismatch'
            row['error'] = 'wrong model'
        # Only the mock controller owns accounting, mirroring production ownership.
        with confined(directory, 'luna-calls.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')

    def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['shell'] is False and kwargs['env']['HARNESS_NESTED'] == '1'
        if command[0] == '/mock/codex':
            if command[1] == '--version':
                return subprocess.CompletedProcess(command, 0, 'codex-cli 0.163.0-alpha.11.1\n', '')
            if command[1] == '--help':
                return subprocess.CompletedProcess(command, 0, 'Commands:\n  models List models\n', '')
            models = ['gpt-6-luna'] if control['pin'] else ['gpt-6-luna-next']
            return subprocess.CompletedProcess(command, 0, json.dumps(models), '')
        module, operation = command[2:4]
        control['calls'].append((module, operation, command))
        def arg(name: str) -> str:
            return command[command.index(name) + 1]
        directory, session_id = Path(arg('--artifacts')), arg('--session-id')
        if operation == 'requirements':
            append_call(directory, session_id, 'requirements')
            if control['controller_error']:
                return subprocess.CompletedProcess(command, 2, '', 'failed')
            prompt_path = Path(arg('--prompt'))
            requirement = {'id': 'R-1', 'number': 1, 'text': 'Create result.txt.',
                           'kind': 'named_file', 'source_excerpt': 'Create result.txt.',
                           'check': {'type': 'file_exists', 'path': 'result.txt'}}
            questions = ([{'id': 'Q-1', 'text': 'Which release?', 'requirement_ids': ['R-1'], 'answer': None}]
                         if control['questions'] else [])
            write(directory / 'requirements.json', {'schema_version': 3, 'session_id': session_id,
                'prompt': {'path': str(prompt_path.relative_to(directory)), 'sha256': digest(prompt_path.read_bytes())},
                'state': 'pending_questions' if questions else 'ready', 'requirements': [requirement],
                'open_questions': questions, 'luna_call': {'path': 'luna-calls.jsonl', 'call_id': 'requirements-1'}})
            output = str(directory / 'requirements.json') + '\n'
        elif operation == 'check':
            round_number = int(arg('--round'))
            evidence = snapshot(directory, f'check-{round_number}.txt', b'Completed check output\n')
            evidence.update(kind='check_output', excerpt='Completed check output')
            final_path = Path(arg('--final-message')) if '--final-message' in command else None
            final = ({'path': str(final_path.relative_to(directory)), 'sha256': digest(final_path.read_bytes())}
                     if final_path else None)
            failed = control['failed']
            status = 'fail' if failed else 'unverifiable' if control.get('unverifiable') else 'pass'
            req_path = Path(arg('--requirements'))
            report = {'schema_version': 3, 'session_id': session_id,
                      'requirements': {'path': 'requirements.json', 'sha256': digest(req_path.read_bytes())},
                      'current_final_message': final, 'check_round': round_number,
                      'items': [{'requirement_id': 'R-1', 'status': status,
                                 'reason': 'Mock executed check', 'evidence': [evidence] if status != 'unverifiable' else []}],
                      'claim_audit': {'status': 'unavailable', 'audited_final_message': None,
                                      'claims': [], 'reason': 'Not yet audited', 'luna_call': None},
                      'retry': {'used': int(round_number == 2), 'failed_requirement_ids': ['R-1'] if round_number == 2 else [],
                                'reason': 'Single repair' if round_number == 2 else None},
                      'escalation_advice': {'recommendation': 'human_review', 'text': 'Still failed'} if round_number == 2 and failed else None}
            write(directory / 'completion-report.json', report)
            output = json.dumps({'overall': status, 'failed_rows': failed,
                                 'unverifiable_rows': ['R-1'] if status == 'unverifiable' else [],
                                 'retry_warranted': bool(failed)}) + '\n'
        elif operation == 'claim-audit':
            append_call(directory, session_id, 'claim_audit')
            final = Path(arg('--final-message'))
            audit = {'status': 'complete', 'audited_final_message': {
                'path': str(final.relative_to(directory)), 'sha256': digest(final.read_bytes())},
                'claims': [], 'reason': None, 'luna_call': {'path': 'luna-calls.jsonl', 'call_id': 'claim_audit-1'}}
            write(directory / 'claim-audit.json', audit)
            output = str(directory / 'claim-audit.json') + '\n'
        elif operation == 'ledger-validate':
            ledger_path = Path(arg('--ledger'))
            if not control['ledger_valid'] or not ledger_path.exists():
                return subprocess.CompletedProcess(command, 1, '', '')
            value = read(ledger_path)
            value['validation'] = {'validated_at': datetime.now(timezone.utc).isoformat(), 'status': 'valid',
                'reason': 'Mock mechanical validation', 'identifiers': [], 'files': []}
            write(ledger_path, value)
            output = str(ledger_path) + '\n'
        else:
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0, output, '')

    adapter = Adapter(runner=runner)
    monkeypatch.setattr(adapter, 'ledger_text', lambda directory, session_id: 'MOCK VERIFIER: write ledger; preserve application summary; no application edits.')
    def final(text: str) -> None:
        with transcript.open('a') as stream:
            stream.write(json.dumps({'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant',
                'phase': 'final_answer', 'content': [{'type': 'output_text', 'text': text}]}}) + '\n')
    def drive(event: str, session_id: str = 'native-1', **kwargs: Any) -> Any:
        payload = {'session_id': session_id, 'hook_event_name': event, 'cwd': str(project),
                   'transcript_path': str(transcript), **kwargs}
        return Runtime(payload, adapter=adapter).dispatch(event)
    def ledger(session_id: str = 'native-1') -> Path:
        directory = session_directory(project, session_id)
        path = directory / 'ledger.json'
        write(path, {'schema_version': 3, 'session_id': session_id,
            'requirements': {'path': 'requirements.json', 'sha256': digest((directory / 'requirements.json').read_bytes())},
            'decisions': [], 'open_items': [], 'validation': None})
        return path
    return {'drive': drive, 'final': final, 'ledger': ledger, 'control': control, 'adapter': adapter,
            'root': project, 'directory': session_directory(project, 'native-1'), 'runner': runner}


def start(h: dict[str, Any]) -> None:
    assert 'gpt-6-luna' in h['drive']('SessionStart')['hookSpecificOutput']['additionalContext']
    context = h['drive']('UserPromptSubmit', prompt='Create result.txt.')
    assert 'HARNESS_REQUIREMENTS' in context['hookSpecificOutput']['additionalContext']


def test_success_ledger_next_session_and_duplicate_stops(harness: dict[str, Any]) -> None:
    h = harness
    start(h)
    h['final']('R-1 completed with evidence')
    assert 'MOCK VERIFIER' in h['drive']('Stop')['reason']
    count = len(h['control']['calls'])
    assert h['drive']('Stop') is None
    assert len(h['control']['calls']) == count
    h['ledger']()
    h['final']('R-1 completed; ledger saved')
    assert h['drive']('Stop') is None
    assert h['drive']('Stop') is None
    report = read(h['directory'] / 'completion-report.json')
    assert report['claim_audit']['status'] == 'stale'
    assert (h['directory'].parents[1] / 'latest-ledger.json').exists()
    injected = h['drive']('SessionStart', session_id='native-2')['hookSpecificOutput']['additionalContext']
    assert 'HARNESS_LEDGER' in injected and 'native-1' in injected
    assert h['drive']('SessionStart', session_id='native-2') is None
    assert [r[1] for r in h['control']['calls']].count('claim-audit') == 1


def test_retry_once_and_escalation(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['failed'] = ['R-1']
    start(h)
    h['final']('R-1 completed')
    repair = h['drive']('Stop')
    assert repair['decision'] == 'block' and 'fix only' in repair['reason']
    assert h['drive']('Stop') is None
    h['final']('R-1 repaired but still failing')
    assert 'MOCK VERIFIER' in h['drive']('Stop')['reason']
    report = read(h['directory'] / 'completion-report.json')
    assert report['check_round'] == 2 and report['retry']['used'] == 1
    assert report['escalation_advice']['recommendation'] == 'human_review'
    h['ledger']()
    h['final']('R-1 failed; ledger saved')
    assert h['drive']('Stop') is None
    assert [r[1] for r in h['control']['calls']].count('check') == 2
    assert [r[1] for r in h['control']['calls']].count('claim-audit') == 1


def test_question_pause_and_explicit_answer_no_second_luna(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['questions'] = True
    start(h)
    h['final']('Which release?')
    assert h['drive']('Stop') is None
    assert [c[1] for c in h['control']['calls']] == ['requirements']
    context = h['drive']('UserPromptSubmit', prompt='sure')
    assert 'END THIS TURN' in context['hookSpecificOutput']['additionalContext']
    assert read(h['directory'] / 'requirements.json')['state'] == 'pending_questions'
    h['drive']('UserPromptSubmit', prompt='{"answers":{"Q-1":"stable"}}')
    assert read(h['directory'] / 'requirements.json')['state'] == 'ready'
    h['final']('R-1 created stable')
    assert h['drive']('Stop')['decision'] == 'block'
    assert [c[1] for c in h['control']['calls']].count('requirements') == 1


def test_questions_with_edits_do_not_bypass_verification(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['questions'] = True
    start(h)
    (h['root'] / 'unexpected.txt').write_text('edit')
    h['final']('Edited anyway')
    h['drive']('Stop')
    assert 'check' in [c[1] for c in h['control']['calls']]


def test_pin_disabled_skips_all_luna_retains_deterministic_ledger(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['pin'] = False
    h['drive']('SessionStart')
    context = h['drive']('UserPromptSubmit', prompt='Create result.txt.')
    assert 'not H3' in context['hookSpecificOutput']['additionalContext']
    assert not h['control']['calls']
    # A pre-existing safe requirements table may still be checked without Luna.
    assert read(h['directory'] / 'requirements.json')['state'] == 'unavailable'


@pytest.mark.parametrize('option', ['controller_error', 'mismatch'])
def test_failed_requirements_never_regenerated(harness: dict[str, Any], option: str) -> None:
    h = harness
    h['control'][option] = True
    h['drive']('SessionStart')
    h['drive']('UserPromptSubmit', prompt='Create result.txt.')
    h['drive']('UserPromptSubmit', prompt='Try again')
    assert [c[1] for c in h['control']['calls']] == ['requirements']
    if option == 'mismatch':
        assert read(h['directory'] / 'pin-check.json')['status'] == 'disabled'


def test_unverifiable_does_not_repair(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['unverifiable'] = True
    start(h)
    h['final']('Unknown')
    assert 'MOCK VERIFIER' in h['drive']('Stop')['reason']
    assert not read(h['directory'] / 'hook-state.json').get('repair_used')


def test_nullable_transcript_skips_audit(harness: dict[str, Any]) -> None:
    start(harness)
    assert harness['drive']('Stop', transcript_path=None)['decision'] == 'block'
    assert 'claim-audit' not in [c[1] for c in harness['control']['calls']]


@pytest.mark.parametrize('invalid', ['missing', 'invalid', 'latest_conflict', 'newer_missing', 'tie'])
def test_ledger_rejection_no_older_fallback(harness: dict[str, Any], invalid: str) -> None:
    h = harness
    start(h)
    h['final']('R-1 complete')
    h['drive']('Stop')
    h['ledger']()
    h['final']('R-1 complete; ledger saved')
    h['drive']('Stop')
    root = h['directory'].parents[1]
    if invalid == 'missing':
        (root / 'latest-ledger.json').rename(root / 'latest-held.json')
    elif invalid == 'invalid':
        h['control']['ledger_valid'] = False
    elif invalid == 'latest_conflict':
        value = read(root / 'latest-ledger.json')
        value['session_id'] = 'other'
        write(root / 'latest-ledger.json', value)
    else:
        other = session_directory(h['root'], 'intervening')
        value = read(h['directory'] / 'pin-check.json')
        value['session_id'] = 'intervening'
        if invalid == 'newer_missing':
            value['checked_at'] = '2099-01-01T00:00:00Z'
        write(other / 'pin-check.json', value)
    response = h['drive']('SessionStart', session_id='native-2')
    assert 'Prior ledger not injected' in response['hookSpecificOutput']['additionalContext']
    assert 'HARNESS_LEDGER' not in response['hookSpecificOutput']['additionalContext']


@pytest.mark.parametrize('relative', ['/tmp/escape', '../escape', 'evidence/../../escape'])
def test_path_confinement(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError):
        confined(tmp_path, relative)


def test_symlink_confinement_and_session_id_hash(tmp_path: Path) -> None:
    outside = tmp_path / 'outside'
    outside.mkdir()
    (tmp_path / '.localharness').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        session_directory(tmp_path, '../../hostile')
    clean = tmp_path / 'clean'
    clean.mkdir()
    directory = session_directory(clean, '../../hostile')
    assert directory.name == digest(b'../../hostile')
    assert directory.is_relative_to(clean)


def test_lock_prevents_concurrent_phase_allocation(harness: dict[str, Any]) -> None:
    from plugin.artifacts import locked
    with locked(harness['directory']):
        with pytest.raises(BlockingIOError):
            harness['drive']('SessionStart')
    assert not harness['control']['calls']


def test_default_entrypoint_is_v3(harness: dict[str, Any], monkeypatch: pytest.MonkeyPatch, capsys: Any) -> None:
    from plugin.hooks import _entrypoint, _v3_runtime
    monkeypatch.delenv('HARNESS_INTERFACE_VERSION')
    monkeypatch.setattr(_v3_runtime, 'Adapter', lambda **kwargs: harness['adapter'])
    import time
    payload = {'session_id': 'native-1', 'cwd': str(harness['root']), 'hook_event_name': 'SessionStart'}
    assert _entrypoint.execute('SessionStart', time.perf_counter(), payload) == 0
    assert 'gpt-6-luna' in capsys.readouterr().out


def test_duplicate_hook_log_records_do_not_consume_repair(harness: dict[str, Any]) -> None:
    h = harness
    h['control']['failed'] = ['R-1']
    start(h)
    h['final']('R-1 complete')
    h['drive']('Stop')
    transcript = Path(h['directory'].parents[3]).parent / 'transcript.jsonl'
    with transcript.open('a') as stream:
        stream.write('{"type":"event_msg","payload":{"type":"hook_response"}}\n')
    assert h['drive']('Stop') is None
    assert [r[1] for r in h['control']['calls']].count('check') == 1
    h['final']('R-1 complete')
    assert 'MOCK VERIFIER' in h['drive']('Stop')['reason']


@pytest.mark.parametrize('event', ['SessionStart', 'UserPromptSubmit', 'Stop'])
def test_v3_entrypoint_stdin_stdout(harness: dict[str, Any], event: str,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    import contextlib
    import io
    import runpy
    import sys
    from plugin.hooks import _v3_runtime
    h = harness
    monkeypatch.delenv('HARNESS_INTERFACE_VERSION')
    monkeypatch.setattr(_v3_runtime, 'Adapter', lambda **kwargs: h['adapter'])
    monkeypatch.syspath_prepend(str(ROOT / 'plugin/hooks'))
    if event == 'UserPromptSubmit':
        h['drive']('SessionStart')
    elif event == 'Stop':
        start(h)
        h['final']('R-1 complete')
    payload = {'session_id': 'native-1', 'hook_event_name': event, 'cwd': str(h['root']),
               'prompt': 'Create result.txt.',
               'transcript_path': str(Path(h['root']).parent / 'transcript.jsonl')}
    stdout, stderr = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(payload)))
    script = {'SessionStart': 'session_start', 'UserPromptSubmit': 'user_prompt_submit', 'Stop': 'stop'}[event]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        with pytest.raises(SystemExit) as result:
            runpy.run_path(str(ROOT / 'plugin/hooks' / (script + '.py')), run_name='__main__')
    assert result.value.code == 0
    response = json.loads(stdout.getvalue())
    assert response.get('decision') == 'block' if event == 'Stop' else response['hookSpecificOutput']['hookEventName'] == event
    assert 'warning:' not in stderr.getvalue()


def test_v3_demo_two_session_evidence_checker(harness: dict[str, Any], tmp_path: Path) -> None:
    from plugin import v3_demo
    h = harness
    out = tmp_path / 'capture'
    out.mkdir()
    h['control']['questions'] = True
    start(h)
    # Save the actual first-prompt pause context before the explicit user answer.
    question_context = h['drive']('UserPromptSubmit', prompt='please clarify')
    h['final']('Which release?')
    assert h['drive']('Stop') is None
    h['drive']('UserPromptSubmit', prompt='{"answers":{"Q-1":"release-unique"}}')
    (h['root'] / 'result.txt').write_text('release-unique\n')
    h['final']('R-1 complete with result.txt evidence')
    h['drive']('Stop')
    h['ledger']()
    h['final']('R-1 complete; ledger saved')
    h['drive']('Stop')
    context = h['drive']('SessionStart', session_id='native-2')
    h['control']['questions'] = False
    h['drive']('UserPromptSubmit', session_id='native-2', prompt='Create result.txt.')
    (h['root'] / 'followup.txt').write_text('release-unique\n')
    h['final']('R-1 complete with followup.txt evidence')
    h['drive']('Stop', session_id='native-2')
    h['ledger']('native-2')
    h['final']('R-1 complete; second ledger saved')
    h['drive']('Stop', session_id='native-2')
    write(out / 'experiment.json', {'workspace': str(h['root'])})
    events = [{'input': {'session_id': 'native-1'}, 'output': question_context},
              {'input': {'session_id': 'native-2'}, 'output': context}]
    (out / 'hooks.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
    for name in ('session1.terminal', 'session2.terminal'):
        (out / name).write_text('SYNTHETIC terminal fixture\n')
    assert v3_demo.check(out)['overall'] == 'pass'
    (h['root'] / 'followup.txt').write_text('wrong\n')
    with pytest.raises(ValueError, match='release label'):
        v3_demo.check(out)
