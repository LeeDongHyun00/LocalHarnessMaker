"""Versioned populations and optional executor-tier evidence use mocked calls only."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core
from eval.runner.audit import PrivateGraders
from eval.runner.compare import compare
from eval.runner.telemetry import collect
from tests.eval.test_runner import Executor, setup  # noqa: F401
from tests.eval.test_compare import report


def test_candidate_inventory_and_pilot_configuration() -> None:
    config = core.load_config(core.REPOSITORY / 'eval/configs/pilot-v2-a.yaml')
    root = core.task_directory(config)
    tasks = sorted(p.name for p in root.iterdir() if p.is_dir())
    pilot_tasks = set(config['tasks'])
    assert pilot_tasks < set(tasks) and len(pilot_tasks) == 20 and len(tasks) == 100
    v1 = {p.name for p in (core.REPOSITORY / 'eval/tasks').iterdir() if p.is_dir()}
    assert not set(tasks) & v1
    families: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        meta = json.loads((root / task / 'meta.json').read_text())
        assert meta['id'] == task and task.startswith('v2-')
        assert meta['frozen'] is True and meta['version'] == 2
        assert (root / task / 'day2.md').is_file() == meta['two_session']
        assert 3 <= len(list((root / task / 'workspace/project').glob('*.py'))) <= 8
        text = (root / task / 'prompt.md').read_text()
        count = len(__import__('re').findall(r'(?m)^R\d+\.', text))
        assert count == ((10 if meta['two_session'] else 12) if task in pilot_tasks else 16)
        if task not in pilot_tasks and meta['two_session']:
            tomorrow = (root / task / 'day2.md').read_text()
            assert len(__import__('re').findall(r'(?m)^D\d+\.', tomorrow)) == 2
            assert meta['family'] not in tomorrow
            assert 'casefold' not in tomorrow and "replace('_'" not in tomorrow
        families.setdefault(meta['family'], []).append(meta)
    assert len(families) == 20
    for members in families.values():
        assert len(members) == 5 and sum(m['two_session'] for m in members) == 1
        assert {m['type'] for m in members} == {'bug_fix', 'feature_plus_test', 'multiple_requirements', 'constrained_refactoring'}
    baseline = core.load_config(core.REPOSITORY / 'eval/configs/full-a.yaml')
    assert (config['model'], config['reasoning_effort']) == (baseline['model'], baseline['reasoning_effort'])
    assert config['service_tier'] == 'priority' and config['retry_limit'] == 0
    assert config['codex_version'] == 'codex-cli 0.163.0-alpha.11.1'
    assert config['timeout_seconds'] == 900 and core.paid_call_bound(config) == 24
    assert set(config['task_timeout_seconds'].values()) == {1800}


@pytest.mark.parametrize('name, count, effort, calls', [
    ('a', 100, 'medium', 120), ('b', 80, 'max', 80),
    ('harness', 100, 'medium', 780),
])
def test_full_v2_population_and_frozen_digest_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, count: int, effort: str, calls: int,
) -> None:
    path = core.REPOSITORY / f'eval/configs/full-v2-{name}.yaml'
    config = core.load_config(path)
    population = sorted(p.name for p in core.task_directory(config).glob('v2-*') if p.is_dir())
    assert config['tasks'] == sorted(config['tasks'])
    assert len(config['tasks']) == count and len(population) == 100
    assert config.get('task_population', config['tasks']) == population
    assert config['reasoning_effort'] == effort and config['model'] == 'gpt-6.1-sol'
    assert config['service_tier'] == 'priority' and config['calibration'] is False
    assert config['codex_version'] == 'codex-cli 0.163.0-alpha.11.1'
    assert config['retry_limit'] == 0 and core.paid_call_bound(config) == calls
    assert config['harness'] == (name == 'harness')
    assert config['control_backend'] == ('codex_cli' if name == 'harness' else 'none')
    assert config['reinstruction_limit'] == (2 if name == 'harness' else 0)
    expected_two = {task for task in population
                    if (core.task_directory(config) / task / 'day2.md').is_file()}
    assert set(config['task_timeout_seconds']) == (set() if name == 'b' else expected_two)
    if name == 'b':
        assert not set(config['tasks']) & expected_two
    else:
        assert config['tasks'] == population

    class PopulationSelected(Exception):
        pass

    observed: list[set[str]] = []

    def selected_digest(graders: dict[str, Any], requested: dict[str, Any]) -> str:
        assert requested == config
        observed.append(set(graders))
        if set(graders) == set(population):
            raise PopulationSelected
        return 'selected-subset'

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError('No executor calls during freeze verification')

    # Synthetic graders only; reach the real runner's post-freeze digest selection.
    monkeypatch.setattr(core.PrivateGraders, 'load', lambda *a, **k: object())
    monkeypatch.setattr(core, 'configured_digest', selected_digest)
    with pytest.raises(PopulationSelected):
        core.run(path, tmp_path / 'out', tmp_path / 'unused-private',
                 execute=forbidden, version=config['codex_version'])
    assert observed[-1] == set(population)
    assert len(observed) == (2 if name == 'b' else 1)
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('root', ['', '../tasks', '/tmp/tasks', 'eval/../tasks', 'eval/tasks/', 'eval/tasks/a', None, 1])
def test_noncanonical_roots_rejected(root: Any) -> None:
    with pytest.raises(ValueError, match='task_root'):
        core.task_directory({'task_root': root})


def test_symlink_task_root_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / 'eval').mkdir()
    (tmp_path / 'eval/tasks-v2').symlink_to(core.REPOSITORY / 'eval/tasks-v2', target_is_directory=True)
    monkeypatch.setattr(core, 'REPOSITORY', tmp_path)
    with pytest.raises(ValueError, match='task_root'):
        core.task_directory({'task_root': 'eval/tasks-v2'})


@pytest.mark.parametrize('tier', ['', None, 1, 'priority"', 'priority\n'])
def test_bad_tier_config_rejected(setup: tuple[Path, Path, Path], tier: Any) -> None:
    _, path, _ = setup
    config = json.loads(path.read_text())
    config['service_tier'] = tier
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='service_tier'):
        core.load_config(path)


@pytest.mark.parametrize('applied', [None, 'standard', 'priority'])
def test_tier_requires_explicit_applied_record(tmp_path: Path, applied: str | None) -> None:
    events = [{'type': 'turn_context', 'payload': {'model': 'sol', 'effort': 'medium', 'service_tier': 'priority'}}]
    if applied:
        events.append({'type': 'event_msg', 'payload': {'type': 'thread_settings_applied', 'thread_settings': {
            'model': 'sol', 'reasoning_effort': 'medium', 'service_tier': applied}}})
    native = tmp_path / 'native.jsonl'
    native.write_text(''.join(json.dumps(e) + '\n' for e in events))
    evidence = collect([], [native], 'sol', 'medium', 'priority')['settings_evidence']
    assert evidence['verified'] == evidence['service_tier_verified'] == (applied == 'priority')
    # Without a tier request, historical model/effort verification is unchanged.
    assert collect([], [native], 'sol', 'medium')['settings_evidence']['verified']


@pytest.mark.parametrize('observed', [None, 'standard', 'priority'])
def test_launch_tier_and_invalidation_and_checkpoint(setup: tuple[Path, Path, Path], observed: str | None) -> None:
    root, path, out = setup
    config = json.loads(path.read_text())
    config['service_tier'] = 'priority'
    path.write_text(json.dumps(config))

    class TierExecutor(Executor):
        def __call__(self, argv: list[str], **kwargs: Any) -> Any:
            if argv[0] == 'codex':
                assert 'service_tier="priority"' in argv
                result = super().__call__(argv, **kwargs)
                if observed is not None:
                    native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
                    fixture = Path(__file__).parent / 'fixtures/native-session-0.163.jsonl'
                    event = next(json.loads(line) for line in fixture.read_text().splitlines()
                                 if json.loads(line).get('payload', {}).get('type') == 'thread_settings_applied')
                    event['payload']['thread_id'] = 'unit-session'
                    event['payload']['thread_settings']['service_tier'] = observed
                    with native.open('a') as stream:
                        stream.write(json.dumps(event) + '\n')
                return result
            return super().__call__(argv, **kwargs)

    result = json.loads(core.run(path, out, root, execute=TierExecutor(), version=config['codex_version']).read_text())
    task = result['tasks'][0]
    assert (task['outcome'] == 'invalid') == (observed != 'priority')
    if observed != 'priority':
        assert 'executor_service_tier_missing_or_different' in task['invalid_reasons']
        assert task['grading'] is None
    else:
        assert task['outcome'] == 'pass'
        # Native priority evidence selects the Fast snapshot.
        assert task['costs']['total_usd'] == pytest.approx(.000221)
    checkpoint = json.loads((out / 'checkpoint.json').read_text())
    assert checkpoint['config']['service_tier'] == 'priority'
    assert json.loads((out / 'run-diagnostics.json').read_text())['service_tier'] == 'priority'


def test_root_namespaces_digests_and_compare_refuses_cross_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = tmp_path / 'repo'
    for name in ('tasks', 'tasks-v2'):
        public = repository / 'eval' / name / 'same'
        public.mkdir(parents=True)
        (public / 'prompt.md').write_text('same bytes')
    private = tmp_path / 'trusted/same'
    private.mkdir(parents=True)
    (private / 'test_synthetic.py').write_text('same synthetic grader bytes')
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    def files(task: str, task_root: str = 'eval/tasks') -> list[Path]:
        return [repository / task_root / task / 'prompt.md']
    monkeypatch.setattr(core, 'public_files', files)
    graders = {'same': PrivateGraders.load(private.parent, 'same', repository)}
    old = core.taskset_digest(graders)
    assert old == core.configured_digest(graders, {}) == core.configured_digest(graders, {'task_root': 'eval/tasks'})
    new = core.configured_digest(graders, {'task_root': 'eval/tasks-v2'})
    assert old != new
    left, right = report(), report()
    left['metadata']['task_set_sha256'], right['metadata']['task_set_sha256'] = old, new
    with pytest.raises(ValueError, match='task_set_sha256'):
        compare(left, right)


def test_selected_root_population_resume_and_freeze(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil
    from tests.eval.test_runner import two_task_config
    from eval.runner import regrade
    root, path, out = setup
    two_task_config(root, path, monkeypatch, tmp_path)
    candidate = core.REPOSITORY / 'eval/candidate'
    shutil.copytree(core.REPOSITORY / 'eval/tasks', candidate)
    (candidate / 'bug-chunk-tail/prompt.md').write_text('Distinct candidate prompt; repair the tail.\n')
    config = json.loads(path.read_text())
    config.update(task_root='eval/candidate', tasks=['bug-chunk-tail'], task_population=['bug-chunk-tail', 'second-task'])
    path.write_text(json.dumps(config))
    def files(task: str, task_root: str = 'eval/tasks') -> list[Path]:
        return sorted(p for p in (core.REPOSITORY / task_root / task).rglob('*') if p.is_file())
    monkeypatch.setattr(core, 'public_files', files)
    executor = Executor()
    def execute(argv: list[str], **kwargs: Any) -> Any:
        if argv[0] == 'codex':
            assert kwargs['stdin'] == 'Distinct candidate prompt; repair the tail.\n'
            assert not any(v.startswith('service_tier=') for v in argv)
        return executor(argv, **kwargs)
    result = json.loads(core.run(path, out, root, execute=execute, version=config['codex_version']).read_text())
    assert result['tasks'][0]['outcome'] == 'pass'
    checkpoint = json.loads((out / 'checkpoint.json').read_text())
    assert checkpoint['task_set_sha256'] != checkpoint['selected_task_set_sha256']
    core.run(path, out, root, execute=execute, version=config['codex_version'])
    assert executor.calls == 1
    regraded = json.loads(regrade.regrade(root, out, tmp_path / 'regraded').read_text())
    assert regraded['tasks'][0]['outcome'] == 'pass'
    population_meta = candidate / 'second-task/meta.json'
    meta = json.loads(population_meta.read_text())
    meta['frozen'] = False
    population_meta.write_text(json.dumps(meta))
    with pytest.raises(ValueError, match='unfrozen'):
        core.run(path, tmp_path / 'unfrozen', root, execute=execute, version=config['codex_version'])
    assert executor.calls == 1


@pytest.mark.parametrize('missing_day', [0, 1, 2])
def test_tier_required_on_both_fresh_sessions(setup: tuple[Path, Path, Path], tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch, missing_day: int) -> None:
    from tests.eval.test_runner import TwoSessionExecutor, two_session_config
    root, path, out = two_session_config(setup, monkeypatch, tmp_path)
    config = json.loads(path.read_text())
    config['service_tier'] = 'priority'
    path.write_text(json.dumps(config))

    class BothDays(TwoSessionExecutor):
        def __call__(self, argv: list[str], **kwargs: Any) -> Any:
            if argv[0] != 'codex':
                return super().__call__(argv, **kwargs)
            assert 'service_tier="priority"' in argv
            result = super().__call__(argv, **kwargs)
            if self.calls != missing_day:
                fixture = Path(__file__).parent / 'fixtures/native-session-0.163.jsonl'
                event = next(json.loads(line) for line in fixture.read_text().splitlines()
                             if json.loads(line).get('payload', {}).get('type') == 'thread_settings_applied')
                event['payload']['thread_id'] = f'day-{self.calls}'
                event['payload']['thread_settings']['service_tier'] = 'priority'
                native = Path(kwargs['env']['CODEX_HOME']) / f'sessions/rollout-day-{self.calls}.jsonl'
                with native.open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
            return result
    task = json.loads(core.run(path, out, root, execute=BothDays(), version=config['codex_version']).read_text())['tasks'][0]
    assert (task['outcome'] == 'pass') == (missing_day == 0)
    if missing_day:
        assert 'executor_service_tier_missing_or_different' in task['invalid_reasons']
        assert task['grading'] is None


@pytest.mark.parametrize('tier', [None, [], {}, 1, 'standard'])
def test_missing_or_malformed_native_tier_invalidates_without_fake_price(tmp_path: Path, tier: Any) -> None:
    native = tmp_path / 'native.jsonl'
    native.write_text(json.dumps({'type': 'event_msg', 'payload': {'type': 'thread_settings_applied',
        'thread_settings': {'model': 'sol', 'reasoning_effort': 'medium', 'service_tier': tier}}}) + '\n')
    observed = collect([], [native], 'sol', 'medium', 'priority')
    assert not observed['settings_evidence']['service_tier_verified']
    assert observed['pricing_evidence']['tier'] == ('standard' if tier == 'standard' else 'unknown')
    native.write_text('{"type":"turn_context","payload":{"model":"sol","effort":"medium"}}\n')
    assert collect([], [native], 'sol', 'medium', 'priority')['pricing_evidence']['tier'] == 'unknown'


def test_explicit_tier_is_passed_on_interrupted_resume(setup: tuple[Path, Path, Path]) -> None:
    root, path, out = setup
    config = json.loads(path.read_text())
    config['service_tier'] = 'priority'
    path.write_text(json.dumps(config))
    executor = Executor(interrupt=True)
    launches = []
    def execute(argv: list[str], **kwargs: Any) -> Any:
        if argv[0] == 'codex':
            assert 'service_tier="priority"' in argv
            launches.append(argv)
        return executor(argv, **kwargs)
    with pytest.raises(core.IncompleteRun):
        core.run(path, out, root, execute=execute, version=config['codex_version'])
    result = json.loads(core.run(path, out, root, execute=execute, version=config['codex_version']).read_text())
    assert len(launches) == 2 and 'resume' in launches[1]
    assert result['tasks'][0]['outcome'] == 'invalid'
    assert 'executor_service_tier_missing_or_different' in result['tasks'][0]['invalid_reasons']
