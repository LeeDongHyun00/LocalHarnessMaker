"""Offline regressions for aliased temp roots and legacy workspace recovery."""

import copy
import json
import os
from pathlib import Path
import shlex
import shutil
from typing import Any

import pytest

from eval.runner import continue_day2, core, reaudit, regrade, rerun_invalid
from eval.runner.audit import PrivateGraders, audit_logs, audit_retained_logs, command_operands, digest
from eval.runner.process import ProcessResult, run_process
from eval.runner.workspace_verification import exit_time_ns, verify
from tests.eval.test_access_audit import private, audit_loop_record, LOOP_RECORDS, thread_settings_event
from tests.eval.test_continue_day2 import stopped, continuation_executor
from tests.eval.test_reaudit import finished
from tests.eval.test_restart_recovery import infrastructure_source
from tests.eval.test_runner import Executor, HarnessExecutor, harness_config, setup
from tests.eval.test_workspace_digest import add_caches

VERSION = 'codex-cli 0.162.0-alpha.17.2'


@pytest.mark.parametrize('form', LOOP_RECORDS)
@pytest.mark.parametrize('case', ['literal', 'private', 'alias', 'traversal', 'variable', 'glob', 'substitution'])
def test_absolute_literal_loop_and_following_newline(
        tmp_path: Path, private: PrivateGraders, form: str, case: str) -> None:
    workspace = tmp_path / 'runtime/workspace'
    workspace.mkdir(parents=True)
    alias = tmp_path / 'alias'
    alias.symlink_to(private.root)
    paths = ['/AGENTS.md', '/private/AGENTS.md', '/private/var/AGENTS.md',
             '/private/var/folders/AGENTS.md', '/private/var/folders/XX/AGENTS.md',
             '/private/var/folders/XX/YYYY/AGENTS.md', '/private/var/folders/XX/YYYY/T/AGENTS.md',
             '/private/var/folders/XX/YYYY/T/lhm-eval-ZZZZ/AGENTS.md', 'AGENTS.md', 'project/AGENTS.md']
    extra = {'literal': '', 'private': str(private.root / 'probe'), 'alias': str(alias / 'probe'),
             'traversal': str(tmp_path / 'ordinary/../trusted-storage/probe'),
             'variable': '$EXTRA', 'glob': '/somewhere/*', 'substitution': '$(printf /AGENTS.md)'}[case]
    body = 'for path in ' + ' '.join(paths + ([extra] if extra else []))
    body += '; do if [ -f "$path" ]; then cat "$path"; fi; done\n'
    body += 'shasum -a 256 README.md project/compat.py test_public.py verify.py'
    command = '/bin/zsh -lc ' + shlex.quote(body)
    result = audit_loop_record(tmp_path, private, command, workspace, form)
    expected = ('access_detected' if case in {'private', 'alias', 'traversal'} else
                'inconclusive' if case in {'variable', 'glob', 'substitution'} else 'clean')
    assert result['status'] == expected, result
    if case == 'literal':
        operands, unresolved = command_operands(command, workspace, workspace=workspace)
        assert not unresolved
        for value in paths:
            path = Path(value) if Path(value).is_absolute() else workspace / value
            assert operands.count((path.resolve(), False)) == 2
        assert (workspace / 'project/compat.py', False) in operands
        assert result['errors'] == result['matches'] == []
    elif expected == 'access_detected':
        assert any(match['marker'] == 'protected_path' for match in result['matches'])
    else:
        assert any(error.startswith('unresolved_operand:') for error in result['errors'])


def temp_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    real = tmp_path / 'real-temp'
    real.mkdir()
    alias = tmp_path / 'temp-alias'
    alias.symlink_to(real, target_is_directory=True)
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(alias))
    return real, alias


