"""Versioned retained workspace pins, cache exclusion and post-verifier timing."""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from eval.runner import continue_day2, core, reaudit, regrade, republish, rerun_invalid
from eval.runner.audit import PrivateGraders, audit_retained_logs, digest
from eval.runner.process import ProcessResult, run_process
from tests.eval.test_runner import Executor, HarnessExecutor, harness_config, setup
from tests.eval.test_reaudit import finished as audit_finished
from tests.eval.test_republish import finished as publication_finished, snapshot
from tests.eval.test_continue_day2 import stopped
from tests.eval.test_restart_recovery import infrastructure_source

VERSION = 'codex-cli 0.162.0-alpha.17.2'


def add_caches(workspace: Path) -> None:
    for name in ('__pycache__/solution.cpython-313.pyc', '__pycache__/solution.cpython-314.pyc',
                 '__pycache__/test_solution.cpython-314.pyc', 'loose.pyc', 'loose.pyo',
                 '.pytest_cache/v/cache/nodeids', '.mypy_cache/cache.json',
                 '.ruff_cache/one', '.hypothesis/examples/one'):
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'generated cache')


def test_v2_ignores_caches_but_preserves_source_content_modes_and_links(tmp_path: Path) -> None:
    workspace = tmp_path / 'workspace'
    (workspace / 'nested').mkdir(parents=True)
    source = workspace / 'solution.py'
    source.write_text('value = 1\n')
    source.chmod(0o644)
    expected = core.workspace_digest(workspace)
    add_caches(workspace)
    (workspace / 'nested/__pycache__').mkdir()
    (workspace / 'nested/__pycache__/nested.pyc').write_bytes(b'nested cache')
    assert core.workspace_digest(workspace) == expected
    assert core.workspace_digest(workspace, 1) != expected
    source.write_text('value = 2\n')
    assert core.workspace_digest(workspace) != expected
    source.write_text('value = 1\n')
    source.chmod(0o755)
    assert core.workspace_digest(workspace) != expected
    source.chmod(0o644)
    (workspace / 'source-link').symlink_to('solution.py')
    assert core.workspace_digest(workspace) != expected


@pytest.mark.parametrize('version', [1, 2])
@pytest.mark.parametrize('explicit', [False, True])
def test_matching_respects_recorded_algorithm_and_unversioned_legacy(
        tmp_path: Path, version: int, explicit: bool) -> None:
    (tmp_path / 'solution.py').write_text('value = 1\n')
    add_caches(tmp_path)
    record = {'workspace_exit_sha256': core.workspace_digest(tmp_path, version)}
    if explicit:
        record['workspace_digest_version'] = version
    assert core.matching_workspace_digest_version(tmp_path, record) == version
    if version == 2:
        (tmp_path / '__pycache__/new.pyc').write_bytes(b'new interpreter')
        assert core.matching_workspace_digest_version(tmp_path, record) == 2
    (tmp_path / 'solution.py').write_text('value = 2\n')
    assert core.matching_workspace_digest_version(tmp_path, record) is None


def test_v1_known_legacy_manifest_and_no_hash_repair(tmp_path: Path) -> None:
    (tmp_path / '__pycache__').mkdir(mode=0o755)
    cache = tmp_path / '__pycache__/solution.pyc'
    cache.write_bytes(b'old cache')
    cache.chmod(0o644)
    # The exact pre-versioning manifest included the cache directory and file.
    manifest = [['__pycache__', 'directory', 0o755, None],
                ['__pycache__/solution.pyc', 'file', 0o644, digest(b'old cache')]]
    old_hash = digest(json.dumps(manifest, ensure_ascii=True, separators=(',', ':')).encode())
    assert core.workspace_digest(tmp_path, 1) == old_hash
    legacy = {'workspace_exit_sha256': old_hash}
    assert core.matching_workspace_digest_version(tmp_path, legacy) == 1
    cache.write_bytes(b'changed cache')
    assert core.matching_workspace_digest_version(tmp_path, legacy) is None
    assert legacy == {'workspace_exit_sha256': old_hash}


@pytest.mark.parametrize('version', [None, 0, 3, '2', True, 2.0])
def test_explicit_unknown_version_never_falls_back(tmp_path: Path, version: Any) -> None:
    record = {'workspace_exit_sha256': core.workspace_digest(tmp_path), 'workspace_digest_version': version}
    assert core.matching_workspace_digest_version(tmp_path, record) is None
    with pytest.raises(ValueError, match='version'):
        core.workspace_digest(tmp_path, version)


