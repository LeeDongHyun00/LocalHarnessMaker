"""Offline restart, audit precision, signal and selective rerun regressions."""

import copy
import json
import os
from pathlib import Path
import shlex
import signal
from typing import Any

import pytest

from eval.runner import core, harness, regrade, rerun_invalid
from eval.runner.audit import PrivateGraders, audit_logs, command_operands, digest
from eval.runner.limits import capacity_message
from eval.runner.process import ProcessResult, run_process
from eval.runner.telemetry import records
from tests.eval.test_runner import Executor, HarnessExecutor, harness_config, setup, two_task_config


VERSION = 'codex-cli 0.162.0-alpha.17.2'


def test_unicode_line_separators_are_json_data(tmp_path: Path) -> None:
    root = tmp_path / 'private'
    (root / 'task').mkdir(parents=True)
    (root / 'task/test_synthetic.py').write_text('# harmless synthetic grader\n')
    private = PrivateGraders.load(root, 'task', tmp_path / 'repo')
    text = 'NEL\u0085LS\u2028PS\u2029end'
    events = [
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': text}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 1}},
    ]
    log = tmp_path / 'exec.jsonl'
    log.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in events))
    native = tmp_path / 'native.jsonl'
    native.write_text(json.dumps({'type': 'response_item', 'payload': {
        'type': 'message', 'role': 'assistant', 'content': text}}, ensure_ascii=False) + '\n')
    assert len(log.read_text().splitlines()) == 5
    assert records(log) == events
    assert records(native)[0]['payload']['content'] == text
    audit = audit_logs([log, native], private)
    assert audit['status'] == 'clean', audit
    assert private.redact(log.read_text()) == log.read_text()
    envelope = tmp_path / 'contract.stderr'
    envelope.write_text('control_cli_events ' + json.dumps({'events': json.dumps({
        'type': 'error', 'message': text + ' at capacity'}, ensure_ascii=False) + '\n'}, ensure_ascii=False) + '\n')
    assert capacity_message([envelope]) == text + ' at capacity'


@pytest.mark.parametrize('quoted', [True, False])
def test_heredoc_body_quotes_do_not_consume_following_commands(tmp_path: Path, quoted: bool) -> None:
    # Same host command shape: an inline Python raw regex with mixed quotes,
    # followed by compile and unittest commands outside the quoted heredoc.
    body = "import re\npattern = r'''(?:'|\"|\\\\|\"\"\"|\\d+)'''\nprint(pattern)\n"
    delimiter = "'PY'" if quoted else 'PY'
    command = "python - <<" + delimiter + '\n' + body + 'PY\n'
    command += 'python -m py_compile solution.py\npython -m unittest discover -v'
    wrapped = '/bin/zsh -lc ' + shlex.quote(command)
    operands, unresolved = command_operands(wrapped, tmp_path, workspace=tmp_path)
    assert not unresolved
    assert (tmp_path / 'solution.py', False) in operands
    assert (tmp_path / 'discover', False) in operands
    # An unmatched quote is data, too; expansion in an unquoted body stays unknown.
    command = "cat <<'PY'\n'\"'''\\$UNEXPANDED\nPY\ncat after.txt"
    assert not command_operands(command, tmp_path, workspace=tmp_path)[1]
    assert command_operands(command.replace("'PY'", 'PY'), tmp_path, workspace=tmp_path)[1]
    assert command_operands("cat <<'PY'\nunclosed", tmp_path, workspace=tmp_path)[1]


@pytest.mark.parametrize('extra, expected', [
    ('', 'clean'), ('{"type":"unknown"}\n', 'inconclusive'),
    ('{"type":"item.started","item":{"id":"pending","type":"command_execution","command":"cat public"}}\n', 'inconclusive'),
    ('broken\n', 'inconclusive'),
])
def test_interrupted_terminal_exception_keeps_other_errors(tmp_path: Path, extra: str, expected: str) -> None:
    root = tmp_path / 'private'
    (root / 'task').mkdir(parents=True)
    (root / 'task/test_synthetic.py').write_text('# synthetic\n')
    private = PrivateGraders.load(root, 'task', tmp_path / 'repo')
    first, second = tmp_path / 'exec-1.jsonl', tmp_path / 'exec-2.jsonl'
    first.write_text('{"type":"thread.started","thread_id":"same"}\n' + extra)
    second.write_text('{"type":"thread.started","thread_id":"same"}\n{"type":"turn.completed"}\n')
    assert audit_logs([first, second], private)['status'] == 'inconclusive'
    audit = audit_logs([first, second], private, interrupted_paths={first}, workspace=tmp_path)
    assert audit['status'] == expected
    assert not any(error.startswith('missing_terminal_event') for error in audit['errors'])


