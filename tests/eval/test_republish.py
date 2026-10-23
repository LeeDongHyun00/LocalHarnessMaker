"""Offline publication recovery with explicit macOS-style ancestor aliases."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from eval.runner import core, harness, republish
from eval.runner.audit import PrivateGraders, digest
from eval.runner.publication import safe_source
from tests.eval.test_reaudit import schema_report

REPOSITORY = core.REPOSITORY


@pytest.fixture
def finished(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    repository = tmp_path / 'repository'
    shutil.copytree(REPOSITORY / 'schemas', repository / 'schemas')
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    private_root = tmp_path / 'private'
    (private_root / 'unit-task').mkdir(parents=True)
    (private_root / 'unit-task/test_synthetic.py').write_text('assert synthetic == 123456789\n')
    real = tmp_path / 'real-parent'
    real.mkdir()
    alias = tmp_path / 'alias-parent'
    alias.symlink_to(real, target_is_directory=True)
    runtime = alias / 'runtime'
    (runtime / 'workspace').mkdir(parents=True)
    (runtime / 'workspace/contract.json').write_text('executor forgery')
    (runtime / 'workspace/private.py').write_text('must never copy')
    native = runtime / 'codex-home/sessions/native.jsonl'
    native.parent.mkdir(parents=True)
    native.write_text('{"type":"session_meta"}\n')
    files = {'exec-1.jsonl': '{"type":"turn.completed"}\n', 'exec-1.stderr': 'stderr\n',
             'final-1.md': 'Done.\n', 'contract.json': '{}\n',
             'contract.stdout': str(runtime / 'contract.json') + '\n',
             'contract.stderr': str(private_root) + '\n', 'contract.control.json': '{}\n',
             'verdict-1.json': '{}\n', 'handoff.json': '{}\n',
             'day2/verdict-2.json': '{}\n', 'control-interruptions/one/day2/contract.stderr': 'archived\n',
             'transcript-1.jsonl': 'not on publication allowlist\n'}
    for name, data in files.items():
        path = runtime / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
    report = schema_report(['unit-task'])
    segment = {k: report['tasks'][0]['executor_segments'][0][k]
               for k in ('attempt', 'started_at', 'exited_at', 'exit_code')}
    segment.update(attempt=1, events='exec-1.jsonl', stderr='exec-1.stderr', native_logs=[str(native)],
                   evidence_sha256={name: digest((runtime / name).read_bytes())
                                    for name in ('exec-1.jsonl', 'exec-1.stderr', 'final-1.md')})
    logs = [{'name': path.name, 'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
            for path in (runtime / 'exec-1.jsonl', native)]
    controls = {name: digest((runtime / name).read_bytes()) for name in files
                if not name.startswith(('exec-', 'final-'))}
    entry = {'phase': 'finished', 'runtime': str(runtime), 'segments': [segment], 'control_files': controls,
             'result': {'segments': [deepcopy(segment)], 'grader_access_audit': {'logs': logs}}}
    out = repository / 'eval/reports/run'
    (out / 'unit-task').mkdir(parents=True)
    report['tasks'][0]['executor_segments'] = [{k: segment[k] for k in
        ('attempt', 'started_at', 'exited_at', 'exit_code')} | {
            'session_id': 'unit-session', 'events': {'path': str(runtime / 'exec-1.jsonl'),
                                                     'sha256': digest((runtime / 'exec-1.jsonl').read_bytes())}}]
    report['tasks'][0]['artifacts'] = [{'path': str(native), 'sha256': digest(native.read_bytes())}]
    state = {'report_schema': 'evaluation-report-v1', 'config': {'tasks': ['unit-task']},
             'tasks': {'unit-task': entry}, **{k: report['metadata'][k]
                                            for k in ('run_id', 'config_sha256', 'task_set_sha256')}}
    (out / 'checkpoint.json').write_text(json.dumps(state))
    (out / 'report.json').write_text(json.dumps(report))

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError('Republication must never call subprocesses')

    monkeypatch.setattr(core.subprocess, 'run', forbidden)
    monkeypatch.setattr(core, 'run_process', forbidden)
    return private_root, out, runtime


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_republish_redaction_artifacts_idempotence_and_only_artifacts_change(
        finished: tuple[Path, Path, Path]) -> None:
    private, out, runtime = finished
    checkpoint = (out / 'checkpoint.json').read_bytes()
    before = json.loads((out / 'report.json').read_text())
    source = snapshot(runtime)
    rows = republish.republish(private, out)
    assert rows == [{'task_id': 'unit-task', 'published': 11, 'existing': 0, 'unpinned': 0}]
    task_out = out / 'unit-task'
    assert (task_out / 'exec-1.stderr').read_text() == 'stderr\n'
    assert (task_out / 'final-1.md').read_text() == 'Done.\n'
    assert (task_out / 'day2-verdict-2.json').exists()
    assert (task_out / 'control-interruptions/one/day2/contract.stderr').exists()
    assert str(private) not in (task_out / 'contract.stderr').read_text()
    assert not (task_out / 'workspace').exists()
    assert not (task_out / 'transcript-1.jsonl').exists()
    after = json.loads((out / 'report.json').read_text())
    refs = after['tasks'][0]['artifacts']
    assert len(refs) == 12
    for ref in refs:
        path = Path(ref['path'])
        path = path if path.is_absolute() else core.REPOSITORY / path
        assert digest(path.read_bytes()) == ref['sha256']
    after['tasks'][0]['artifacts'] = before['tasks'][0]['artifacts']
    assert after == before
    assert (out / 'checkpoint.json').read_bytes() == checkpoint
    assert snapshot(runtime) == source
    published = snapshot(out)
    assert republish.republish(private, out) == [dict(rows[0], published=0, existing=11)]
    assert snapshot(out) == published


def test_republish_backup_without_original_runtime(finished: tuple[Path, Path, Path], tmp_path: Path) -> None:
    private, out, runtime = finished
    backup = tmp_path / 'backup'
    backup.mkdir()
    runtime.rename(backup / 'unit-task')
    assert republish.republish(private, out, backup)[0]['published'] == 11
    assert (out / 'unit-task/exec-1.jsonl').exists()


@pytest.mark.parametrize('case', ['control', 'events', 'native', 'stderr', 'final', 'audit_size',
    'missing_control', 'missing_native', 'extra_native', 'control_link', 'native_parent_link',
    'runtime_link', 'destination_link', 'existing_conflict', 'artifact_pin', 'segment_hash',
    'segment_metadata', 'checkpoint_segments', 'report_missing', 'checkpoint_missing',
    'running', 'pid', 'incomplete', 'provenance', 'workspace_pin', 'traversal_pin'])
def test_republish_refuses_before_writing(finished: tuple[Path, Path, Path], case: str, tmp_path: Path) -> None:
    private, out, runtime = finished
    state_path, report_path = out / 'checkpoint.json', out / 'report.json'
    state, report = json.loads(state_path.read_text()), json.loads(report_path.read_text())
    entry = state['tasks']['unit-task']
    if case in {'control', 'events', 'native', 'stderr', 'final'}:
        name = {'control': 'contract.json', 'events': 'exec-1.jsonl', 'native': 'codex-home/sessions/native.jsonl',
                'stderr': 'exec-1.stderr', 'final': 'final-1.md'}[case]
        (runtime / name).write_text('changed')
    elif case == 'audit_size':
        entry['result']['grader_access_audit']['logs'][0]['bytes'] += 1
    elif case.startswith('missing_'):
        name = 'contract.json' if case == 'missing_control' else 'codex-home/sessions/native.jsonl'
        (runtime / name).rename(tmp_path / 'missing')
    elif case == 'extra_native':
        (runtime / 'codex-home/sessions/extra.jsonl').write_text('{}\n')
    elif case == 'control_link':
        (runtime / 'contract.json').rename(tmp_path / 'moved')
        (runtime / 'contract.json').symlink_to(tmp_path / 'moved')
    elif case == 'native_parent_link':
        (runtime / 'codex-home').rename(tmp_path / 'moved')
        (runtime / 'codex-home').symlink_to(tmp_path / 'moved', target_is_directory=True)
    elif case == 'runtime_link':
        runtime.rename(tmp_path / 'moved')
        runtime.symlink_to(tmp_path / 'moved', target_is_directory=True)
    elif case == 'destination_link':
        (out / 'unit-task/day2-verdict-2.json').symlink_to(tmp_path / 'absent')
    elif case == 'existing_conflict':
        (out / 'unit-task/contract.json').write_text('conflict')
    elif case == 'artifact_pin':
        report['tasks'][0]['artifacts'].append({'path': str(out / 'unit-task/contract.json'), 'sha256': '0' * 64})
    elif case == 'segment_hash':
        report['tasks'][0]['executor_segments'][0]['events']['sha256'] = '0' * 64
    elif case == 'segment_metadata':
        report['tasks'][0]['executor_segments'][0]['exit_code'] = 42
    elif case == 'checkpoint_segments':
        entry['result']['segments'][0]['attempt'] = 2
    elif case == 'running':
        entry['phase'] = 'running'
    elif case == 'pid':
        entry['pid'] = 123
    elif case == 'incomplete':
        state['config']['tasks'].append('another-task')
    elif case == 'provenance':
        state['run_id'] = 'different'
    elif case in {'workspace_pin', 'traversal_pin'}:
        entry['control_files']['workspace/contract.json' if case == 'workspace_pin' else '../contract.json'] = '0' * 64
    state_path.write_text(json.dumps(state))
    report_path.write_text(json.dumps(report))
    if case in {'report_missing', 'checkpoint_missing'}:
        (report_path if case == 'report_missing' else state_path).rename(tmp_path / 'missing')
    before = snapshot(out)
    with pytest.raises((ValueError, OSError)):
        republish.republish(private, out)
    assert snapshot(out) == before


def test_historical_unpinned_executor_files_are_counted_and_not_adopted(
        finished: tuple[Path, Path, Path]) -> None:
    private, out, _ = finished
    path = out / 'checkpoint.json'
    state = json.loads(path.read_text())
    entry = state['tasks']['unit-task']
    entry['segments'][0].pop('evidence_sha256')
    entry['result']['segments'] = deepcopy(entry['segments'])
    path.write_text(json.dumps(state))
    assert republish.republish(private, out)[0] == {
        'task_id': 'unit-task', 'published': 9, 'existing': 0, 'unpinned': 2}
    assert not (out / 'unit-task/exec-1.stderr').exists()
    assert not (out / 'unit-task/final-1.md').exists()


def test_cli_counts_only(finished: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                         capsys: pytest.CaptureFixture[str]) -> None:
    private, out, _ = finished
    monkeypatch.setattr('sys.argv', ['republish', '--private-root', str(private), '--out', str(out)])
    assert republish.main() == 0
    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines()]
    assert rows[-1] == {'tasks': 1, 'published': 11, 'existing': 0, 'unpinned': 0}
    assert captured.err == ''
    assert str(private) not in captured.out and str(out) not in captured.out


def test_cli_error_does_not_leak_paths(finished: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                                      capsys: pytest.CaptureFixture[str]) -> None:
    private, out, _ = finished
    monkeypatch.setattr('sys.argv', ['republish', '--private-root', str(private), '--out', str(out / 'missing')])
    assert republish.main() == 1
    assert capsys.readouterr().err == 'Republication input error\n'


def test_publish_and_guard_accept_ancestor_alias_but_reject_inner_links(
        finished: tuple[Path, Path, Path], tmp_path: Path) -> None:
    private_root, _, runtime = finished
    private = PrivateGraders.load(private_root, 'unit-task', core.REPOSITORY)
    source = runtime / 'day2/verdict-2.json'
    destination = tmp_path / 'published.json'
    core.publish(source, destination, private, source_root=runtime)
    assert destination.read_text() == source.read_text()
    guard = harness.ControlFiles(runtime, {'day2/verdict-2.json': digest(source.read_bytes())}, lambda: None)
    guard.verify()
    assert not safe_source(runtime / '../outside', runtime)
    (runtime / 'day2').rename(runtime / 'real-day2')
    (runtime / 'day2').symlink_to(runtime / 'real-day2', target_is_directory=True)
    other = tmp_path / 'not-published.json'
    core.publish(source, other, private, source_root=runtime)
    assert not other.exists()
    with pytest.raises(harness.HarnessError):
        guard.verify()


def test_day2_copy_accepts_symlinked_runtime_ancestor(finished: tuple[Path, Path, Path],
                                                     monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from eval.runner.continue_day2 import copy_runtime
    private_root, out, runtime = finished
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['unit-task']
    entry['workspace_exit_sha256'] = core.workspace_digest(runtime / 'workspace')
    login = tmp_path / 'login'
    login.mkdir()
    (login / 'auth.json').write_text('{}')
    monkeypatch.setenv('CODEX_HOME', str(login))
    private = PrivateGraders.load(private_root, 'unit-task', core.REPOSITORY)
    copied = copy_runtime(entry, private)
    fresh = Path(copied['runtime'])
    assert fresh != runtime
    assert core.workspace_digest(fresh / 'workspace') == entry['workspace_exit_sha256']
    assert (fresh / 'day2/verdict-2.json').read_bytes() == (runtime / 'day2/verdict-2.json').read_bytes()
    assert (fresh / 'exec-1.jsonl').read_bytes() == (runtime / 'exec-1.jsonl').read_bytes()


def test_all_tasks_preflight_before_first_write(finished: tuple[Path, Path, Path]) -> None:
    private, out, _ = finished
    shutil.copytree(private / 'unit-task', private / 'second-task')
    state_path, report_path = out / 'checkpoint.json', out / 'report.json'
    state, report = json.loads(state_path.read_text()), json.loads(report_path.read_text())
    state['tasks']['second-task'] = deepcopy(state['tasks']['unit-task'])
    state['config']['tasks'].append('second-task')
    report['tasks'].append(dict(deepcopy(report['tasks'][0]), task_id='second-task'))
    (out / 'second-task').mkdir()
    (out / 'second-task/contract.json').write_text('late conflict')
    state_path.write_text(json.dumps(state))
    report_path.write_text(json.dumps(report))
    before = snapshot(out)
    with pytest.raises(ValueError):
        republish.republish(private, out)
    assert snapshot(out) == before


def test_static_templates_accept_parent_alias_and_reject_directory_link(tmp_path: Path) -> None:
    from eval.runner.static_templates import load_templates
    real = tmp_path / 'real'
    (real / 'templates').mkdir(parents=True)
    (real / 'templates/unit-task.md').write_text('Human guidance\n')
    alias = tmp_path / 'alias'
    alias.symlink_to(real, target_is_directory=True)
    config = {'tasks': ['unit-task'], 'static_template_dir': str(alias / 'templates')}
    assert load_templates(config, tmp_path) == {'unit-task': b'Human guidance\n'}
    (alias / 'templates').rename(real / 'moved')
    (alias / 'templates').symlink_to(real / 'moved', target_is_directory=True)
    with pytest.raises(ValueError):
        load_templates(config, tmp_path)


def test_v2_report_preserves_metrics_and_classification(finished: tuple[Path, Path, Path]) -> None:
    private, out, _ = finished
    path, checkpoint = out / 'report.json', out / 'checkpoint.json'
    report, state = json.loads(path.read_text()), json.loads(checkpoint.read_text())
    example = json.loads((REPOSITORY / 'schemas/examples/evaluation_report.json').read_text())
    report['metrics']['task_false_done_rate'] = example['metrics']['task_false_done_rate']
    state['report_schema'] = 'evaluation-report-v2'
    path.write_text(json.dumps(report))
    checkpoint.write_text(json.dumps(state))
    republish.republish(private, out)
    after = json.loads(path.read_text())
    assert after['metrics'] == report['metrics']
    assert after['accounting'] == report['accounting']
    assert not (out / 'unit-task/task-completion.json').exists()


def test_publication_and_republication_share_decoding_and_newlines(
        finished: tuple[Path, Path, Path], tmp_path: Path) -> None:
    private_root, out, runtime = finished
    raw = b'line\r\ninvalid-\xff\rfinal\n'
    (runtime / 'contract.stderr').write_bytes(raw)
    checkpoint = out / 'checkpoint.json'
    state = json.loads(checkpoint.read_text())
    state['tasks']['unit-task']['control_files']['contract.stderr'] = digest(raw)
    checkpoint.write_text(json.dumps(state))
    private = PrivateGraders.load(private_root, 'unit-task', core.REPOSITORY)
    published = tmp_path / 'expected'
    core.publish(runtime / 'contract.stderr', published, private, source_root=runtime)
    republish.republish(private_root, out)
    assert (out / 'unit-task/contract.stderr').read_bytes() == published.read_bytes()
    assert published.read_bytes() == 'line\ninvalid-\ufffd\nfinal\n'.encode()


@pytest.mark.parametrize('name', ['checkpoint.json', 'report.json'])
def test_manifest_links_refused_before_writing(finished: tuple[Path, Path, Path], tmp_path: Path,
                                              name: str) -> None:
    private, out, _ = finished
    manifest = out / name
    original = tmp_path / name
    manifest.rename(original)
    manifest.symlink_to(original)
    before = snapshot(out)
    with pytest.raises(ValueError):
        republish.republish(private, out)
    assert snapshot(out) == before


def test_existing_absolute_artifact_is_reused_without_duplicate_reference(
        finished: tuple[Path, Path, Path]) -> None:
    private, out, runtime = finished
    target = out / 'unit-task/contract.json'
    target.write_bytes((runtime / 'contract.json').read_bytes())
    report_path = out / 'report.json'
    report = json.loads(report_path.read_text())
    report['tasks'][0]['artifacts'].append({'path': str(target), 'sha256': digest(target.read_bytes())})
    report_path.write_text(json.dumps(report))
    assert republish.republish(private, out)[0]['existing'] == 1
    after = json.loads(report_path.read_text())
    refs = [ref for ref in after['tasks'][0]['artifacts'] if Path(ref['path']).name == 'contract.json']
    assert refs == [{'path': str(target), 'sha256': digest(target.read_bytes())}]