def test_resolved_audit_roots_and_reaudit_clear_self_context(
        finished: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, out, old = finished
    real, alias = temp_alias(tmp_path, monkeypatch)
    runtime = real / 'lhm-eval-continue-self'
    old.rename(runtime)
    sibling = alias / 'lhm-eval-sibling'
    (sibling / 'workspace').mkdir(parents=True)
    (runtime / 'grading-old').mkdir()
    roots = core.audit_roots(runtime)
    assert roots == core.audit_roots(alias / runtime.name)
    assert runtime.resolve() not in roots
    assert sibling.resolve() in roots and (runtime / 'grading-old').resolve() in roots
    log = runtime / 'exec-1.jsonl'
    settings = thread_settings_event()
    settings['payload']['synthetic_extra'] = str(runtime / 'workspace')
    records = [{'type': 'item.completed', 'item': {'type': 'command_execution',
                'command': 'cat ' + str(alias / runtime.name / 'workspace/source.py')}},
               {'type': 'world_state', 'payload': {'full': True, 'state': {'cwd': str(runtime / 'workspace')}}},
               settings, {'type': 'turn.completed'}]
    log.write_text(''.join(json.dumps(row) + '\n' for row in records))
    private = PrivateGraders.load(root, 'unit-task', core.REPOSITORY)
    paths = [log, *sorted((runtime / 'codex-home/sessions').rglob('*.jsonl'))]
    audit = audit_logs(paths, private, workspace=runtime / 'workspace', repository=core.REPOSITORY,
                       grading_roots=roots)
    assert audit['status'] == 'clean', audit
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['unit-task']
    entry['runtime'] = str(runtime)
    entry['result']['grader_access_audit'] = audit
    core.write_json(out / 'checkpoint.json', state)
    assert reaudit.reaudit(root, out)[0]['status'] == 'clean'
    # Old continuations may have persisted their own aliased root as protected.
    context = {'runtime': str(runtime), 'workspace': str(runtime / 'workspace'),
               'copied_runtime': str(runtime), 'workspace_exit_sha256': core.workspace_digest(runtime / 'workspace'),
               'grading_roots': [str(alias / runtime.name), *map(str, roots)],
               'logs': {str(path): digest(path.read_bytes()) for path in paths}}
    assert audit_retained_logs(paths, private, retained_context=context,
        workspace=runtime / 'workspace', repository=core.REPOSITORY, grading_roots=roots)['status'] == 'clean'
    for target in (sibling / 'workspace/source.py', runtime / 'grading-old/probe'):
        log.write_text(json.dumps({'type': 'item.completed', 'item': {
            'type': 'command_execution', 'command': 'cat ' + str(target)}}) + '\n{"type":"turn.completed"}\n')
        assert audit_logs([log], private, workspace=runtime / 'workspace',
            repository=core.REPOSITORY, grading_roots=roots)['status'] == 'access_detected'


def legacy_workspace(source: Path, *, explicit: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retain synthetic run-time publication pins, then rewrite caches after exit."""
    state = json.loads((source / 'checkpoint.json').read_text())
    report = json.loads((source / 'report.json').read_text())
    for task in report['tasks']:
        entry = state['tasks'][task['task_id']]
        workspace = Path(entry['runtime']) / 'workspace'
        add_caches(workspace)
        cutoff = exit_time_ns(entry, task) - 1_000_000_000
        for path in workspace.rglob('*'):
            if path.is_file():
                os.utime(path, ns=(cutoff, cutoff))
        published = source / task['task_id'] / 'workspace'
        if not published.exists():
            shutil.copytree(workspace, published, ignore=core.WORKSPACE_COPY_IGNORE)
        task['artifacts'].extend({'path': str(p), 'sha256': digest(p.read_bytes())}
                                 for p in sorted(published.rglob('*')) if p.is_file())
        for record in (entry, entry['segments'][-1]):
            record['workspace_exit_sha256'] = core.workspace_digest(workspace, 1)
            record.pop('workspace_digest_version', None)
            if explicit:
                record['workspace_digest_version'] = 1
        entry['result']['segments'] = copy.deepcopy(entry['segments'])
        (workspace / '__pycache__/solution.cpython-313.pyc').write_bytes(b'rewritten after exit')
        assert core.matching_workspace_digest_version(workspace, entry) is None
    core.write_json(source / 'checkpoint.json', state)
    core.write_json(source / 'report.json', report)
    return state, report


def change_legacy(source: Path, case: str) -> None:
    state = json.loads((source / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    workspace = Path(entry['runtime']) / 'workspace'
    if case == 'modified':
        source_file = workspace / 'chunking.py'
        retained_mtime = source_file.stat().st_mtime_ns
        source_file.write_text('modified source')
        # A bounded timestamp cannot waive a published content-hash mismatch.
        os.utime(source_file, ns=(retained_mtime, retained_mtime))
    elif case == 'missing_artifacts':
        report = json.loads((source / 'report.json').read_text())
        for task in report['tasks']:
            task['artifacts'] = [ref for ref in task['artifacts'] if '/workspace/' not in ref['path']]
        core.write_json(source / 'report.json', report)
    elif case == 'late_mtime':
        cutoff = exit_time_ns(entry, next(t for t in json.loads((source / 'report.json').read_text())['tasks']
                                        if t['task_id'] == 'bug-chunk-tail'))
        os.utime(workspace / 'chunking.py', ns=(cutoff + 1, cutoff + 1))
    elif case == 'extra_file':
        (workspace / 'extra.txt').write_text('extra')
    elif case == 'missing_file':
        # Move instead of deleting: project rules forbid file deletion.
        (workspace / 'chunking.py').rename(workspace.parent / 'removed-source')


@pytest.mark.parametrize('explicit', [False, True])
@pytest.mark.parametrize('case', ['unchanged', 'modified', 'missing_artifacts', 'late_mtime', 'extra_file', 'missing_file'])
def test_harness_legacy_regrade_requires_all_published_hashes_and_bounded_mtimes(
        setup: tuple[Path, Path, Path], tmp_path: Path, explicit: bool, case: str) -> None:
    root, config, source = setup
    harness_config(config)
    core.run(config, source, root, execute=HarnessExecutor(), version=VERSION)
    state, _ = legacy_workspace(source, explicit=explicit)
    change_legacy(source, case)
    before = (source / 'checkpoint.json').read_bytes()
    out = tmp_path / 'regraded'
    if case != 'unchanged':
        def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
            pytest.fail('Refusal must precede all calls')
        with pytest.raises(ValueError, match='hash mismatch'):
            regrade.regrade(root, source, out, execute=forbidden)
        assert not out.exists()
    else:
        assert reaudit.reaudit(root, source)[0]['status'] == 'clean'
        report = json.loads(regrade.regrade(root, source, out).read_text())
        assert report['tasks'][0]['outcome'] == 'pass'
        provenance = json.loads((out / 'bug-chunk-tail/regrade-provenance.json').read_text())
        assert provenance['workspace_verification'] == 'published_artifact_hashes'
        assert provenance['hashes_compared'] == provenance['mtimes_checked'] > 0
        assert provenance['published_file_count'] == provenance['workspace_file_count']
        checks = json.loads((out / 'run-diagnostics.json').read_text())['workspace_hash_checks']
        assert checks[0]['workspace_verification'] == 'published_artifact_hashes'
        assert checks[0]['observed_sha256'] is None
        assert any(Path(ref['path']).name == 'regrade-provenance.json' for ref in report['tasks'][0]['artifacts'])
        assert json.loads(regrade.regrade(root, out, tmp_path / 'again').read_text())['tasks'][0]['outcome'] == 'pass'
        assert json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['workspace_exit_sha256'] == state['tasks']['bug-chunk-tail']['workspace_exit_sha256']
    assert (source / 'checkpoint.json').read_bytes() == before


@pytest.mark.parametrize('case', ['unchanged', 'modified', 'missing_artifacts'])
def test_rerun_invalid_legacy_verification(
        setup: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    legacy_workspace(source)
    change_legacy(source, case)
    executor = Executor()

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert case == 'unchanged', 'Refusal must precede all calls'
        return executor(argv, **kwargs) if argv[0] == 'codex' else run_process(argv, **kwargs)

    out = tmp_path / 'rerun'
    if case != 'unchanged':
        with pytest.raises(ValueError, match='hash mismatch'):
            rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'}, execute=execute, version=VERSION)
        assert not out.exists()
    else:
        report = json.loads(rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'},
                                                      execute=execute, version=VERSION).read_text())
        assert executor.calls == 1 and all(task['outcome'] == 'pass' for task in report['tasks'])
        evidence = json.loads((out / 'bug-chunk-tail/rerun-provenance.json').read_text())
        assert evidence['workspace_verification'] == 'published_artifact_hashes'
        assert evidence['hashes_compared'] == evidence['mtimes_checked'] > 0


@pytest.mark.parametrize('case', ['unchanged', 'modified', 'missing_artifacts'])
def test_day2_legacy_verification_and_aliased_continuation(
        stopped: tuple[Path, Path, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    root, source, executor = stopped
    state, _ = legacy_workspace(source)
    change_legacy(source, case)
    old_runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    real, alias = temp_alias(tmp_path, monkeypatch)
    base = continuation_executor(executor, old_runtime)

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert case == 'unchanged', 'Refusal must precede all calls'
        result = base(argv, **kwargs)
        if argv[0] == 'codex':
            runtime = kwargs['cwd'].parent
            assert runtime.parent == real.resolve()
            native = runtime / 'codex-home/sessions/rollout-day-2.jsonl'
            settings = thread_settings_event()
            settings['payload']['synthetic_extra'] = str(alias / runtime.name / 'workspace')
            rows = [{'type': 'event_msg', 'payload': {'type': 'item_completed', 'item': {
                'type': 'CommandExecution', 'command': ['cat', str(runtime / 'workspace/chunking.py')]}}},
                {'type': 'world_state', 'payload': {'full': True, 'state': {'cwd': str(runtime / 'workspace')}}}, settings]
            with native.open('a') as stream:
                stream.write(''.join(json.dumps(row) + '\n' for row in rows))
        return result

    out = tmp_path / 'continued'
    if case != 'unchanged':
        with pytest.raises(ValueError):
            continue_day2.continue_day2(root, source, out, execute=execute, version=VERSION)
        assert not out.exists()
    else:
        report = json.loads(continue_day2.continue_day2(root, source, out, execute=execute, version=VERSION).read_text())
        assert report['tasks'][0]['outcome'] == 'pass'
        evidence = json.loads((out / 'bug-chunk-tail/continuation.json').read_text())
        assert evidence['workspace_verification'] == 'published_artifact_hashes'
        assert evidence['hashes_compared'] == evidence['mtimes_checked'] > 0
        assert evidence['copy_hash_matched'] is False
        assert evidence['copied_workspace_sha256'] != evidence['day1_workspace_exit_sha256']
        assert evidence['copied_workspace_digest_version'] == 2
        assert reaudit.reaudit(root, out)[0]['status'] == 'clean'
        assert json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=executor).read_text())['tasks'][0]['outcome'] == 'pass'


@pytest.mark.parametrize('case', ['unknown_version', 'v2', 'duplicate', 'bad_hash', 'symlink', 'conflicting_exits', 'naive_exit'])
def test_artifact_fallback_stays_fail_closed(setup: tuple[Path, Path, Path], case: str) -> None:
    root, config, source = setup
    core.run(config, source, root, execute=Executor(), version=VERSION)
    state, report = legacy_workspace(source)
    entry, task = state['tasks']['bug-chunk-tail'], report['tasks'][0]
    workspace = Path(entry['runtime']) / 'workspace'
    if case in {'unknown_version', 'v2'}:
        entry['workspace_digest_version'] = 3 if case == 'unknown_version' else 2
    elif case == 'duplicate':
        task['artifacts'].append(copy.deepcopy(task['artifacts'][-1]))
    elif case == 'bad_hash':
        task['artifacts'][-1]['sha256'] = 'invalid'
    elif case == 'symlink':
        (workspace / 'linked-source').symlink_to('chunking.py')
    elif case == 'conflicting_exits':
        entry['segments'][-1]['exited_at'] = '2099-01-01T00:00:00+00:00'
    else:
        entry['segments'][-1]['exited_at'] = task['executor_segments'][-1]['exited_at'] = '2026-10-23T00:00:00'
    assert verify(workspace, entry, task) is None