def test_recorded_v1_does_not_fall_back_to_v2(tmp_path: Path) -> None:
    expected = core.workspace_digest(tmp_path, 2)
    add_caches(tmp_path)
    assert core.matching_workspace_digest_version(tmp_path, {'workspace_exit_sha256': expected}) == 2
    assert core.matching_workspace_digest_version(tmp_path, {
        'workspace_exit_sha256': expected, 'workspace_digest_version': 1}) is None


def test_unreadable_source_directory_is_not_silently_omitted(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / 'source').mkdir()
    scandir = os.scandir

    def blocked(path: Any) -> Any:
        if Path(path).name == 'source':
            raise PermissionError('synthetic inaccessible source')
        return scandir(path)

    monkeypatch.setattr(os, 'scandir', blocked)
    with pytest.raises(PermissionError):
        core.workspace_digest(tmp_path)


@pytest.mark.parametrize('version,explicit', [(1, True), (1, False), (2, True), (2, False)])
def test_regrade_accepts_both_retained_versions_without_repinning(
        setup: tuple[Path, Path, Path], tmp_path: Path, version: int, explicit: bool) -> None:
    root, config, out = setup
    core.run(config, out, root, execute=Executor(), version=VERSION)
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    workspace = Path(entry['runtime']) / 'workspace'
    add_caches(workspace)
    for record in (entry, entry['segments'][-1]):
        record['workspace_exit_sha256'] = core.workspace_digest(workspace, version)
        record.pop('workspace_digest_version')
        if explicit:
            record['workspace_digest_version'] = version
    core.write_json(out / 'checkpoint.json', state)
    if version == 2:
        (workspace / '__pycache__/later.pyc').write_bytes(b'after exit')
    before = (out / 'checkpoint.json').read_bytes()
    regrade.regrade(root, out, tmp_path / 'regraded')
    assert (out / 'checkpoint.json').read_bytes() == before
    checks = json.loads((tmp_path / 'regraded/run-diagnostics.json').read_text())['workspace_hash_checks']
    assert checks[0]['matched'] and checks[0]['workspace_digest_version'] == version