@pytest.mark.parametrize('crash', ['partial', 'contract', 'changed', 'unowned'])
def test_prelaunch_resume_reuses_only_pinned_control_files(setup: tuple[Path, Path, Path], crash: str) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor()

    def stop(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        assert argv[0] != 'codex'
        if crash == 'partial':
            # Simulate hard host loss after pinned stdout/stderr/accounting but
            # before a contract was produced. _invoke_once's post-call pinning
            # does not execute on abrupt process loss.
            Path(argv[argv.index('--out') + 1]).rename(kwargs['stdout'].parent / 'unpublished-partial')
        raise RuntimeError('host restart')

    with pytest.raises(RuntimeError, match='host restart'):
        core.run(config, out, root, execute=stop, version=VERSION)
    path = out / 'checkpoint.json'
    state = json.loads(path.read_text())
    entry = state['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    # Reproduce the manifest state observed by the host at interruption.
    for name in ('contract.stdout', 'contract.stderr', 'contract.json'):
        file = runtime / name
        if file.is_file() and crash != 'unowned':
            entry['control_files'][name] = digest(file.read_bytes())
    if crash == 'changed':
        (runtime / 'contract.stdout').write_text('changed pinned evidence')
    path.write_text(json.dumps(state))
    assert entry['phase'] == 'ready' and entry['segments'] == []
    executor.operations.clear()
    report = json.loads(core.run(config, out, root, execute=executor, version=VERSION).read_text())
    task = report['tasks'][0]
    if crash in {'changed', 'unowned'}:
        assert task['outcome'] == 'invalid' and executor.calls == 0
    else:
        assert task['outcome'] == 'pass' and executor.calls == 2
        assert executor.operations.count('contract') == int(crash == 'partial')
        if crash == 'partial':
            assert list((runtime / 'control-interruptions').rglob('*.control.json'))


def test_hard_restart_resume_and_regrade_terminal_exception(setup: tuple[Path, Path, Path], tmp_path: Path) -> None:
    root, config, out = setup
    executor = Executor()

    def killed(argv: list[str], **kwargs: Any) -> ProcessResult:
        executor(argv, **kwargs)
        kwargs['stdout'].write_text('{"type":"thread.started","thread_id":"unit-session"}\n')
        raise RuntimeError('host restart')

    with pytest.raises(RuntimeError):
        core.run(config, out, root, execute=killed, version=VERSION)
    report = json.loads(core.run(config, out, root, execute=executor, version=VERSION).read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert report['tasks'][0]['attempts'] == 2
    checkpoint = json.loads((out / 'checkpoint.json').read_text())
    assert checkpoint['tasks']['bug-chunk-tail']['segments'][0]['interrupted'] is True
    executor.calls = 0

    def grade_only(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] != 'codex'
        return executor(argv, **kwargs)

    recovered = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=grade_only).read_text())
    assert recovered['tasks'][0]['outcome'] == 'pass'


@pytest.mark.parametrize('sig', [signal.SIGINT, signal.SIGTERM])
@pytest.mark.parametrize('where', ['prelaunch', 'executor'])
def test_cli_signals_persist_reason_and_exit_130(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str], sig: int, where: str) -> None:
    import eval.__main__ as cli
    out = tmp_path / 'out'
    monkeypatch.setenv('LHM_PRIVATE_GRADERS', '/synthetic-unused')
    monkeypatch.setattr('sys.argv', ['eval', 'run', '--config', 'unused', '--out', str(out)])
    before = signal.getsignal(sig)

    def interrupted(*args: Any) -> Path:
        os.kill(os.getpid(), sig)
        raise AssertionError('Signal must interrupt')

    def consumed(*args: Any) -> Path:
        try:
            interrupted()
        except KeyboardInterrupt:
            core.write_json(out / 'run-diagnostics.json', {'stop_reason': 'generic', 'retained': True})
            raise core.IncompleteRun('executor interrupted')

    monkeypatch.setattr(cli, 'run', interrupted if where == 'prelaunch' else consumed)
    assert cli.main() == 130
    captured = capsys.readouterr()
    assert captured.out == '' and 'Traceback' not in captured.err
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    assert diagnostics['stop_reason'] == signal.Signals(sig).name
    assert diagnostics['exit_code'] == 130
    assert signal.getsignal(sig) == before


