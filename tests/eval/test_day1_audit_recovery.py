"""Recover the missed final verifier call using synthetic post-exit evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import continue_day2, core, reaudit, regrade
from eval.runner.audit import PrivateGraders, audit_logs, digest, valid_native_metadata
from eval.runner.process import ProcessResult
from tests.eval.test_access_audit import private
from tests.eval.test_continue_day2 import VERSION, continuation_executor, snapshot
from tests.eval.test_runner import Executor, TwoSessionExecutor, setup, two_session_config

FIXTURE = Path(__file__).parent / 'fixtures/runtime-records/v2-job-queues-two-session.jsonl'
FIXTURE_SHA256 = 'dce27110dd0a9df8ba609b737e06190bf3dbbc25fee057a572bd461b65c6bd0e'


def sleep_record() -> dict[str, Any]:
    """Load the exact supplied native record without rewriting the fixture."""
    assert digest(FIXTURE.read_bytes()) == FIXTURE_SHA256
    return json.loads(FIXTURE.read_text())


@pytest.mark.parametrize('case', ['observed', 'unknown', 'missing_kind', 'duration_bool',
                                  'negative_duration', 'extra_input', 'missing_id', 'bad_time', 'started'])
def test_extension_kinds_fail_closed(tmp_path: Path, private: PrivateGraders, case: str) -> None:
    event = sleep_record()
    payload = event['payload']
    if case == 'unknown':
        payload['item']['kind'] = 'unknown.synthetic'
    elif case == 'missing_kind':
        payload['item'].pop('kind')
    elif case == 'duration_bool':
        payload['item']['durationMs'] = True
    elif case == 'negative_duration':
        payload['item']['durationMs'] = -1
    elif case == 'extra_input':
        payload['item']['input'] = 'cat secret'
    elif case == 'missing_id':
        payload['item'].pop('id')
    elif case == 'bad_time':
        payload['completed_at_ms'] = payload['started_at_ms'] - 1
    elif case == 'started':
        payload['type'] = 'item_started'
    assert valid_native_metadata('clock.sleep', payload) is (case in {'observed', 'started'})
    path = tmp_path / 'native.jsonl'
    path.write_text(json.dumps(event) + '\n')
    audit = audit_logs([path], private, workspace=tmp_path / 'workspace')
    assert audit['status'] == ('clean' if case in {'observed', 'started'} else 'inconclusive')
    if case in {'unknown', 'missing_kind'}:
        assert audit['errors'] == [f"unsupported_native_item:native.jsonl:1:{payload['item'].get('kind')}"]


class ThirdAttemptExecutor(TwoSessionExecutor):
    """Use existing mock protocols, with two failed day-1 verdicts before sleep."""

    def __init__(self, *, unknown: bool = False) -> None:
        super().__init__()
        self.day1_calls = 0
        self.unknown = unknown
        self.recovered_attempts: list[int] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex' and self.day1_calls < 3:
            self.day1_calls += 1
            self.calls = 0  # Reuse the mock's day-1 emission for each resume.
            result = super().__call__(argv[:2] + [v for v in argv[2:] if v != 'resume'], **kwargs)
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-day-1.jsonl'
            if self.day1_calls == 3:
                with (kwargs['cwd'] / 'chunking.py').open('a') as stream:
                    stream.write('\n# Final day-one attempt\n')
                event = sleep_record()
                if self.unknown:
                    event['payload']['item']['kind'] = 'unknown.synthetic'
                with native.open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
            native.rename(native.with_name(f'rollout-attempt-{self.day1_calls}.jsonl'))
            return result
        result = super().__call__(argv, **kwargs)
        if '--attempt' in argv:
            attempt = int(argv[argv.index('--attempt') + 1])
            destination = Path(argv[argv.index('--out') + 1])
            value = json.loads(destination.read_text())
            value['attempt'] = attempt
            if self.calls == 1 and attempt < 3:
                value.update(overall='fail', reinstruct_message='Finish the task')
                value['items'][0]['status'] = 'fail'
            if self.calls == 1 and attempt == 3:
                assert self.day1_calls == 3
                self.recovered_attempts.append(attempt)
                assert 'clock.sleep' in Path(argv[argv.index('--transcript') + 1]).read_text()
            destination.write_text(json.dumps(value))
        return result


def blocked_third(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                  tmp_path: Path, *, unknown: bool = False, missing_hash: bool = True
                  ) -> tuple[Path, Path, ThirdAttemptExecutor]:
    root, config, source = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    value = json.loads(config.read_text())
    value['reinstruction_limit'] = 2
    config.write_text(json.dumps(value))
    executor = ThirdAttemptExecutor(unknown=unknown)
    original = core.audit_logs

    def old_parser(*args: Any, **kwargs: Any) -> dict[str, Any]:
        audit = original(*args, **kwargs)
        for path in args[0]:
            if path.exists() and 'clock.sleep' in path.read_text():
                audit['errors'].append('unsupported_native_item:' + path.name + ':4')
                audit['status'] = 'inconclusive'
        return audit

    with monkeypatch.context() as historical:
        historical.setattr(core, 'audit_logs', old_parser)
        report = json.loads(core.run(config, source, root, execute=executor, version=VERSION).read_text())
    assert set(report['tasks'][0]['invalid_reasons']) == continue_day2.RECOVERABLE
    checkpoint = source / 'checkpoint.json'
    state = json.loads(checkpoint.read_text())
    entry = state['tasks']['bug-chunk-tail']
    assert executor.day1_calls == 3 and executor.grades == 0
    assert [v['attempt'] for v in entry['verdicts_day1']] == [1, 2]
    assert not (Path(entry['runtime']) / 'handoff.json').exists()
    if missing_hash:
        # Historical runner stopped before recording the third attempt's hash.
        entry['segments'][-1].pop('workspace_exit_sha256')
        entry['segments'][-1].pop('workspace_digest_version')
        entry['workspace_exit_sha256'] = entry['segments'][-2]['workspace_exit_sha256']
        entry['result']['segments'] = copy.deepcopy(entry['segments'])
        checkpoint.write_text(json.dumps(state))
    return root, source, executor


@pytest.mark.parametrize('missing_hash', [True, False])
def test_blocked_third_attempt_verifies_then_handoffs_and_grades_day2(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        missing_hash: bool) -> None:
    root, source, executor = blocked_third(setup, monkeypatch, tmp_path, missing_hash=missing_hash)
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    before, old_runtime = snapshot(source), snapshot(runtime)
    assert reaudit.reaudit(root, source)[0]['status'] == 'clean'
    out = tmp_path / 'continued'
    report = json.loads(continue_day2.continue_day2(root, source, out,
                        execute=continuation_executor(executor, runtime), version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['attempts'] == 4
    assert task['grader_access_audit']['status'] == 'clean'
    assert task['handoff']['day2_pass'] and executor.grades == 1
    assert executor.day1_calls == 3 and executor.recovered_attempts == [3]
    assert executor.operations == ['contract', 'check', 'check', 'check', 'handoff',
                                   'validate-handoff', 'contract', 'check']
    result = json.loads((out / 'bug-chunk-tail/result.json').read_text())
    recovery = result['day1_verification_recovery']
    assert recovery['attempt'] == 3 and recovery['verification_after_exit'] is True
    assert recovery['historical_exit_hash_available'] is (not missing_hash)
    assert recovery['executor_exited_at'] <= recovery['snapshot_recorded_at'] <= recovery['verified_at']
    assert recovery['recovery_workspace_sha256'] == core.workspace_digest(runtime / 'workspace')
    provenance = json.loads((out / 'bug-chunk-tail/continuation.json').read_text())
    assert provenance['day1_verification_recovery'] == recovery
    assert snapshot(source) == before and snapshot(runtime) == old_runtime
    assert reaudit.reaudit(root, out)[0]['status'] == 'clean'
    repeated = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=executor).read_text())
    assert repeated['tasks'][0]['outcome'] == 'pass'
    assert repeated['tasks'][0]['calls'] == task['calls']


def test_blocked_third_attempt_still_unsupported_is_refused(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, source, _ = blocked_third(setup, monkeypatch, tmp_path, unknown=True)
    before = snapshot(source)

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('No calls before a clean re-audit')

    out = tmp_path / 'refused'
    assert reaudit.reaudit(root, source)[0]['status'] == 'inconclusive'
    with pytest.raises(ValueError, match='no audit-recoverable'):
        continue_day2.continue_day2(root, source, out, execute=forbidden, version=VERSION)
    assert not out.exists() and snapshot(source) == before


def test_missing_exit_hash_does_not_enable_nonharness_recovery(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from tests.eval.test_continue_day2 import make_stopped
    root, source, _ = make_stopped(setup, monkeypatch, tmp_path, harness_on=False)
    state = json.loads((source / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    entry['segments'][-1].pop('workspace_exit_sha256')
    entry['result']['segments'] = copy.deepcopy(entry['segments'])
    assert not continue_day2.eligible(json.loads((source / 'report.json').read_text())['tasks'][0],
                                      entry, state['config'])


@pytest.mark.parametrize('record', [1, 2, 'v2-rate-budgets-bug-fix',
                                   'v2-layered-settings-multiple-requirements',
                                   'v2-workflow-state-feature-plus-test',
                                   'v2-workflow-state-constrained-refactoring'])
def test_reaudit_and_regrade_keep_resolved_records_clean(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        record: int | str) -> None:
    """Historical unresolved errors never override current concrete resolutions."""
    from tests.eval.test_derived_inputs import stored
    from tests.eval.test_runtime_records import records
    root, config, source = setup
    executor = Executor()
    original = core.audit_logs
    rows: list[dict[str, Any]] = []
    if isinstance(record, int):
        scripts = [(stored(), ''), ((FIXTURE.parents[1] / f'derived-record-{record}.js').read_text(), '')]
        for index, (script, output) in enumerate(scripts):
            rows.extend([{'type': 'response_item', 'payload': {'type': 'custom_tool_call',
                         'name': 'exec', 'call_id': f'call-{index}', 'input': script}},
                         {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
                          'call_id': f'call-{index}', 'output': output}}])
    else:
        rows = records(record)

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
            with native.open('a') as stream:
                stream.write(''.join(json.dumps(row) + '\n' for row in rows))
        return result

    def historical(*args: Any, **kwargs: Any) -> dict[str, Any]:
        audit = original(*args, **kwargs)
        if audit['resolutions']:
            audit['errors'].append('unresolved_custom_input:historical')
            audit['status'] = 'inconclusive'
        return audit

    with monkeypatch.context() as old:
        old.setattr(core, 'audit_logs', historical)
        report = json.loads(core.run(config, source, root, execute=execute, version=VERSION).read_text())
    assert report['tasks'][0]['invalid_reasons'] == ['incomplete_access_audit']
    before = snapshot(source)
    assert reaudit.reaudit(root, source)[0]['status'] == 'clean'
    out = tmp_path / 'regraded'
    report = json.loads(regrade.regrade(root, source, out, execute=executor).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['grader_access_audit']['status'] == 'clean'
    audit = json.loads((out / 'bug-chunk-tail/access-audit.json').read_text())
    assert audit['resolutions'] and not audit['errors'] and not audit['matches']
    assert snapshot(source) == before
