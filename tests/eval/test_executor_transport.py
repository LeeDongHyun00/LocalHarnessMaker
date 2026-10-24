"""Outage classification, retained recovery and accounting without model calls."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core, reaudit, regrade, rerun_invalid, transport
from eval.runner.audit import digest
from eval.runner.process import ProcessResult
from tests.eval.test_runner import Executor, setup, two_session_config


VERSION = 'codex-cli 0.162.0-alpha.17.2'
TIMEOUT = 'stream disconnected before completion: No route to host (os error 65)'
ROUTING = 'workspace routing discovery timed out'
FIXTURES = Path(__file__).parent / 'fixtures/executor-transport'
TAIL_HASHES = {
    'deadline-tail.jsonl': '048063ce1e1bca36c88cd94da3692bed2586260220c8ce832352f7de8449aab5',
    'deadline-tail-model-error.jsonl': 'b241b31104f1c33c54449c0f780888dca95f3303aaa704a77028ff088f80e8ae',
}


def error_item(message: str) -> dict[str, Any]:
    return {'type': 'item.completed', 'item': {'type': 'error', 'id': 'error_1', 'message': message}}


def stream(shape: str) -> list[dict[str, Any]]:
    message = TIMEOUT if shape == 'timeout' else ROUTING
    result = [{'type': 'thread.started', 'thread_id': 'unit-session'}, {'type': 'turn.started'},
              {'type': 'item.completed', 'item': {'id': 'work', 'type': 'agent_message', 'text': 'Working.'}}]
    result.extend(error_item(f'Reconnecting... {n}/5 ({message})') for n in range(1, 6))
    if shape == 'timeout':
        result.append(error_item('Reconnecting... 5/5 (request timed out)'))
    else:
        result.append({'type': 'turn.failed', 'error': {'message': message}})
    return result


def write_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))


@pytest.mark.parametrize('shape', ['timeout', 'failed'])
def test_real_transport_shapes_keep_line_evidence(tmp_path: Path, shape: str) -> None:
    path = tmp_path / 'exec-1.jsonl'
    write_events(path, stream(shape))
    segment = {'attempt': 1, 'events': path.name, 'exit_code': -9 if shape == 'timeout' else 1,
               'timed_out': shape == 'timeout'}
    failure = transport.classify(segment, tmp_path, lambda text: text.replace('host', '[REDACTED]'))
    assert failure and failure['reason'] == transport.REASON
    assert failure['errors'][0]['line'] == 4
    assert failure['errors'][-1]['line'] == len(stream(shape))
    assert failure['errors'][0]['evidence_sha256'] == digest(path.read_text().split('\n')[3].encode())
    assert 'host' not in json.dumps(failure)
    assert failure['log_sha256'] == digest(path.read_bytes())


@pytest.mark.parametrize('message', [
    'stream disconnected before completion', 'workspace routing discovery timed out',
    'No route to host (os error 65)', 'request timed out',
    'Falling back from WebSockets to HTTPS transport',
    'Reconnecting... waiting for network (Connection failed: error sending request)',
    'Reconnecting... 1/5 (arbitrary reconnect reason)',
    'Reconnecting... (another reason)', 'Connection failed: error sending request',
    'Transport error: timeout', 'failed to lookup address information', 'waiting for network',
])
def test_transport_error_family(tmp_path: Path, message: str) -> None:
    write_events(tmp_path / 'exec.jsonl', [error_item(message), {'type': 'turn.failed', 'error': {'message': message}}])
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': 1}, tmp_path, str)


@pytest.mark.parametrize('name', TAIL_HASHES)
@pytest.mark.parametrize('exit_code', [-9, None])
def test_verbatim_deadline_tail(tmp_path: Path, name: str, exit_code: int | None) -> None:
    data = (FIXTURES / name).read_bytes()
    assert digest(data) == TAIL_HASHES[name]
    path = tmp_path / 'exec.jsonl'
    path.write_bytes(data)
    failure = transport.classify({'attempt': 1, 'events': path.name, 'exit_code': exit_code,
                                  'timed_out': True}, tmp_path, str)
    if name == 'deadline-tail-model-error.jsonl':
        assert failure is None
    else:
        assert failure and failure['reason'] == transport.REASON
        assert failure['exit_code'] == exit_code
        assert [row['line'] for row in failure['errors']] == list(range(4, 16))
        assert failure['log_sha256'] == TAIL_HASHES[name]
        assert all(row['evidence_sha256'] == digest(data.splitlines()[row['line'] - 1])
                   for row in failure['errors'])


@pytest.mark.parametrize('tail', [
    [{'type': 'item.started', 'item': {'id': 'later', 'type': 'command_execution'}}],
    [{'type': 'unknown_event'}],
    [{'type': 'token_count'}],
    [{'type': 'error', 'message': 'Model could not produce a valid response'}],
    [{'type': 'turn.completed'}, {'type': 'error', 'message': 'Model timeout'}],
])
def test_deadline_tail_cannot_restart_after_later_activity(tmp_path: Path, tail: list[dict[str, Any]]) -> None:
    events = [json.loads(line) for line in (FIXTURES / 'deadline-tail.jsonl').read_text().splitlines()]
    write_events(tmp_path / 'exec.jsonl', [*events[:8], *tail, *events[8:]])
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': -9,
                               'timed_out': True}, tmp_path, str) is None


@pytest.mark.parametrize('exit_code,timed_out', [(None, False), (-9, False), (1, True), (0, True)])
def test_deadline_tail_requires_kill_metadata(tmp_path: Path, exit_code: int | None, timed_out: bool) -> None:
    (tmp_path / 'exec.jsonl').write_bytes((FIXTURES / 'deadline-tail.jsonl').read_bytes())
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': exit_code,
                               'timed_out': timed_out}, tmp_path, str) is None


def test_reconnect_wrapper_matches_terminal_reason(tmp_path: Path) -> None:
    message = 'Connection failed: error sending request'
    write_events(tmp_path / 'exec.jsonl', [error_item(f'Reconnecting... waiting for network ({message})'),
                                         {'type': 'turn.failed', 'error': {'message': message}}])
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': 1}, tmp_path, str)


@pytest.mark.parametrize('tail', [
    [{'type': 'turn.completed'}],
    [{'type': 'turn.failed', 'error': {'message': 'Model could not produce a valid response'}}],
    [{'type': 'turn.failed', 'error': {'message': 'Different transport request timed out'}}],
    [{'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'request timed out'}}],
    [{'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'python verify.py', 'exit_code': 1}}],
    [{'type': 'error', 'message': 'Model failure'}, error_item(TIMEOUT)],
])
def test_transport_prefix_cannot_hide_later_model_outcomes(tmp_path: Path, tail: list[dict[str, Any]]) -> None:
    write_events(tmp_path / 'exec.jsonl', [error_item(TIMEOUT), *tail])
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': -9, 'timed_out': True}, tmp_path, str) is None


def test_native_resume_boundaries_and_malformed_suffix(tmp_path: Path) -> None:
    path = tmp_path / 'native.jsonl'
    events = [{'timestamp': '2026-10-24T04:00:02Z', **error_item(TIMEOUT)},
              {'timestamp': '2026-10-24T04:00:03Z', 'type': 'turn.failed', 'error': {'message': TIMEOUT}},
              {'timestamp': '2026-10-24T04:01:02Z', 'type': 'turn.completed'}]
    write_events(path, [{'type': 'session_meta', 'payload': {'id': 'unit-session'}}, *events])
    write_events(tmp_path / 'exec.jsonl', [{'type': 'thread.started', 'thread_id': 'unit-session'}])
    segment = {'attempt': 1, 'events': 'exec.jsonl', 'exit_code': 1, 'native_logs': [str(path)],
               'started_at': '2026-10-24T04:00:00Z', 'exited_at': '2026-10-24T04:00:05Z'}
    assert transport.classify(segment, tmp_path, str)['errors'][-1]['line'] == 3
    later = dict(segment, started_at='2026-10-24T04:01:00Z', exited_at='2026-10-24T04:01:05Z')
    assert transport.classify(later, tmp_path, str) is None
    write_events(tmp_path / 'exec.jsonl', stream('failed'))
    with (tmp_path / 'exec.jsonl').open('a') as output:
        output.write('truncated record\n')
    assert transport.classify(dict(segment, native_logs=[]), tmp_path, str) is None


class OutageExecutor(Executor):
    """Produce settings and structured outage evidence without final output."""

    def __init__(self, shape: str, *, recover: bool = False) -> None:
        super().__init__()
        self.shape, self.recover = shape, recover

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] == 'codex' or self.recover, 'Infrastructure-failed tasks must never be graded'
        result = super().__call__(argv, **kwargs)
        if argv[0] != 'codex' or self.recover and self.calls > 1:
            return result
        if self.shape in {'timeout', 'failed', 'deadline_record', 'deadline_model_error'}:
            if self.shape.startswith('deadline_'):
                name = 'deadline-tail.jsonl' if self.shape == 'deadline_record' else 'deadline-tail-model-error.jsonl'
                text = (FIXTURES / name).read_text().replace('/synthetic/runtime/workspace', str(kwargs['cwd']))
                events = [{'type': 'thread.started', 'thread_id': 'unit-session'}, {'type': 'turn.started'},
                          *[json.loads(line) for line in text.splitlines()]]
            else:
                events = stream(self.shape)
            if self.shape == 'timeout':
                events.append({'type': 'error', 'message': 'request timed out'})
            # Retain measured usage even for a failed call; unknown usage is
            # tested separately and must stay unknown, never fabricated zero.
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
            with native.open('a') as output:
                output.write(json.dumps({'type': 'event_msg', 'payload': {'type': 'token_count',
                    'info': {'total_token_usage': {'input_tokens': 20, 'cached_input_tokens': 5,
                                                   'output_tokens': 8}}}}) + '\n')
        elif self.shape == 'model_error':
            events = [{'type': 'thread.started', 'thread_id': 'unit-session'},
                      {'type': 'turn.failed', 'error': {'message': 'Model could not produce a valid response'}}]
        else:
            events = [{'type': 'thread.started', 'thread_id': 'unit-session'}, {'type': 'turn.completed'}]
        write_events(kwargs['stdout'], events)
        kwargs['stderr'].write_text('failed to refresh available models: request timed out\n'
                                    'http/request failed: error sending request for url (https://chatgpt.com/backend-api/...)\n')
        return ProcessResult(-9, timed_out=True) if self.shape in {
            'timeout', 'model_timeout', 'deadline_record', 'deadline_model_error'} else ProcessResult(1)


def finished_run(root: Path, config: Path, out: Path, execute: Any) -> dict[str, Any]:
    try:
        path = core.run(config, out, root, execute=execute, version=VERSION)
    except core.IncompleteRun:
        path = core.run(config, out, root, execute=execute, version=VERSION)
    return json.loads(path.read_text())


@pytest.mark.parametrize('shape', ['timeout', 'failed', 'model_timeout', 'model_error'])
def test_run_classification_and_provenance(setup: tuple[Path, Path, Path], shape: str) -> None:
    root, config, out = setup
    report = finished_run(root, config, out, OutageExecutor(shape))
    task = report['tasks'][0]
    expected = 'invalid' if shape in {'timeout', 'failed'} else 'timeout' if shape == 'model_timeout' else 'error'
    assert task['outcome'] == expected
    assert (transport.REASON in task['invalid_reasons']) == (expected == 'invalid')
    assert task['grading'] is None
    if expected == 'invalid':
        result = json.loads((out / task['task_id'] / 'result.json').read_text())
        evidence = result['diagnostics']['executor_transport_failures']
        assert evidence and not evidence[0]['resolved_by_resume']
        diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
        assert diagnostics['executor_transport_failures'][0]['task_id'] == task['task_id']
        assert any(Path(a['path']).name == 'infrastructure-provenance.json' for a in task['artifacts'])
        assert task['costs']['executor_usd'] == pytest.approx(.0001105)
        assert report['metrics']['pass_rate']['sample_size'] == 0


@pytest.mark.parametrize('shape', ['timeout', 'failed'])
def test_regrade_reclassifies_legacy_outage_and_reaudit_is_readonly(
    setup: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str,
) -> None:
    root, config, source = setup
    with monkeypatch.context() as patch:
        patch.setattr(transport, 'inspect', lambda *args: [])
        original = finished_run(root, config, source, OutageExecutor(shape))
    assert original['tasks'][0]['outcome'] == ('timeout' if shape == 'timeout' else 'error')
    before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
    rows = reaudit.reaudit(root, source)
    assert rows[0]['invalid_reasons'] == [transport.REASON]
    assert rows[0]['executor_transport_failures'][0]['errors'][0]['line'] == 4

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Reclassifying infrastructure failures must not execute or grade anything')

    out = tmp_path / 'regraded'
    report = json.loads(regrade.regrade(root, source, out, execute=forbidden).read_text())
    assert report['tasks'][0]['outcome'] == 'invalid'
    assert transport.REASON in report['tasks'][0]['invalid_reasons']
    assert report['tasks'][0]['costs'] == original['tasks'][0]['costs']
    assert report['accounting']['invalid_tasks'] == 1
    assert 'transport.py' in regrade.audit_code_version()
    assert json.loads((out / 'run-diagnostics.json').read_text())['executor_transport_failures']
    assert before == {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}


@pytest.mark.parametrize('shape', ['deadline_record', 'deadline_model_error', 'model_timeout'])
def test_regrade_retained_deadline_record(
    setup: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str,
) -> None:
    root, config, source = setup
    with monkeypatch.context() as patch:
        patch.setattr(transport, 'inspect', lambda *args: [])
        original = finished_run(root, config, source, OutageExecutor(shape))
    assert original['tasks'][0]['outcome'] == 'timeout'
    before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Retained deadline classification must not call models or graders')

    out = tmp_path / 'regraded'
    report = json.loads(regrade.regrade(root, source, out, execute=forbidden).read_text())
    task = report['tasks'][0]
    outage = shape == 'deadline_record'
    assert task['outcome'] == ('invalid' if outage else 'timeout')
    assert (transport.REASON in task['invalid_reasons']) == outage
    assert task['grading'] is None
    assert task['costs'] == original['tasks'][0]['costs']
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())['executor_transport_failures']
    assert bool(diagnostics) == outage
    if outage:
        assert [row['line'] for row in diagnostics[0]['errors']] == list(range(6, 18))
        assert report['accounting']['invalid_tasks'] == 1
    assert before == {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}


@pytest.mark.parametrize('shape', ['timeout', 'failed'])
def test_rerun_transport_failure_is_fresh_audited_and_priced(
    setup: tuple[Path, Path, Path], tmp_path: Path, shape: str,
) -> None:
    root, config, source = setup
    original = finished_run(root, config, source, OutageExecutor(shape))
    state = json.loads((source / 'checkpoint.json').read_text())
    old_runtime = state['tasks']['bug-chunk-tail']['runtime']
    executor = Executor()

    def fresh(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex':
            assert 'resume' not in argv
            assert str(kwargs['cwd'].parent) != old_runtime
            assert 'len(items) - 1' in (kwargs['cwd'] / 'chunking.py').read_text()
        return executor(argv, **kwargs)

    out = tmp_path / 'rerun'
    report = json.loads(rerun_invalid.rerun_invalid(root, source, out, {transport.REASON},
                                                   execute=fresh, version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and executor.calls == 1
    assert task['grader_access_audit']['status'] == 'clean'
    assert len(task['calls']) == 2
    assert task['costs']['executor_usd'] == pytest.approx(original['tasks'][0]['costs']['executor_usd'] + .0001105)
    evidence = json.loads((out / 'bug-chunk-tail/rerun-provenance.json').read_text())
    assert evidence['source_outcome'] == 'invalid'
    assert evidence['infrastructure_causes'][0]['reason'] == transport.REASON
    assert evidence['added_cost_usd'] == pytest.approx(.0001105)
    assert evidence['fresh_runtime'] != old_runtime
    assert evidence['accounting_policy'] == 'retain_prior_spending'
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    assert diagnostics['executor_transport_failures'][0]['rerun']['fresh_runtime'] == evidence['fresh_runtime']
    assert diagnostics['rerun_invalid']['selected_tasks'] == ['bug-chunk-tail']
    # Disclosure and prices survive another retained-evidence regrade.
    regraded = tmp_path / 'rerun-regraded'
    again = json.loads(regrade.regrade(root, out, regraded, execute=executor).read_text())
    assert again['tasks'][0]['costs'] == task['costs']
    assert json.loads((regraded / 'run-diagnostics.json').read_text())['executor_transport_failures'][0]['rerun']


def test_live_transport_failure_keeps_backoff_resume(
    setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, config, out = setup
    data = json.loads(config.read_text())
    data['retry_limit'] = 1
    config.write_text(json.dumps(data))
    waits = []
    monkeypatch.setattr(core, 'sleep', waits.append)
    executor = OutageExecutor('failed', recover=True)
    calls = []

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex':
            calls.append(argv)
        return executor(argv, **kwargs)

    report = json.loads(core.run(config, out, root, execute=execute, version=VERSION).read_text())
    assert executor.calls == 2 and 'resume' in calls[1]
    assert waits == [60]
    assert report['tasks'][0]['outcome'] == 'pass'
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    assert diagnostics['executor_transport_failures'][0]['resolved_by_resume'] is True


@pytest.mark.parametrize('terminal', ['turn.completed', 'turn.failed'])
def test_native_transport_does_not_override_exec_model_terminal(tmp_path: Path, terminal: str) -> None:
    native = tmp_path / 'native.jsonl'
    write_events(native, [{'type': 'session_meta', 'payload': {'id': 'unit-session'}},
                         {'timestamp': '2026-10-24T04:00:02Z', **error_item(TIMEOUT)}])
    write_events(tmp_path / 'exec.jsonl', [{'type': 'thread.started', 'thread_id': 'unit-session'},
                                         {'type': terminal, 'error': {'message': 'model error'}}])
    segment = {'attempt': 1, 'events': 'exec.jsonl', 'exit_code': -9, 'timed_out': True,
               'started_at': '2026-10-24T04:00:00Z', 'exited_at': '2026-10-24T04:00:05Z',
               'native_logs': [str(native)]}
    assert transport.classify(segment, tmp_path, str) is None


def test_transport_rerun_refuses_unproven_causes_and_dirty_audits() -> None:
    audit = {'status': 'clean', 'matches': [], 'errors': []}
    task = {'outcome': 'invalid', 'invalid_reasons': [transport.REASON], 'grader_access_audit': audit}
    entry = {'result': dict(task), 'segments': [{'attempt': 1, 'events': 'exec.jsonl',
                                               'exit_code': 1}]}
    failure = {'attempt': 1, 'resolved_by_resume': False}
    assert not rerun_invalid.eligible(task, entry, audit)
    assert rerun_invalid.eligible(task, entry, audit, transport_failures=[failure])
    for bad in [{'status': 'access_detected', 'matches': [{}], 'errors': []},
                {'status': 'inconclusive', 'matches': [], 'errors': ['unresolved_operand:exec.jsonl:3']},
                {'status': 'inconclusive', 'matches': [], 'errors': ['unfinished_tool_events']}]:
        assert not rerun_invalid.eligible(task, entry, bad, transport_failures=[failure])


def test_unknown_outage_usage_stays_unknown_through_priced_rerun(
    setup: tuple[Path, Path, Path], tmp_path: Path,
) -> None:
    root, config, source = setup
    outage = OutageExecutor('failed')

    def unknown(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = outage(argv, **kwargs)
        native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
        events = [e for e in map(json.loads, native.read_text().splitlines())
                  if e.get('payload', {}).get('type') != 'token_count']
        write_events(native, events)
        return result

    original = finished_run(root, config, source, unknown)
    assert original['tasks'][0]['costs']['executor_usd'] is None
    out = tmp_path / 'rerun'
    report = json.loads(rerun_invalid.rerun_invalid(root, source, out, {transport.REASON},
                                                   execute=Executor(), version=VERSION).read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert report['tasks'][0]['calls'][0]['usage']['usd'] is None
    assert report['tasks'][0]['calls'][1]['usage']['usd'] == pytest.approx(.0001105)
    assert report['tasks'][0]['costs']['total_usd'] is None


def test_day1_outage_does_not_launch_day2(
    setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = OutageExecutor('failed')
    report = finished_run(root, config, out, executor)
    assert executor.calls == 1
    assert report['tasks'][0]['outcome'] == 'invalid'
    assert transport.REASON in report['tasks'][0]['invalid_reasons']
    assert 'missing_two_session_handoff_observation' in report['tasks'][0]['invalid_reasons']


def test_outage_after_completed_prior_turn_classifies_only_last_turn(tmp_path: Path) -> None:
    write_events(tmp_path / 'exec.jsonl', [{'type': 'turn.completed'}, *stream('failed')])
    assert transport.classify({'attempt': 1, 'events': 'exec.jsonl', 'exit_code': 1}, tmp_path, str)