def infrastructure_source(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                          tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create two retained tasks and mark one historical infrastructure interruption."""
    from eval.runner import report as reports
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    original = json.loads(core.run(config, out, root, execute=Executor(), version=VERSION).read_text())
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    entry['segments'][0].update(exit_code=-2, interrupted=True)
    result = entry['result']
    result.update(outcome='invalid', invalid_reasons=['execution_interrupted'], grading=None,
                  segments=copy.deepcopy(entry['segments']))
    core.write_json(out / 'bug-chunk-tail/result.json', result)
    tasks = [reports.build_task(state['tasks'][t['task_id']]['result'], state['tasks'][t['task_id']],
                               out / t['task_id'], state['config'], original['metadata']['pricing'], t)
             for t in original['tasks']]
    fresh = reports.build(state['config'], state, tasks, VERSION, Path(__file__).resolve().parents[2])
    core.write_json(out / 'checkpoint.json', state)
    core.write_json(out / 'report.json', fresh)
    return root, config, out


def test_selective_fresh_rerun_regrades_rest_and_preserves_costs(setup: tuple[Path, Path, Path],
                                                              monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, config, source = infrastructure_source(setup, monkeypatch, tmp_path)
    original = json.loads((source / 'report.json').read_text())
    before = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    state = json.loads((source / 'checkpoint.json').read_text())
    old_runtimes = {Path(e['runtime']) for e in state['tasks'].values()}
    executor = Executor()
    grades = []

    def fresh_only(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex':
            assert 'resume' not in argv
            assert kwargs['cwd'].parent not in old_runtimes
            assert 'len(items) - 1' in (kwargs['cwd'] / 'chunking.py').read_text()
            return executor(argv, **kwargs)
        grades.append(kwargs['cwd'])
        return run_process(argv, **kwargs)

    out = tmp_path / 'rerun'
    new = json.loads(rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'},
                                                execute=fresh_only, version=VERSION).read_text())
    assert executor.calls == 1 and len(grades) == 2  # one regrade + one fresh run
    assert all(t['outcome'] == 'pass' for t in new['tasks'])
    assert new['accounting']['total_cost_usd'] == pytest.approx(original['accounting']['total_cost_usd'] * 1.5)
    task = next(t for t in new['tasks'] if t['task_id'] == 'bug-chunk-tail')
    assert len(task['calls']) == 2 and len(task['executor_segments']) == task['attempts'] == 1
    assert len({c['call_id'] for c in task['calls']}) == 2
    evidence = json.loads((out / 'bug-chunk-tail/rerun-provenance.json').read_text())
    assert evidence['source_report_sha256'] == digest((source / 'report.json').read_bytes())
    assert evidence['invalid_reasons'] == ['execution_interrupted']
    assert evidence['source_executor_segments'][0]['exit_code'] == -2
    assert json.loads((out / 'rerun-invalid.json').read_text())['status'] == 'finished'
    assert before == {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    # Regrading or checkpoint resume cannot drop or double-count prior spending.
    executor.finished = True
    graded = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=executor).read_text())
    assert graded['accounting'] == new['accounting']
    resumed = json.loads(core.run(out / 'rerun-config.yaml', out, root, execute=fresh_only, version=VERSION,
                                 _recorded_config_sha256=state['config_sha256']).read_text())
    assert resumed['accounting'] == new['accounting'] and executor.calls == 1


@pytest.mark.parametrize('case', ['historical_access', 'current_access', 'malformed', 'outcome',
                                  'unknown_reason', 'changed_control', 'precision_only'])
def test_rerun_refuses_noninfrastructure_before_any_call(setup: tuple[Path, Path, Path],
                                                       monkeypatch: pytest.MonkeyPatch,
                                                       tmp_path: Path, case: str) -> None:
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    state = json.loads((source / 'checkpoint.json').read_text())
    original = json.loads((source / 'report.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    selected = next(t for t in original['tasks'] if t['task_id'] == 'bug-chunk-tail')
    runtime = Path(entry['runtime'])
    reasons = {'execution_interrupted'}
    if case == 'historical_access':
        entry['result']['grader_access_audit']['matches'] = [{'marker': 'synthetic'}]
    elif case == 'current_access':
        log = runtime / 'exec-1.jsonl'
        log.write_text(json.dumps({'type': 'item.completed', 'item': {
            'type': 'command_execution', 'command': 'cat ' + str(root / 'anything')}}) + '\n{"type":"turn.completed"}\n')
    elif case == 'malformed':
        (runtime / 'exec-1.jsonl').write_text('broken\n')
    elif case == 'outcome':
        selected['outcome'] = entry['result']['outcome'] = 'fail'
    elif case == 'unknown_reason':
        selected['invalid_reasons'].append('unexplained_invalidity')
    elif case == 'precision_only':
        reasons = {'incomplete_access_audit'}
        entry['segments'][0].pop('interrupted')
        selected['invalid_reasons'] = entry['result']['invalid_reasons'] = list(reasons)
        entry['result']['grader_access_audit']['errors'] = ['unresolved_operand:exec-1.jsonl:1']
    elif case == 'changed_control':
        path = runtime / 'contract.stdout'
        path.write_text('changed')
        entry['control_files'] = {'contract.stdout': '0' * 64}
    core.write_json(source / 'checkpoint.json', state)
    core.write_json(source / 'report.json', original)

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        raise AssertionError('Refusal must precede every model and grading call')

    destination = tmp_path / 'refused'
    with pytest.raises((ValueError, harness.HarnessError)):
        rerun_invalid.rerun_invalid(root, source, destination, reasons, execute=forbidden, version=VERSION)
    assert not destination.exists()


@pytest.mark.parametrize('deadline', [False, True])
def test_rerun_prelaunch_control_failure_needs_no_exit_hash(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                          deadline: bool) -> None:
    root, config, source = setup
    harness_config(config)
    historical = HarnessExecutor(fail_contract=True)

    def failure(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = historical(argv, **kwargs)
        if deadline:
            kwargs['stderr'].write_text('control_failure {"reason":"deadline"}\n')
        return result

    report = json.loads(core.run(config, source, root, execute=failure, version=VERSION).read_text())
    assert historical.calls == 0 and report['tasks'][0]['outcome'] == 'invalid'
    state = json.loads((source / 'checkpoint.json').read_text())
    assert 'workspace_exit_sha256' not in state['tasks']['bug-chunk-tail']
    executor = HarnessExecutor()
    reason = 'control_timeout' if deadline else 'control_cli_error'
    new = json.loads(rerun_invalid.rerun_invalid(root, source, tmp_path / 'new', {reason},
                                                execute=executor, version=VERSION).read_text())
    assert new['tasks'][0]['outcome'] == 'pass' and executor.calls == 2
    assert new['tasks'][0]['costs']['control_usd'] is None  # Unknown original spending stays unknown.
    assert len(new['tasks'][0]['calls']) == len(report['tasks'][0]['calls']) + 2


@pytest.mark.parametrize('reason', ['', 'grader_access_detected', 'fail', 'unresolved_operand'])
def test_rerun_rejects_unsafe_reason_selectors(tmp_path: Path, reason: str) -> None:
    with pytest.raises(ValueError, match='Unsupported'):
        rerun_invalid.rerun_invalid(tmp_path / 'unused', tmp_path / 'unused', tmp_path / 'new', {reason})


def test_rerun_cli_conventions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                               capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / 'new'
    monkeypatch.setattr('sys.argv', ['rerun_invalid', '--private-root', '/synthetic-unused', '--from', 'source',
                                     '--out', str(out), '--reasons', 'control_cli_error,execution_interrupted'])
    observed = []

    def mock(*args: Any) -> Path:
        observed.append(args[-1])
        return out / 'report.json'

    monkeypatch.setattr(rerun_invalid, 'rerun_invalid', mock)
    assert rerun_invalid.main() == 0
    assert observed == [{'control_cli_error', 'execution_interrupted'}]
    assert capsys.readouterr().out == str(out) + '\n'


@pytest.mark.parametrize('capacity', [False, True])
def test_capacity_and_restart_missing_logs_are_infrastructure_only(capacity: bool) -> None:
    segment = {'events': 'exec-1.jsonl', 'exit_code': 1, 'capacity_error': True} if capacity else {
        'events': 'exec-1.jsonl', 'exit_code': -2, 'interrupted': True}
    audit = {'status': 'clean', 'matches': [], 'errors': []} if capacity else {
        'status': 'inconclusive', 'matches': [], 'errors': ['missing_log:exec-1.jsonl']}
    reasons = ['capacity_exhausted'] if capacity else ['incomplete_access_audit', 'execution_interrupted']
    result = {'outcome': 'invalid', 'invalid_reasons': reasons, 'grader_access_audit': audit}
    entry = {'segments': [segment], 'result': result}
    if capacity:
        entry['infrastructure_stop'] = 'Selected model is at capacity'
    task = {'outcome': 'invalid', 'invalid_reasons': reasons, 'grader_access_audit': audit}
    assert rerun_invalid.eligible(task, entry, audit)
    changed = copy.deepcopy(audit)
    changed.update(status='inconclusive', errors=['unresolved_operand:exec-1.jsonl:1'])
    assert not rerun_invalid.eligible(task, entry, changed)