def test_harness_pins_each_attempt_after_verifier_and_before_grading(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor()
    monkeypatch.setenv('PYTHONDONTWRITEBYTECODE', '0')
    verified: list[str] = []

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex' and verified:
            entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
            previous = entry['segments'][-2]
            assert previous['workspace_exit_sha256'] == verified[-1]
            assert previous['workspace_digest_version'] == entry['workspace_digest_version'] == 2
        result = executor(argv, **kwargs)
        if '-m' in argv and argv[argv.index('-m') + 1] == 'verifier':
            assert '-B' in argv and kwargs['env']['PYTHONDONTWRITEBYTECODE'] == '1'
            workspace = Path(argv[argv.index('--workspace') + 1])
            # A non-cache marker proves the exit pin is taken after checks.
            (workspace / 'verifier-observation.txt').write_text(str(len(verified)))
            add_caches(workspace)
            verified.append(core.workspace_digest(workspace))
        return result

    core.run(config, out, root, execute=execute, version=VERSION)
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert len(verified) == 2
    assert [s['workspace_exit_sha256'] for s in entry['segments']] == verified
    assert all(s['workspace_digest_version'] == 2 for s in entry['segments'])
    assert entry['workspace_exit_sha256'] == verified[-1]
    assert entry['workspace_digest_version'] == 2
    assert os.environ['PYTHONDONTWRITEBYTECODE'] == '0'


@pytest.mark.parametrize('changed', [False, True])
def test_reaudit_checks_v2_pin_with_new_caches(
        audit_finished: tuple[Path, Path, Path], changed: bool) -> None:
    root, out, runtime = audit_finished
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['unit-task']
    core.record_workspace_exit(runtime / 'workspace', entry, entry['segments'][-1])
    core.write_json(out / 'checkpoint.json', state)
    add_caches(runtime / 'workspace')
    if changed:
        (runtime / 'workspace/source.py').write_text('changed source')
    row = reaudit.reaudit(root, out)[0]
    assert row['status'] == ('inconclusive' if changed else 'clean')
    assert row['error_kinds'] == (['workspace_exit_hash_mismatch'] if changed else [])


@pytest.mark.parametrize('changed', [False, True])
def test_republish_preflights_v2_pin_with_new_caches(
        publication_finished: tuple[Path, Path, Path], changed: bool) -> None:
    root, out, runtime = publication_finished
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['unit-task']
    core.record_workspace_exit(runtime / 'workspace', entry, entry['segments'][-1])
    entry['result']['segments'] = entry['segments']
    core.write_json(out / 'checkpoint.json', state)
    add_caches(runtime / 'workspace')
    before = snapshot(out)
    if changed:
        (runtime / 'workspace/private.py').write_text('changed source')
        with pytest.raises(ValueError, match='hash mismatch'):
            republish.republish(root, out)
        assert snapshot(out) == before
    else:
        assert republish.republish(root, out)[0]['published'] > 0


@pytest.mark.parametrize('version,explicit', [(1, True), (1, False), (2, True), (2, False)])
def test_day2_copy_and_retained_audit_context_preserve_version(
        stopped: tuple[Path, Path, Any], version: int, explicit: bool) -> None:
    root, source, _ = stopped
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    workspace = Path(entry['runtime']) / 'workspace'
    add_caches(workspace)
    for record in (entry, entry['segments'][-1]):
        record['workspace_exit_sha256'] = core.workspace_digest(workspace, version)
        record.pop('workspace_digest_version')
        if explicit:
            record['workspace_digest_version'] = version
    private = PrivateGraders.load(root, 'bug-chunk-tail', core.REPOSITORY)
    copied = continue_day2.copy_runtime(entry, private)
    runtime = Path(copied['runtime'])
    assert core.matching_workspace_digest_version(runtime / 'workspace', copied) == version
    context = copied['retained_audit_context']
    assert context.get('workspace_digest_version') == (version if explicit else None)
    paths = [Path(path) for path in context['logs']]
    kwargs = dict(retained_context=context, workspace=runtime / 'workspace',
                  repository=core.REPOSITORY, grading_roots=core.audit_roots(runtime))
    assert audit_retained_logs(paths, private, **kwargs)['status'] == 'clean'
    (workspace / 'changed-source.py').write_text('source changed after copy')
    audit = audit_retained_logs(paths, private, **kwargs)
    assert audit['status'] == 'inconclusive'
    assert 'retained_context_workspace_hash_mismatch' in audit['errors']


@pytest.mark.parametrize('changed', [False, True])
def test_rerun_invalid_checks_selected_and_unselected_workspace_pins(
        setup: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        changed: bool) -> None:
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    state = json.loads((source / 'checkpoint.json').read_text())
    for entry in state['tasks'].values():
        add_caches(Path(entry['runtime']) / 'workspace')
    if changed:
        entry = state['tasks']['bug-chunk-tail']
        (Path(entry['runtime']) / 'workspace/chunking.py').write_text('changed source')
    executor = Executor()

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert not changed, 'Mismatched retained pin must fail before all calls'
        return executor(argv, **kwargs) if argv[0] == 'codex' else run_process(argv, **kwargs)

    out = tmp_path / 'rerun'
    if changed:
        with pytest.raises(ValueError, match='hash mismatch'):
            rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'},
                                        execute=execute, version=VERSION)
        assert not out.exists()
    else:
        report = json.loads(rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'},
                            execute=execute, version=VERSION).read_text())
        assert executor.calls == 1
        assert all(task['outcome'] == 'pass' for task in report['tasks'])


def test_pending_verifier_recovery_repins_after_each_failed_check(
        setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor()
    failures = 0

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal failures
        if '-m' in argv and argv[argv.index('-m') + 1] == 'verifier' and failures < 2:
            failures += 1
            workspace = Path(argv[argv.index('--workspace') + 1])
            (workspace / 'verification-marker.txt').write_text(str(failures))
            add_caches(workspace)
            kwargs['stdout'].write_text('')
            kwargs['stderr'].write_text('control_cli_events ' + json.dumps({
                'model': 'gpt-6-luna', 'events': (Path(__file__).parent / 'fixtures/usage-limit.jsonl').read_text()}) + '\n')
            return ProcessResult(2)
        return executor(argv, **kwargs)

    pins = []
    for _ in range(2):
        with pytest.raises(core.IncompleteRun, match='usage limit'):
            core.run(config, out, root, execute=limited, version=VERSION)
        entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
        assert entry['pending_verification'] and len(entry['segments']) == 1
        assert entry['workspace_exit_sha256'] == core.workspace_digest(Path(entry['runtime']) / 'workspace')
        assert entry['segments'][-1]['workspace_digest_version'] == entry['workspace_digest_version'] == 2
        pins.append(entry['workspace_exit_sha256'])
    assert pins[0] != pins[1]
    core.run(config, out, root, execute=limited, version=VERSION)
    assert executor.calls == 2
