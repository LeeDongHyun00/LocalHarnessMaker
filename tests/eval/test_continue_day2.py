"""Recover synthetic day-1 audit stops without touching retained source evidence."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import continue_day2, core, regrade
from eval.runner.audit import digest
from eval.runner.process import ProcessResult, run_process
from tests.eval.test_runner import Executor, TwoSessionExecutor, setup, two_session_config


VERSION = 'codex-cli 0.162.0-alpha.17.2'


def snapshot(root: Path) -> dict[str, bytes | str]:
    """Include symlink targets without following external credential references."""
    return {str(p.relative_to(root)): str(p.readlink()) if p.is_symlink() else p.read_bytes()
            for p in root.rglob('*') if p.is_symlink() or p.is_file()}


@pytest.fixture(params=[False, True], ids=['baseline', 'harness'])
def stopped(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
            tmp_path: Path, request: pytest.FixtureRequest) -> tuple[Path, Path, TwoSessionExecutor]:
    return make_stopped(setup, monkeypatch, tmp_path, harness_on=request.param)


def make_stopped(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                 tmp_path: Path, *, harness_on: bool, include_other: bool = False,
                 population: bool = False) -> tuple[Path, Path, TwoSessionExecutor]:
    """Create a historical parser failure with real hash-pinned synthetic evidence."""
    root, config, source = two_session_config(setup, monkeypatch, tmp_path, harness_on=harness_on)
    if include_other or population:
        value = json.loads(config.read_text())
        if include_other:
            value['tasks'].append('second-task')
        if population:
            value['task_population'] = ['bug-chunk-tail', 'second-task']
        config.write_text(json.dumps(value))
    executor = TwoSessionExecutor()
    other = Executor()
    original = core.audit_logs

    def old_parser(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original(*args, **kwargs)
        if any(p.name == 'rollout-day-1.jsonl' for p in args[0]):
            result['status'] = 'inconclusive'
            result['errors'].append('unresolved_custom_input:synthetic-day1')
        return result

    def with_literal_patch(argv: list[str], **kwargs: Any) -> ProcessResult:
        if include_other and argv[0] == 'codex':
            state = json.loads((source / 'checkpoint.json').read_text())
            selected = next(t for t, e in state['tasks'].items() if Path(e['runtime']) == kwargs['cwd'].parent)
            if selected == 'second-task':
                return other(argv, **kwargs)
        if include_other and argv[0] != 'codex':
            return run_process(argv, **kwargs)
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-day-1.jsonl'
            patch = '*** Begin Patch\nX*** Update File: chunking.py\n@@\n-old\n+new\n*** End Patch\n'
            events = [{'type': 'response_item', 'payload': {
                'type': 'custom_tool_call', 'call_id': 'literal-call', 'name': 'exec',
                'input': 'text(await tools.apply_patch(' + json.dumps(patch) + '.replace(\'X\',\'\')));'}},
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
                 'call_id': 'literal-call', 'output': 'ok'}}]
            # Absolute day-1 workspace operands must retain their old context.
            events.append({'type': 'response_item', 'payload': {'type': 'function_call',
                           'call_id': 'cwd-call', 'name': 'exec_command',
                           'arguments': json.dumps({'cmd': 'cat chunking.py', 'workdir': str(kwargs['cwd'])})}})
            events.append({'type': 'response_item', 'payload': {'type': 'function_call_output',
                           'call_id': 'cwd-call', 'output': 'ok'}})
            with native.open('a') as stream:
                stream.write(''.join(json.dumps(e) + '\n' for e in events))
        return result

    with monkeypatch.context() as historical:
        historical.setattr(core, 'audit_logs', old_parser)
        report = json.loads(core.run(config, source, root, execute=with_literal_patch, version=VERSION).read_text())
    task = next(t for t in report['tasks'] if t['task_id'] == 'bug-chunk-tail')
    assert set(task['invalid_reasons']) == continue_day2.RECOVERABLE
    assert executor.calls == 1 and executor.grades == 0
    return root, source, executor


def continuation_executor(executor: TwoSessionExecutor, source_runtime: Path) -> Any:
    """Use existing mocked protocols while requiring a new copied workspace."""
    original_workspace = executor.workspaces[0]

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex':
            assert kwargs['cwd'] != original_workspace
            assert not kwargs['cwd'].is_relative_to(core.REPOSITORY)
            assert not kwargs['cwd'].is_relative_to(source_runtime)
            assert 'resume' not in argv
            assert kwargs['env']['HARNESS_NESTED'] == '1'
            # Fixture checks same-workspace semantics within the continued run.
            executor.workspaces[0] = kwargs['cwd']
        return executor(argv, **kwargs)

    return execute


def test_continuation_reuses_runner_and_preserves_source(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, source, executor = stopped
    old_report = json.loads((source / 'report.json').read_text())
    old_state = json.loads((source / 'checkpoint.json').read_text())
    old_entry = old_state['tasks']['bug-chunk-tail']
    old_runtime = Path(old_entry['runtime'])
    before, runtime_before = snapshot(source), snapshot(old_runtime)
    from tests.eval.test_recovery_estimates import install_estimate
    matched = install_estimate(old_state['config'], tmp_path, monkeypatch)
    out = tmp_path / 'continued'
    report_path = continue_day2.continue_day2(root, source, out,
        execute=continuation_executor(executor, old_runtime), version=VERSION)
    estimate = json.loads((out / 'run-diagnostics.json').read_text())['recovery_estimate']
    assert estimate == {'matched_estimate': matched, 'recovery_subset': True,
                        'paid_call_bound': core.paid_call_bound(dict(old_state['config'], tasks=['bug-chunk-tail'])),
                        'reasons': sorted(continue_day2.RECOVERABLE)}
    report = json.loads(report_path.read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['attempts'] == 2
    assert task['handoff']['day2_pass'] is True
    assert task['grader_access_audit']['status'] == 'clean'
    assert executor.calls == 2 and executor.grades == 1
    assert executor.operations in ([], ['contract', 'check', 'handoff', 'validate-handoff', 'contract', 'check'])
    assert task['calls'][0] == old_report['tasks'][0]['calls'][0]
    old_ids = {c['call_id'] for c in old_report['tasks'][0]['calls']}
    assert [c for c in task['calls'] if c['call_id'] in old_ids] == old_report['tasks'][0]['calls']
    assert len([c for c in task['calls'] if c['purpose'] == 'executor']) == 2
    assert task['costs']['executor_usd'] == pytest.approx(2 * .0001105)
    for key in ('config_sha256', 'task_set_sha256', 'executor_model', 'reasoning_effort', 'pricing', 'confidence'):
        assert report['metadata'][key] == old_report['metadata'][key]
    assert report['metadata']['run_id'] != old_report['metadata']['run_id']
    provenance = json.loads((out / 'continuation.json').read_text())
    evidence = provenance['tasks'][0]
    assert provenance['status'] == 'finished' and provenance['source_run_id'] == old_state['run_id']
    assert evidence['gap_seconds'] >= 0 and evidence['copy_hash_matched']
    assert evidence['day1_exited_at'] == old_entry['segments'][-1]['exited_at']
    assert evidence['day2_started_at'] > evidence['day1_exited_at']
    assert evidence['day1_workspace_exit_sha256'] == evidence['copied_workspace_sha256']
    assert evidence['audit_code_version']['javascript.py'] == digest((Path(core.__file__).parent / 'javascript.py').read_bytes())
    assert snapshot(source) == before and snapshot(old_runtime) == runtime_before
    state = json.loads((out / 'checkpoint.json').read_text())
    new_runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    assert core.valid_day2_observation(state['tasks']['bug-chunk-tail'], core.REPOSITORY / 'eval/tasks/bug-chunk-tail')
    assert (new_runtime / 'day2-delivered.md').read_bytes() == (core.REPOSITORY / 'eval/tasks/bug-chunk-tail/day2.md').read_bytes()
    assert (new_runtime / 'exec-1.jsonl').read_bytes() == (old_runtime / 'exec-1.jsonl').read_bytes()
    # Re-auditing and regrading a continued report keeps both contexts clean.
    assert continue_day2.reaudit.reaudit(root, out)[0]['status'] == 'clean'
    graded = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=executor).read_text())
    assert graded['tasks'][0]['outcome'] == 'pass' and executor.grades == 2
    assert graded['tasks'][0]['calls'] == task['calls']


@pytest.mark.parametrize('tier_record', ['absent', 'omitted', 'null', 'default'])
def test_continued_day2_prices_unrequested_cli_default(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                     tmp_path: Path, tier_record: str) -> None:
    root, source, executor = stopped
    old_report = json.loads((source / 'report.json').read_text())
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    base = continuation_executor(executor, Path(entry['runtime']))

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = base(argv, **kwargs)
        if argv[0] == 'codex':
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-day-2.jsonl'
            events = [json.loads(line) for line in native.read_text().splitlines()]
            for event in events:
                if event.get('payload', {}).get('type') == 'thread_settings_applied':
                    settings = event['payload']['thread_settings']
                    settings.pop('service_tier', None)
                    if tier_record in {'null', 'default'}:
                        settings['service_tier'] = None if tier_record == 'null' else 'default'
            if tier_record == 'absent':
                events = [e for e in events if e.get('payload', {}).get('type') != 'thread_settings_applied']
            native.write_text(''.join(json.dumps(e) + '\n' for e in events))
        return result

    out = tmp_path / 'continued-default'
    report = json.loads(continue_day2.continue_day2(root, source, out, execute=execute, version=VERSION).read_text())
    task = report['tasks'][0]
    assert report['validity']['status'] == 'valid' and task['outcome'] == 'pass'
    assert task['costs']['executor_usd'] == pytest.approx(2 * .0001105)
    assert task['calls'][0] == old_report['tasks'][0]['calls'][0]
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    evidence = entry['segments'][-1]['pricing_evidence']
    assert evidence['tier'] == 'standard'
    if tier_record != 'default':
        assert 'inferred from the model default' in evidence['basis']
    price_ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    provenance = json.loads(core.REPOSITORY.joinpath(price_ref['path']).read_text())
    fresh_call = next(c for c in task['calls'] if c['purpose'] == 'executor' and c['call_id'].endswith('-2'))
    row = next(p for p in provenance if p['call_id'] == fresh_call['call_id'])
    assert row['basis'] == evidence['basis'] and row['pricing_ref'] == fresh_call['usage']['pricing_ref']


@pytest.mark.parametrize('case', ['other_reason', 'detected', 'day2_present', 'failed_day1',
                                  'still_inconclusive', 'changed_log', 'changed_workspace', 'wrong_version'])
def test_continuation_refuses_ineligible_or_changed_evidence(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                            tmp_path: Path, case: str) -> None:
    root, source, _ = stopped
    report = json.loads((source / 'report.json').read_text())
    state = json.loads((source / 'checkpoint.json').read_text())
    task, entry = report['tasks'][0], state['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    if case == 'other_reason':
        task['invalid_reasons'].append('executor_settings_unverified')
        entry['result']['invalid_reasons'].append('executor_settings_unverified')
    elif case == 'detected':
        task['grader_access_audit']['status'] = entry['result']['grader_access_audit']['status'] = 'access_detected'
    elif case == 'day2_present':
        entry['segments'][0]['day'] = 2
    elif case == 'failed_day1':
        entry['segments'][0]['exit_code'] = 1
    elif case in {'changed_log', 'still_inconclusive'}:
        with (runtime / 'exec-1.jsonl').open('a') as stream:
            stream.write('{}\n' if case == 'still_inconclusive' else '\n')
    elif case == 'changed_workspace':
        (runtime / 'workspace/chunking.py').write_text('changed')
    (source / 'report.json').write_text(json.dumps(report))
    (source / 'checkpoint.json').write_text(json.dumps(state))
    before, runtime_before = snapshot(source), snapshot(runtime)

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Refusal must precede any executor, control or grading call')

    out = tmp_path / 'refused'
    with pytest.raises(ValueError):
        continue_day2.continue_day2(root, source, out, execute=forbidden,
                                    version='different' if case == 'wrong_version' else VERSION)
    assert not out.exists()
    assert snapshot(source) == before and snapshot(runtime) == runtime_before


def test_day2_access_to_original_runtime_is_detected(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                   tmp_path: Path) -> None:
    root, source, executor = stopped
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    old_runtime = Path(entry['runtime'])
    execute = continuation_executor(executor, old_runtime)

    def access(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = execute(argv, **kwargs)
        if argv[0] == 'codex':
            events = kwargs['stdout'].read_text().splitlines()
            events.insert(1, json.dumps({'type': 'item.completed', 'item': {
                'type': 'command_execution', 'command': 'cat ' + str(old_runtime / 'workspace/chunking.py')}}))
            kwargs['stdout'].write_text('\n'.join(events) + '\n')
        return result

    report = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'access', execute=access,
                                                   version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None
    assert task['grader_access_audit']['status'] == 'access_detected'
    assert executor.grades == 0


def test_cli_stdout_and_sanitized_errors(monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr('sys.argv', ['continue-day2', '--private-root', '/synthetic-secret',
                                    '--from', 'source', '--out', 'new'])
    monkeypatch.setattr(continue_day2, 'continue_day2', lambda *args: Path('new/report.json'))
    assert continue_day2.main() == 0
    assert capsys.readouterr().out == 'new\n'

    def unavailable(*args: Any) -> Path:
        raise ValueError('/synthetic-secret')

    monkeypatch.setattr(continue_day2, 'continue_day2', unavailable)
    assert continue_day2.main() == 1
    captured = capsys.readouterr()
    assert not captured.out and 'synthetic-secret' not in captured.err


@pytest.mark.parametrize('population', [False, True])
def test_other_tasks_regraded_once_and_accounting_reused(setup: tuple[Path, Path, Path],
                                                        monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                        population: bool) -> None:
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=False,
                                          include_other=True, population=population)
    state = json.loads((source / 'checkpoint.json').read_text())
    old_report = json.loads((source / 'report.json').read_text())
    snapshots = {t: snapshot(Path(e['runtime'])) for t, e in state['tasks'].items()}
    old_task = next(t for t in old_report['tasks'] if t['task_id'] == 'second-task')
    old_runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    base = continuation_executor(executor, old_runtime)
    grades = []

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if '-I' in argv:
            grades.append(kwargs['cwd'])
            if executor.calls == 1:
                return run_process(argv, **kwargs)
        return base(argv, **kwargs)

    report = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'continued',
                                                   execute=execute, version=VERSION).read_text())
    assert len(grades) == len(set(grades)) == 2
    new_task = next(t for t in report['tasks'] if t['task_id'] == 'second-task')
    assert new_task['outcome'] == 'pass' and new_task['grading']['copy_path'] != old_task['grading']['copy_path']
    for key in ('calls', 'costs', 'done_claims'):
        assert new_task[key] == old_task[key]
    assert report['accounting']['total_cost_usd'] == pytest.approx(old_report['accounting']['total_cost_usd'] + .0001105)
    for task, entry in state['tasks'].items():
        assert snapshot(Path(entry['runtime'])) == snapshots[task]


def test_population_hash_includes_unselected_inputs(setup: tuple[Path, Path, Path],
                                                    monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=False, population=True)
    old_runtime = Path(json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['runtime'])
    report = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'continued',
                        execute=continuation_executor(executor, old_runtime), version=VERSION).read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert report['metadata']['task_set_sha256'] == json.loads((source / 'report.json').read_text())['metadata']['task_set_sha256']


def test_known_control_costs_include_only_added_calls(setup: tuple[Path, Path, Path],
                                                     monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from tests.eval.test_control_accounting import generation
    original_invoke = core.harness._invoke_once

    def accounted(*args: Any, **kwargs: Any) -> Any:
        execute = kwargs['execute']

        def with_usage(argv: list[str], **options: Any) -> ProcessResult:
            result = execute(argv, **options)
            if argv[argv.index('-m') + 2] in {'contract', 'handoff'}:
                options['stderr'].write_text(generation())
            return result

        return original_invoke(*args, **dict(kwargs, execute=with_usage))

    monkeypatch.setattr(core.harness, '_invoke_once', accounted)
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=True)
    old = json.loads((source / 'report.json').read_text())['tasks'][0]
    old_runtime = Path(json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['runtime'])
    report = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'continued',
                        execute=continuation_executor(executor, old_runtime), version=VERSION).read_text())
    task = report['tasks'][0]
    assert old['costs']['control_usd'] == pytest.approx(.000132)
    assert task['costs']['control_usd'] == pytest.approx(3 * .000132)
    assert task['costs']['total_usd'] == pytest.approx(2 * .0001105 + 3 * .000132)
    assert [c for c in task['calls'] if c['purpose'] != 'executor'][:1] == old['calls'][1:]
    assert len({c['call_id'] for c in task['calls']}) == len(task['calls'])


def test_copy_hash_is_checked_before_executor(stopped: tuple[Path, Path, TwoSessionExecutor],
                                             monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, source, _ = stopped
    state = json.loads((source / 'checkpoint.json').read_text())
    runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    before = snapshot(runtime)
    original_copy = continue_day2.shutil.copytree

    def damaged_copy(src: Path, destination: Path, **kwargs: Any) -> Path:
        result = original_copy(src, destination, **kwargs)
        if Path(destination).name == 'workspace' and Path(destination).parent.name.startswith('lhm-eval-continue-'):
            (Path(destination) / 'chunking.py').write_text('bad copy')
        return result

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Copy verification must precede all new calls')

    monkeypatch.setattr(continue_day2.shutil, 'copytree', damaged_copy)
    with pytest.raises(ValueError, match='copied day-1 workspace exit hash mismatch'):
        continue_day2.continue_day2(root, source, tmp_path / 'damaged', execute=forbidden, version=VERSION)
    assert snapshot(runtime) == before


def test_changed_historical_log_during_day2_prevents_grading(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                          tmp_path: Path) -> None:
    root, source, executor = stopped
    old_runtime = Path(json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['runtime'])
    before = snapshot(old_runtime)
    execute = continuation_executor(executor, old_runtime)

    def tamper(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = execute(argv, **kwargs)
        if argv[0] == 'codex':
            path = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-day-1.jsonl'
            path.write_text(path.read_text() + json.dumps({'type': 'event_msg', 'payload': {'type': 'task_complete'}}) + '\n')
        return result

    report = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'changed', execute=tamper,
                                                   version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None and executor.grades == 0
    assert task['grader_access_audit']['status'] == 'inconclusive'
    assert 'retained_context_log_hash_mismatch' in task['grader_access_audit']['reason']
    assert snapshot(old_runtime) == before


def test_workspace_external_link_refused_without_copying_source(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                               tmp_path: Path) -> None:
    root, source, _ = stopped
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    (runtime / 'workspace/outside-link').symlink_to(runtime / 'exec-1.jsonl')
    before = snapshot(runtime)
    private = continue_day2.PrivateGraders.load(root, 'bug-chunk-tail', core.REPOSITORY)
    with pytest.raises(ValueError, match='external symlink'):
        continue_day2.copy_runtime(entry, private)
    assert snapshot(runtime) == before


def test_version_change_before_day2_keeps_fresh_incomplete_state(stopped: tuple[Path, Path, TwoSessionExecutor],
                                                               tmp_path: Path) -> None:
    root, source, executor = stopped
    runtime = Path(json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['runtime'])
    before = snapshot(runtime)
    versions = iter([VERSION, VERSION, 'codex-cli changed'])
    out = tmp_path / 'version-changed'
    with pytest.raises(core.IncompleteRun, match='version changed'):
        continue_day2.continue_day2(root, source, out, execute=continuation_executor(executor, runtime),
                                    version=lambda: next(versions))
    assert executor.calls == 1 and executor.grades == 0
    assert json.loads((out / 'continuation.json').read_text())['status'] == 'incomplete'
    assert snapshot(runtime) == before
