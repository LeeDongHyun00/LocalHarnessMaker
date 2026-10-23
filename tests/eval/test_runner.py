"""Mock executor behavior and prove grading occurs only after termination."""

import json
import shlex
from pathlib import Path
from typing import Any

import pytest

from eval.runner.core import REPOSITORY, IncompleteRun, load_config, run
from eval.runner.audit import PrivateGraders
from eval.runner.process import ProcessResult, run_process


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    auth_home = tmp_path / "original-home"
    auth_home.mkdir()
    (auth_home / "auth.json").write_text("{}")
    monkeypatch.setenv("CODEX_HOME", str(auth_home))
    root = tmp_path / "trusted"
    task = root / "bug-chunk-tail"
    task.mkdir(parents=True)
    (task / "test_private_synthetic.py").write_text(
        "import unittest\nfrom chunking import chunked\n"
        "class Checks(unittest.TestCase):\n"
        " def test_one(self): self.assertEqual(chunked([1], 2), [[1]])\n"
        " def test_tail(self): self.assertEqual(chunked([1,2,3], 2), [[1,2],[3]])\n"
        " def test_unit(self): self.assertEqual(chunked([1,2], 1), [[1],[2]])\n"
    )
    config = tmp_path / "config.yaml"
    config.write_text((REPOSITORY / "eval/configs/pilot.yaml").read_text())
    return root, config, tmp_path / "out"


class Executor:
    """Simulate Codex while using the real grader subprocess."""

    def __init__(self, *, leak: bool = False, incomplete: bool = False, interrupt: bool = False) -> None:
        self.calls = 0
        self.finished = False
        self.leak = leak
        self.incomplete = incomplete
        self.interrupt = interrupt

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != "codex":
            assert self.finished, "Grading started before executor exit"
            return run_process(argv, **kwargs)
        self.calls += 1
        env = kwargs["env"]
        assert "LHM_PRIVATE_GRADERS" not in env
        assert kwargs["cwd"].is_dir()
        assert not list(kwargs["cwd"].glob("test_private_*.py"))
        session = Path(env["CODEX_HOME"]) / "sessions"
        session.mkdir(exist_ok=True)
        (session / "rollout-unit.jsonl").write_text(
            json.dumps({"type": "session_meta", "payload": {"id": "unit-session",
                        "cli_version": "0.162.0-alpha.17.2"}}) + "\n" +
            json.dumps({"type": "turn_context", "payload": {"model": "gpt-6.1-sol", "effort": "medium"}}) + "\n")
        events = [{"type": "thread.started", "thread_id": "unit-session"}]
        if self.leak:
            events.append({"type": "item.completed", "item": {"type": "command_execution", "command": "cat test_private_synthetic.py"}})
        if not self.incomplete and not self.interrupt:
            events.append({"type": "turn.completed", "usage": {"input_tokens": 20, "cached_input_tokens": 5, "output_tokens": 8}})
        kwargs["stdout"].write_text("".join(json.dumps(e) + "\n" for e in events))
        kwargs["stderr"].write_text("")
        source = kwargs["cwd"] / "chunking.py"
        source.write_text(source.read_text().replace("len(items) - 1", "len(items)"))
        # Executor-authored tests must not inflate the hidden-test denominator.
        (kwargs["cwd"] / "test_public.py").write_text("raise RuntimeError('not a private grader')\n")
        self.finished = True
        if self.interrupt:
            self.interrupt = False
            raise KeyboardInterrupt
        return ProcessResult(0)


def test_baseline_grades_after_exit_and_completed_checkpoint_does_not_repeat(setup: tuple[Path, Path, Path],
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    root, config, out = setup
    executor = Executor()
    computations: list[Path] = []
    original = PrivateGraders._compute_line_fingerprints

    def counted(private: PrivateGraders) -> set[str]:
        computations.append(private.root)
        return original(private)

    monkeypatch.setattr(PrivateGraders, "_compute_line_fingerprints", counted)
    report = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert computations == [root.resolve()]
    result = report["tasks"][0]
    assert result["outcome"] == "pass"
    assert result["grading"]["passed_tests"] == 3
    assert result["grader_access_audit"]["status"] == "clean"
    assert result["calls"][0]["usage"]["usd"] == pytest.approx(.0001105)
    assert report["accounting"]["total_cost_usd"] == pytest.approx(.0001105)
    assert report["metrics"]["cost_per_pass"]["value"] == pytest.approx(.0001105)
    diagnostics = json.loads((out / "run-diagnostics.json").read_text())
    observed = diagnostics["executor_runs"][0]
    assert observed["task_id"] == "bug-chunk-tail" and observed["attempt"] == 1
    assert observed["tokens"] == {"input_tokens": 20, "cached_input_tokens": 5, "output_tokens": 8}
    assert observed["plan_usage"]["before"] is observed["plan_usage"]["after"] is None
    assert report["metrics"]["pass_rate"]["value"] == 1
    assert str(root) not in "".join(p.read_text() for p in out.rglob("*") if p.is_file())
    run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2")
    assert executor.calls == 1


@pytest.mark.parametrize("options", [{"leak": True}, {"incomplete": True}])
def test_invalid_runs_keep_evidence_and_never_grade(setup: tuple[Path, Path, Path], options: dict[str, bool]) -> None:
    root, config, out = setup
    result = json.loads(run(config, out, root, execute=Executor(**options), version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert result["tasks"][0]["outcome"] == "invalid"
    assert result["tasks"][0]["grading"] is None
    assert (out / "bug-chunk-tail/exec-1.jsonl").exists()
    assert result["metrics"]["pass_rate"]["sample_size"] == 0


@pytest.mark.parametrize("metadata_leak", [False, True])
def test_native_audit_persists_all_errors_and_blocks_grading(setup: tuple[Path, Path, Path],
                                                           metadata_leak: bool) -> None:
    root, config, out = setup

    class NativeExecutor(Executor):
        def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
            assert argv[0] == "codex", "Invalid native evidence must prevent grading"
            result = super().__call__(argv, **kwargs)
            fixture = Path(__file__).parent / "fixtures/native-session-0.162.jsonl"
            events = [json.loads(line) for line in fixture.read_text().splitlines()]
            events[0]["payload"].update(id="unit-session", cli_version="0.162.0-alpha.17.2")
            events[7]["payload"].update(model="gpt-6.1-sol", effort="medium")
            if metadata_leak:
                events[6]["payload"]["state"]["synthetic_location"] = str(root)
            events.extend([{"type": "synthetic_unknown_one"}, {"type": "synthetic_unknown_two"}])
            native = Path(kwargs["env"]["CODEX_HOME"]) / "sessions/rollout-unit.jsonl"
            native.write_text("".join(json.dumps(event) + "\n" for event in events))
            return result

    report = json.loads(run(config, out, root, execute=NativeExecutor(), version="codex-cli 0.162.0-alpha.17.2").read_text())
    task = report["tasks"][0]
    assert task["outcome"] == "invalid" and task["grading"] is None
    audit_path = out / "bug-chunk-tail/access-audit.json"
    audit = json.loads(audit_path.read_text())
    assert any(e == "unsupported_event:rollout-unit.jsonl:34:synthetic_unknown_one" for e in audit["errors"])
    assert any(e == "unsupported_event:rollout-unit.jsonl:35:synthetic_unknown_two" for e in audit["errors"])
    assert str(root) not in audit_path.read_text()
    if metadata_leak:
        assert audit["status"] == "access_detected"
        assert "reached executor context" in task["grader_access_audit"]["reason"]
    else:
        assert audit["status"] == "inconclusive"
        assert "synthetic_unknown_one" in task["grader_access_audit"]["reason"]
        assert "synthetic_unknown_two" in task["grader_access_audit"]["reason"]
    assert json.loads((audit_path.parent / "result.json").read_text())["grader_access_audit"] == audit


def test_interrupted_turn_resumes_same_session_before_grading(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor(interrupt=True)
    with pytest.raises(IncompleteRun, match="STOP-E1"):
        run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2")
    assert not (out / "report.json").exists()
    second = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    # Recovery cannot erase the interrupted stream's incomplete audit evidence.
    assert second["tasks"][0]["outcome"] == "invalid"
    assert second["tasks"][0]["attempts"] == 2
    assert executor.calls == 2


def test_paid_batch_guard_and_config_pin(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    with pytest.raises(ValueError, match="version"):
        run(config, out, root, version="different-version")
    value = json.loads(config.read_text())
    value["retry_limit"] = 9
    config.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="STOP-3"):
        load_config(config)


def test_grading_crash_recovers_without_resuming_executor(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor()

    def failing_grader(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != "codex":
            raise RuntimeError("Simulated interruption after grader copy")
        return executor(argv, **kwargs)

    with pytest.raises(RuntimeError):
        run(config, out, root, execute=failing_grader, version="codex-cli 0.162.0-alpha.17.2")
    state = json.loads((out / "checkpoint.json").read_text())
    assert state["tasks"]["bug-chunk-tail"]["phase"] == "grading"
    report = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert report["tasks"][0]["outcome"] == "pass"
    assert executor.calls == 1


def test_transport_retry_resumes_before_any_grading(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    value = json.loads(config.read_text())
    value["retry_limit"] = 1
    config.write_text(json.dumps(value))
    executor = Executor()

    def transport(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == "codex" and executor.calls == 0:
            executor(argv, **kwargs)
            kwargs["stdout"].write_text('{"type":"thread.started","thread_id":"unit-session"}\n{"type":"turn.failed"}\n')
            return ProcessResult(1)
        if argv[0] == "codex":
            assert "resume" in argv and "unit-session" in argv
            assert not list(kwargs["cwd"].parent.glob("grading-*"))
        return executor(argv, **kwargs)

    report = json.loads(run(config, out, root, execute=transport, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert report["tasks"][0]["outcome"] == "pass"
    assert report["tasks"][0]["attempts"] == 2


class HarnessExecutor(Executor):
    """Fake the frozen CLIs without importing either implementation."""

    def __init__(self, *, fail_contract: bool = False, leak_resume: bool = False,
                 exhausted: bool = False, bad_ids: bool = False) -> None:
        super().__init__()
        self.operations: list[str] = []
        self.fail_contract = fail_contract
        self.leak_resume = leak_resume
        self.exhausted = exhausted
        self.bad_ids = bad_ids

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        if "-m" in argv and argv[argv.index("-m") + 1] in {"controller", "verifier"}:
            module = argv[argv.index("-m") + 1]
            operation = argv[argv.index("-m") + 2]
            self.operations.append(operation)
            assert kwargs["env"]["HARNESS_NESTED"] == "1"
            assert "LHM_PRIVATE_GRADERS" not in kwargs["env"]
            destination = Path(argv[argv.index("--out") + 1])
            assert not list(destination.parent.glob("grading-*"))
            if module == "controller":
                assert argv[argv.index("--backend") + 1] == "codex_cli"
                assert argv[argv.index("--handoff") + 1] == "none"
                value = {"task_summary": "Repair chunk tail", "constraints": [],
                         "success_criteria": [{"id": "SC-1", "description": "Fix tail", "check": {"type": "file_exists", "path": "chunking.py"}}],
                         "verification": [], "stop_conditions": [], "assumptions": [],
                         "reasoning_effort": {"value": "medium", "rationale": "Fixture"},
                         "cost_estimate": {"input_tokens": 10, "output_tokens": 10, "usd": .01}}
                if self.fail_contract:
                    kwargs["stdout"].write_text("")
                    kwargs["stderr"].write_text("controller unavailable\n")
                    return ProcessResult(2)
            else:
                assert kwargs["env"]["HARNESS_BACKEND"] == "codex_cli"
                assert kwargs["env"]["HARNESS_MAX_ATTEMPTS"] == "2"
                attempt = int(argv[argv.index("--attempt") + 1])
                value = {"items": [{"id": "wrong" if self.bad_ids else "SC-1", "status": "fail" if attempt == 1 else "pass",
                                   "evidence": "Public fixture evidence", "reason": "check result"}],
                         "overall": "fail" if attempt == 1 else "pass", "attempt": attempt,
                         "reinstruct_message": None if self.exhausted or attempt == 2 else "Fix SC-1 only."}
            destination.write_text(json.dumps(value))
            kwargs["stdout"].write_text(str(destination) + "\n")
            kwargs["stderr"].write_text("")
            return ProcessResult(0)
        if argv[0] == "codex":
            if self.calls == 0:
                assert "Approved evaluation contract" in kwargs["stdin"]
            else:
                assert "resume" in argv and "unit-session" in argv
                assert kwargs["stdin"] == "Fix SC-1 only."
                if self.leak_resume:
                    self.leak = True
        return super().__call__(argv, **kwargs)


def harness_config(config: Path) -> None:
    value = json.loads(config.read_text())
    value.update(harness=True, control_backend="codex_cli", reinstruction_limit=1)
    config.write_text(json.dumps(value))


def test_harness_contract_verify_reinstruction_then_grade(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    import os
    root, config, out = setup
    harness_config(config)
    monkeypatch.delenv("HARNESS_NESTED", raising=False)
    executor = HarnessExecutor()
    report = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert executor.calls == 2
    assert executor.operations == ["contract", "check", "check"]
    assert report["tasks"][0]["outcome"] == "pass"
    assert report["tasks"][0]["costs"]["control_usd"] is None
    assert "HARNESS_NESTED" not in os.environ
    assert (out / "bug-chunk-tail/contract.json").exists()
    assert (out / "bug-chunk-tail/verdict-2.json").exists()
    run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2")
    assert executor.calls == 2
    assert executor.operations == ["contract", "check", "check"]


@pytest.mark.parametrize("options,expected_calls", [({"fail_contract": True}, 0), ({"leak_resume": True}, 2), ({"bad_ids": True}, 1)])
def test_harness_failure_or_access_never_grades(setup: tuple[Path, Path, Path], options: dict[str, bool], expected_calls: int) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor(**options)
    report = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert executor.calls == expected_calls
    assert report["tasks"][0]["outcome"] == "invalid"
    assert report["tasks"][0]["grading"] is None
    assert report["validity"]["status"] == "invalid"
    run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2")
    assert executor.calls == expected_calls


def test_null_reinstruction_stops_without_resuming(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor(exhausted=True)
    run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2")
    assert executor.calls == 1
    assert executor.operations == ["contract", "check"]


def test_report_runtime_invariants_and_hashes(setup: tuple[Path, Path, Path]) -> None:
    import copy
    from eval.runner.report import build, validate
    root, config, out = setup
    report = json.loads(run(config, out, root, execute=Executor(), version="codex-cli 0.162.0-alpha.17.2").read_text())
    for mutation in ('accounting', 'metric', 'cost', 'hash', 'order', 'duplicate'):
        changed = copy.deepcopy(report)
        if mutation == 'accounting':
            changed['accounting']['valid_tasks'] += 1
        elif mutation == 'metric':
            changed['metrics']['pass_rate']['sample_size'] += 1
        elif mutation == 'cost':
            changed['tasks'][0]['costs']['executor_usd'] = 3
        elif mutation == 'hash':
            changed['tasks'][0]['executor_segments'][0]['events']['sha256'] = '0' * 64
        elif mutation == 'order':
            changed['tasks'][0]['executor_segments'][0]['exited_at'] = '2000-01-01T00:00:00Z'
        else:
            changed['tasks'].append(copy.deepcopy(changed['tasks'][0]))
        with pytest.raises(ValueError):
            validate(changed, REPOSITORY)


def test_missing_executor_capture_is_recorded_invalid(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup

    def missing_capture(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] == 'codex'  # no grader may run
        return ProcessResult(0)

    report = json.loads(run(config, out, root, execute=missing_capture, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'invalid'
    assert report['tasks'][0]['grading'] is None
    assert report['tasks'][0]['calls'][0]['usage']['usd'] is None


def test_provisional_checkpoint_requires_explicit_migration(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    out.mkdir()
    (out / 'checkpoint.json').write_text('{}')
    executor = Executor()
    with pytest.raises(ValueError, match='offline migration'):
        run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2')
    assert executor.calls == 0


def two_task_config(root: Path, config: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import shutil
    import eval.runner.core as core
    repository = tmp_path / 'repository'
    repository.mkdir()
    shutil.copytree(REPOSITORY / 'schemas', repository / 'schemas')
    (repository / 'eval/tasks').mkdir(parents=True)
    shutil.copy2(REPOSITORY / 'eval/prices.yaml', repository / 'eval/prices.yaml')
    for task_id in ('bug-chunk-tail', 'second-task'):
        shutil.copytree(REPOSITORY / 'eval/tasks/bug-chunk-tail', repository / 'eval/tasks' / task_id)
    shutil.copytree(root / 'bug-chunk-tail', root / 'second-task')
    value = json.loads(config.read_text())
    value.update(tasks=['bug-chunk-tail', 'second-task'], seed=0)
    config.write_text(json.dumps(value))
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    monkeypatch.setattr(core, 'public_files', lambda task: sorted(p for p in (repository / 'eval/tasks' / task).rglob('*') if p.is_file()))
    # Report git provenance is read from the original repository, never a model.
    original_build = core.build
    monkeypatch.setattr(core, 'build', lambda c, s, t, v, r, **kw: original_build(c, s, t, v, REPOSITORY, **kw))


@pytest.mark.parametrize('frozen', [False, None, 'true', 1])
def test_unfrozen_task_rejected_before_external_work(
    setup: tuple[Path, Path, Path], tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, frozen: Any,
) -> None:
    import eval.runner.core as core

    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    metadata = core.REPOSITORY / 'eval/tasks/second-task/meta.json'
    value = json.loads(metadata.read_text())
    if frozen is None:
        value.pop('frozen')
    else:
        value['frozen'] = frozen
    metadata.write_text(json.dumps(value))

    def unexpected_call(*args: Any, **kwargs: Any) -> Any:
        pytest.fail('Freeze validation must precede all external work')

    monkeypatch.setattr(core.subprocess, 'run', unexpected_call)
    monkeypatch.setattr(core.PrivateGraders, 'load', unexpected_call)
    with pytest.raises(ValueError, match='every selected task to be frozen'):
        run(config, out, root, execute=unexpected_call)
    assert not out.exists()


@pytest.mark.parametrize('wrap', [False, True])
@pytest.mark.parametrize('absolute', [False, True])
@pytest.mark.parametrize('cross_run', [False, True])
def test_previous_grading_copy_access_invalidates(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch, absolute: bool, cross_run: bool, wrap: bool) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    executor = Executor()
    grading_paths: list[Path] = []

    def access(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            grading_paths.append(kwargs['cwd'])
            assert kwargs['cwd'].parent.name == 'lhm-retained-grading'
            return executor(argv, **kwargs)
        result = executor(argv, **kwargs)
        if executor.calls == 2:
            first_copy = grading_paths[0]
            target = str(first_copy) if absolute else str(first_copy.parent / 'grading-*')
            events = kwargs['stdout'].read_text().splitlines()
            command = f'cat {target}/test_*.py'
            if wrap:
                command = '/bin/zsh -lc ' + shlex.quote(command)
            events.insert(1, json.dumps({'type': 'item.completed', 'item': {
                'type': 'command_execution', 'command': command}}))
            kwargs['stdout'].write_text('\n'.join(events) + '\n')
        return result

    if cross_run:
        value = json.loads(config.read_text())
        value['tasks'] = ['bug-chunk-tail']
        config.write_text(json.dumps(value))
        run(config, out, root, execute=access, version='codex-cli 0.162.0-alpha.17.2')
        value['tasks'] = ['second-task']
        config.write_text(json.dumps(value))
        out = tmp_path / 'second-out'
    report = json.loads(run(config, out, root, execute=access, version='codex-cli 0.162.0-alpha.17.2').read_text())
    second = report['tasks'][-1]
    assert second['grader_access_audit']['status'] == 'access_detected'
    assert second['outcome'] == 'invalid'
    assert second['grading'] is None
    assert report['validity']['status'] == 'invalid'
    assert len(grading_paths) == 1


def test_private_path_never_published_in_checkpoint_or_any_output(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor()

    def leak(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        events = kwargs['stdout'].read_text().splitlines()
        events.insert(1, json.dumps({'type': 'item.completed', 'item': {
            'type': 'command_execution', 'command': f'cat {root}/bug-chunk-tail/*'}}))
        kwargs['stdout'].write_text('\n'.join(events) + '\n')
        return result

    report = json.loads(run(config, out, root, execute=leak, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['grader_access_audit']['status'] == 'access_detected'
    for path in out.rglob('*'):
        if path.is_file():
            assert str(root) not in path.read_text()
            assert str(root.resolve()) not in path.read_text()


def test_stop_e1_retains_checkpoint_and_resumes_all_tasks(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    executor = Executor()

    def fail(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] == 'codex'
        executor(argv, **kwargs)
        return ProcessResult(1)

    with pytest.raises(IncompleteRun, match='after 1 of 2 tasks'):
        run(config, out, root, execute=fail, version='codex-cli 0.162.0-alpha.17.2')
    assert not (out / 'report.json').exists()
    assert (out / 'checkpoint.json').exists()
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    assert diagnostics['attempted_tasks'] == 1
    assert diagnostics['configured_tasks'] == 2
    assert 'STOP-E1' in diagnostics['stop_reason']
    assert executor.calls == 1
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert len(report['tasks']) == 2
    assert executor.calls == 2


def test_cli_incomplete_run_exits_two_without_success_path(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import eval.__main__ as cli
    monkeypatch.setenv('LHM_PRIVATE_GRADERS', '/synthetic/trusted')
    monkeypatch.setattr('sys.argv', ['eval', 'run', '--config', 'config', '--out', 'out'])
    def halted(*args: Any) -> None:
        raise IncompleteRun('STOP-E1: attempted=1, configured=2')
    monkeypatch.setattr(cli, 'run', halted)
    assert cli.main() == 2
    capture = capsys.readouterr()
    assert capture.out == ''
    assert 'STOP-E1: attempted=1, configured=2' in capture.err


def test_taskset_hash_ignores_generated_and_untracked_files(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    import eval.runner.core as core
    from eval.runner.audit import PrivateGraders
    root, _, _ = setup
    private = PrivateGraders.load(root, 'bug-chunk-tail', REPOSITORY)
    tracked = core.public_files('bug-chunk-tail')
    public = tmp_path / 'repository/eval/tasks/bug-chunk-tail'
    import shutil
    shutil.copytree(REPOSITORY / 'eval/tasks/bug-chunk-tail', public)
    monkeypatch.setattr(core, 'REPOSITORY', tmp_path / 'repository')
    monkeypatch.setattr(core.subprocess, 'run', lambda *a, **kw: __import__('subprocess').CompletedProcess(a, 0,
        stdout=b'\0'.join(str(p.relative_to(REPOSITORY)).encode() for p in tracked)+b'\0'))
    before = core.taskset_digest({'bug-chunk-tail': private})
    (public / 'workspace/__pycache__').mkdir()
    (public / 'workspace/__pycache__/generated.pyc').write_bytes(b'generated')
    (public / 'workspace/scratch.py').write_text('generated')
    assert core.taskset_digest({'bug-chunk-tail': private}) == before
    (public / 'prompt.md').write_text('changed specification')
    assert core.taskset_digest({'bug-chunk-tail': private}) != before


def test_reinstruction_has_its_own_transport_retry_budget(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    harness_config(config)
    value = json.loads(config.read_text())
    value['retry_limit'] = 1
    config.write_text(json.dumps(value))
    executor = HarnessExecutor()

    def fail_second(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex' and executor.calls == 2:
            kwargs['stdout'].write_text('{"type":"thread.started","thread_id":"unit-session"}\n{"type":"turn.failed"}\n')
            return ProcessResult(1)
        return result

    report = json.loads(run(config, out, root, execute=fail_second, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.calls == 3
    assert report['tasks'][0]['outcome'] == 'pass'


def test_post_call_usage_invariant_is_internal_error(setup: tuple[Path, Path, Path]) -> None:
    from eval.runner.core import ReportError
    root, config, out = setup
    executor = Executor()

    def bad_usage(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            kwargs['stdout'].write_text(kwargs['stdout'].read_text().replace('"cached_input_tokens": 5', '"cached_input_tokens": 50'))
        return result

    with pytest.raises(ReportError):
        run(config, out, root, execute=bad_usage, version='codex-cli 0.162.0-alpha.17.2')
    assert executor.calls == 1


def test_regrade_matches_live_outcomes_without_source_writes(setup: tuple[Path, Path, Path], tmp_path: Path) -> None:
    from eval.runner import regrade
    from eval.runner.core import audit_roots, workspace_digest
    root, config, out = setup
    executor = Executor()
    original = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    assert entry['workspace_exit_sha256'] == workspace_digest(Path(entry['runtime']) / 'workspace')
    assert entry['segments'][-1]['workspace_exit_sha256'] == entry['workspace_exit_sha256']
    before = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}
    runtime = Path(entry['runtime'])
    retained = {p.relative_to(runtime): p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
    new = tmp_path / 'regraded'

    def only_grader(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] != 'codex', 'Regrade must never call an executor'
        assert not kwargs['cwd'].is_relative_to(out)
        assert kwargs['stdout'].parent != runtime
        assert kwargs['stdout'].parent in audit_roots(runtime)
        return run_process(argv, **kwargs)

    report = json.loads(regrade.regrade(root, out, new, execute=only_grader).read_text())
    assert [t['outcome'] for t in report['tasks']] == [t['outcome'] for t in original['tasks']]
    assert report['metrics'] == original['metrics']
    assert report['accounting'] == original['accounting']
    assert report['tasks'][0]['grading']['copy_path'] != original['tasks'][0]['grading']['copy_path']
    assert report['metadata']['run_id'] != original['metadata']['run_id']
    assert {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()} == before
    assert {p.relative_to(runtime): p.read_bytes() for p in runtime.rglob('*') if p.is_file()} == retained
    diagnostics = json.loads((new / 'run-diagnostics.json').read_text())
    assert diagnostics['source'] == str(out)
    from eval.runner.audit import digest
    assert diagnostics['source_report_sha256'] == digest((out / 'report.json').read_bytes())
    assert diagnostics['workspace_hash_checks'][0]['matched'] is True
    assert set(diagnostics['audit_code_version']) == {'audit.py', 'javascript.py', 'regrade.py'}


@pytest.mark.parametrize('case', ['changed', 'missing_hash', 'nested_output', 'source_output'])
def test_regrade_refuses_unpinned_workspace_and_source_output(setup: tuple[Path, Path, Path],
                                                            tmp_path: Path, case: str) -> None:
    from eval.runner import regrade
    root, config, out = setup
    run(config, out, root, execute=Executor(), version='codex-cli 0.162.0-alpha.17.2')
    state_path = out / 'checkpoint.json'
    state = json.loads(state_path.read_text())
    entry = state['tasks']['bug-chunk-tail']
    if case == 'changed':
        (Path(entry['runtime']) / 'workspace/chunking.py').write_text('# modified after executor exit\n')
    elif case == 'missing_hash':
        entry.pop('workspace_exit_sha256')
        state_path.write_text(json.dumps(state))
    destination = out if case == 'source_output' else out / 'nested' if case == 'nested_output' else tmp_path / 'new'
    before = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Refusal must precede any grading')

    with pytest.raises(ValueError, match='hash mismatch' if case == 'changed' else
                       'exit hash missing' if case == 'missing_hash' else 'fresh output'):
        regrade.regrade(root, out, destination, execute=forbidden)
    assert {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()} == before
    if destination != out:
        assert not destination.exists()


def test_regrade_recovers_every_task_after_parser_fix(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """Historical inconclusive tasks gain the same grades as a current live fixture."""
    from eval.runner import core, regrade
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    original_audit = core.audit_logs

    def historical_parser(*args: Any, **kwargs: Any) -> dict[str, Any]:
        audit = original_audit(*args, **kwargs)
        if any('sessions' in str(path) for path in args[0]):
            audit['status'] = 'inconclusive'
            audit['errors'].append('unresolved_custom_input:synthetic-historical-parser')
        return audit

    monkeypatch.setattr(core, 'audit_logs', historical_parser)
    historical = json.loads(run(config, out, root, execute=Executor(), version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert [t['outcome'] for t in historical['tasks']] == ['invalid', 'invalid']
    monkeypatch.setattr(core, 'audit_logs', original_audit)
    live = json.loads(run(config, tmp_path / 'live', root, execute=Executor(),
                          version='codex-cli 0.162.0-alpha.17.2').read_text())
    calls = []

    def only_grade(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] != 'codex'
        calls.append(argv)
        return run_process(argv, **kwargs)

    result = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=only_grade).read_text())
    assert len(calls) == 2
    assert [t['outcome'] for t in result['tasks']] == [t['outcome'] for t in live['tasks']] == ['pass', 'pass']
    assert result['metrics'] == live['metrics']
    assert result['accounting'] == live['accounting']


def test_regrade_cli_prints_only_destination(monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    from eval.runner import regrade
    monkeypatch.setattr('sys.argv', ['regrade', '--private-root', '/synthetic-private',
                                     '--from', 'source', '--out', 'new'])
    monkeypatch.setattr(regrade, 'regrade', lambda *args: Path('new/report.json'))
    assert regrade.main() == 0
    assert capsys.readouterr().out == 'new\n'


def test_regrade_cli_missing_hash_is_clear_and_sanitized(monkeypatch: pytest.MonkeyPatch,
                                                        capsys: pytest.CaptureFixture[str]) -> None:
    from eval.runner import regrade
    monkeypatch.setattr('sys.argv', ['regrade', '--private-root', '/synthetic-private',
                                     '--from', 'source', '--out', 'new'])

    def missing(*args: Any) -> Path:
        raise ValueError('Regrade refused: runner-recorded workspace exit hash missing; rerun the executor on the host')

    monkeypatch.setattr(regrade, 'regrade', missing)
    assert regrade.main() == 1
    captured = capsys.readouterr()
    assert captured.out == '' and 'workspace exit hash missing' in captured.err
    assert '/synthetic-private' not in captured.err


def two_session_config(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                       tmp_path: Path, *, harness_on: bool = False) -> tuple[Path, Path, Path]:
    """Use only synthetic mutable public inputs and private graders."""
    from eval.runner import core
    root, config, out = setup
    if harness_on:
        monkeypatch.setattr(core, 'require_call_estimate', lambda *args: None)
    two_task_config(root, config, monkeypatch, tmp_path)
    public = core.REPOSITORY / 'eval/tasks/bug-chunk-tail'
    meta = json.loads((public / 'meta.json').read_text())
    meta['two_session'] = True
    (public / 'meta.json').write_text(json.dumps(meta))
    (public / 'day2.md').write_bytes(b'Finish using the workspace.\r\nNo day-one restatement.\r\n')
    value = json.loads(config.read_text())
    value.update(tasks=['bug-chunk-tail'], harness=harness_on,
                 control_backend='codex_cli' if harness_on else 'none', reinstruction_limit=0)
    value['task_timeout_seconds'] = {'bug-chunk-tail': 900}
    config.write_text(json.dumps(value))
    return root, config, out


class TwoSessionExecutor(Executor):
    """Mock both fresh sessions and all frozen controller/verifier operations."""

    def __init__(self, *, leak_day: int = 0, native_leak: bool = False,
                 missing_observation: bool = False, invalid_handoff: bool = False,
                 missing_native_day: int = 0, day2_fail: bool = False) -> None:
        super().__init__()
        self.leak_day = leak_day
        self.native_leak = native_leak
        self.missing_observation = missing_observation
        self.invalid_handoff = invalid_handoff
        self.missing_native_day = missing_native_day
        self.day2_fail = day2_fail
        self.operations: list[str] = []
        self.workspaces: list[Path] = []
        self.prompts: list[str] = []
        self.grades = 0

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            self.operations.append(operation)
            assert kwargs['env']['HARNESS_NESTED'] == '1'
            assert 'LHM_PRIVATE_GRADERS' not in kwargs['env']
            assert self.grades == 0
            dest = Path(argv[argv.index('--handoff') + 1] if operation == 'validate-handoff'
                        else argv[argv.index('--out') + 1])
            if operation == 'contract':
                handoff_path = argv[argv.index('--handoff') + 1]
                if self.calls:
                    assert self.operations[-3:] == ['handoff', 'validate-handoff', 'contract']
                    assert handoff_path != 'none' and Path(handoff_path).is_file()
                    assert Path(argv[argv.index('--prompt') + 1]).name == 'day2.md'
                else:
                    assert handoff_path == 'none'
                value = {'task_summary': 'Repair chunk tail', 'constraints': [],
                         'success_criteria': [{'id': 'SC-1', 'description': 'Fix tail',
                                              'check': {'type': 'file_exists', 'path': 'chunking.py'}}],
                         'verification': [], 'stop_conditions': [], 'assumptions': [],
                         'reasoning_effort': {'value': 'medium', 'rationale': 'Fixture'},
                         'cost_estimate': {'input_tokens': 10, 'output_tokens': 10, 'usd': .01}}
            elif operation == 'check':
                value = {'items': [{'id': 'SC-1', 'status': 'pass', 'evidence': 'fixture', 'reason': 'ok'}],
                         'overall': 'pass', 'reinstruct_message': None, 'attempt': 1}
            elif operation == 'handoff':
                assert self.calls == 1
                assert Path(argv[argv.index('--contract') + 1]).parent.name == 'day-1'
                assert Path(argv[argv.index('--verdict') + 1]).is_file()
                transcript = Path(argv[argv.index('--transcript') + 1]).read_text()
                assert 'day-2' not in transcript
                value = {'done': [], 'remaining': [], 'decisions': [], 'verify_commands': [], 'do_not_touch': []}
            else:
                assert operation == 'validate-handoff' and '--out' not in argv
                assert self.calls == 1
                if self.invalid_handoff:
                    kwargs['stdout'].write_text('')
                    kwargs['stderr'].write_text('invalid handoff')
                    return ProcessResult(1)
                value = json.loads(dest.read_text())
            dest.write_text(json.dumps(value))
            kwargs['stdout'].write_text(str(dest) + '\n')
            kwargs['stderr'].write_text('')
            return ProcessResult(0)
        if argv[0] != 'codex':
            assert self.calls == 2, 'Grading must follow day 2'
            self.grades += 1
            return super().__call__(argv, **kwargs)
        assert 'resume' not in argv, 'Day 2 must be a new session'
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        assert kwargs['timeout'] == 900
        self.workspaces.append(kwargs['cwd'])
        self.prompts.append(kwargs['stdin'])
        if self.calls:
            assert self.workspaces[0] == kwargs['cwd']
            assert (kwargs['cwd'] / 'HANDOFF.md').read_text() == 'Executor-authored context'
            from eval.runner import core
            assert kwargs['stdin'].encode() == (core.REPOSITORY / 'eval/tasks/bug-chunk-tail/day2.md').read_bytes()
            if self.operations:
                assert any(v.startswith('developer_instructions=') for v in argv)
            else:
                assert not any(v.startswith('developer_instructions=') for v in argv)
        result = super().__call__(argv, **kwargs)
        events = kwargs['stdout'].read_text().replace('unit-session', f'day-{self.calls}')
        if self.calls == self.leak_day and not self.native_leak:
            lines = events.splitlines()
            lines.insert(1, json.dumps({'type': 'item.completed', 'item': {
                'type': 'command_execution', 'command': 'cat test_private_synthetic.py'}}))
            events = '\n'.join(lines) + '\n'
        kwargs['stdout'].write_text(events)
        native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
        if self.calls == self.leak_day and self.native_leak:
            with native.open('a') as handle:
                handle.write(json.dumps({'type': 'response_item', 'payload': {'type': 'function_call',
                    'name': 'exec_command', 'arguments': json.dumps({'cmd': 'cat test_private_synthetic.py'})}}) + '\n')
        native.write_text(native.read_text().replace('unit-session', f'day-{self.calls}'))
        # Separate native logs reflect distinct fresh sessions and cannot overwrite day 1.
        native.rename(native.with_name(f'rollout-day-{self.calls}.jsonl'))
        if self.calls == self.missing_native_day:
            native.with_name(f'rollout-day-{self.calls}.jsonl').write_text('')
        (kwargs['cwd'] / 'HANDOFF.md').write_text('Executor-authored context')
        if self.calls == 2 and self.missing_observation:
            (kwargs['stdout'].parent / 'day2-delivered.md').rename(kwargs['stdout'].parent / 'unavailable.md')
        if self.calls == 2 and self.day2_fail:
            (kwargs['cwd'] / 'chunking.py').write_text('def chunked(items, size): return []\n')
        return result


def test_two_session_baseline_exact_prompt_costs_and_regrade(setup: tuple[Path, Path, Path],
                                                           monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from eval.runner import core, regrade
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor()
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['two_session']
    assert task['attempts'] == 2 and executor.grades == 1
    assert report['metrics']['avg_attempts']['value'] == 2
    assert report['metrics']['handoff_success']['value'] == 1
    assert report['accounting']['total_cost_usd'] == pytest.approx(2 * .0001105)
    assert task['costs']['control_usd'] == 0 and len(task['calls']) == 2
    assert executor.operations == []
    assert executor.prompts[0] == (core.REPOSITORY / 'eval/tasks/bug-chunk-tail/prompt.md').read_text()
    observation = json.loads(Path(task['handoff']['evidence']['path']).read_text())
    assert observation['delivered_sha256'] == observation['public_sha256']
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    assert all(len(s['workspace_exit_sha256']) == 64 for s in entry['segments'])
    assert entry['workspace_exit_sha256'] == core.workspace_digest(Path(entry['runtime']) / 'workspace')
    new = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=executor).read_text())
    assert executor.calls == 2 and executor.grades == 2
    assert new['metrics'] == report['metrics'] and new['accounting'] == report['accounting']
    assert new['tasks'][0]['handoff']['evidence']['path'] != task['handoff']['evidence']['path']


@pytest.mark.parametrize('day', [1, 2])
@pytest.mark.parametrize('native', [False, True])
def test_access_in_either_session_blocks_grading(setup: tuple[Path, Path, Path],
                                               monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                               day: int, native: bool) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor(leak_day=day, native_leak=native)
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'invalid'
    assert report['tasks'][0]['grader_access_audit']['status'] == 'access_detected'
    assert report['tasks'][0]['grading'] is None and executor.grades == 0
    assert executor.calls == day
    assert report['validity']['status'] == 'invalid'


@pytest.mark.parametrize('options', [{'missing_observation': True}, {'missing_native_day': 2}])
def test_missing_day2_evidence_is_invalid(setup: tuple[Path, Path, Path],
                                        monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                        options: dict[str, Any]) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor(**options)
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'invalid' and executor.grades == 0
    assert report['metrics']['handoff_success']['sample_size'] == 0


@pytest.mark.parametrize('invalid', [False, True])
def test_harness_generates_validates_and_passes_handoff(setup: tuple[Path, Path, Path],
                                                      monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                      invalid: bool) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor(invalid_handoff=invalid)
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.operations == (['contract', 'check', 'handoff', 'validate-handoff'] if invalid else
                                   ['contract', 'check', 'handoff', 'validate-handoff', 'contract', 'check'])
    assert executor.calls == (1 if invalid else 2)
    assert report['tasks'][0]['outcome'] == ('invalid' if invalid else 'pass')
    assert report['tasks'][0]['costs']['control_usd'] is None


def test_two_session_failure_is_eligible_handoff_failure(setup: tuple[Path, Path, Path],
                                                       monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    report = json.loads(run(config, out, root, execute=TwoSessionExecutor(day2_fail=True),
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'fail'
    assert report['metrics']['handoff_success']['sample_size'] == 1
    assert report['metrics']['handoff_success']['value'] == 0
    assert report['tasks'][0]['handoff']['day2_pass'] is False


@pytest.mark.parametrize('case', ['day1_hash', 'prompt_hash', 'same_session'])
def test_two_session_regrade_refuses_missing_or_changed_provenance(setup: tuple[Path, Path, Path],
                                                                  monkeypatch: pytest.MonkeyPatch,
                                                                  tmp_path: Path, case: str) -> None:
    from eval.runner import regrade
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    run(config, out, root, execute=TwoSessionExecutor(), version='codex-cli 0.162.0-alpha.17.2')
    checkpoint = out / 'checkpoint.json'
    state = json.loads(checkpoint.read_text())
    entry = state['tasks']['bug-chunk-tail']
    if case == 'day1_hash':
        entry['segments'][0].pop('workspace_exit_sha256')
    elif case == 'prompt_hash':
        Path(entry['day2_observation']['prompt_path']).write_text('restated day-one context')
    else:
        entry['day2_observation']['attempt'] = 1
    checkpoint.write_text(json.dumps(state))
    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Invalid provenance must be rejected before grading')
    with pytest.raises(ValueError):
        regrade.regrade(root, out, tmp_path / 'regraded', execute=forbidden)
    assert not (tmp_path / 'regraded').exists()


def test_two_session_grading_recovery_never_reexecutes(setup: tuple[Path, Path, Path],
                                                     monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor()
    def interrupted_grading(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            raise RuntimeError('Interrupted grading')
        return executor(argv, **kwargs)
    with pytest.raises(RuntimeError, match='Interrupted grading'):
        run(config, out, root, execute=interrupted_grading, version='codex-cli 0.162.0-alpha.17.2')
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.calls == 2 and executor.grades == 1
    assert report['tasks'][0]['outcome'] == 'pass'


def test_two_session_boundary_recovery_starts_fresh_day2(setup: tuple[Path, Path, Path],
                                                       monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor()
    def interrupted_handoff(argv: list[str], **kwargs: Any) -> ProcessResult:
        if 'handoff' in argv:
            raise KeyboardInterrupt
        return executor(argv, **kwargs)
    with pytest.raises(KeyboardInterrupt):
        run(config, out, root, execute=interrupted_handoff, version='codex-cli 0.162.0-alpha.17.2')
    assert executor.calls == 1
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.calls == 2 and report['tasks'][0]['outcome'] == 'pass'


@pytest.mark.parametrize('harness_on', [False, True])
@pytest.mark.parametrize('process', [ProcessResult(-9, timed_out=True), ProcessResult(1)])
def test_clean_day1_failure_still_runs_day2(setup: tuple[Path, Path, Path],
                                          monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                          harness_on: bool, process: ProcessResult) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=harness_on)
    executor = TwoSessionExecutor()

    def fail_day1(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        return process if argv[0] == 'codex' and executor.calls == 1 else result

    report = json.loads(run(config, out, root, execute=fail_day1,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert executor.calls == 2 and executor.grades == 1
    assert task['outcome'] == 'pass' and task['invalid_reasons'] == []
    assert task['executor_segments'][0]['exit_code'] == process.returncode
    result = json.loads((out / 'bug-chunk-tail/result.json').read_text())
    assert result['segments'][0]['timed_out'] == process.timed_out
    assert report['metrics']['handoff_success']['sample_size'] == 1


@pytest.mark.parametrize('harness_on', [False, True])
@pytest.mark.parametrize('attack', ['files', 'symlink', 'invalid'])
def test_workspace_cannot_publish_control_evidence(setup: tuple[Path, Path, Path],
                                                 monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                 harness_on: bool, attack: str) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=harness_on)
    executor = TwoSessionExecutor(leak_day=1 if attack == 'invalid' else 0)
    secret = tmp_path / 'synthetic-secret'
    secret.write_text('SYNTHETIC SECRET MUST NOT BE PUBLISHED')

    def forge(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            workspace = kwargs['cwd']
            for day in ('day-1', 'day-2'):
                folder = workspace / day
                folder.mkdir(exist_ok=True)
                for name in ('contract.json', 'verdict-1.json', 'contract.stdout', 'verdict-1.stderr'):
                    (folder / name).write_text('FORGED WORKSPACE CONTROL')
            (workspace / 'handoff.json').write_text('FORGED WORKSPACE CONTROL')
            if attack == 'symlink' and executor.calls == 1:
                (workspace / 'verdict-99.json').symlink_to(secret)
        return result

    run(config, out, root, execute=forge, version='codex-cli 0.162.0-alpha.17.2')
    task_out = out / 'bug-chunk-tail'
    controls = [p for p in task_out.iterdir() if p.is_file() and
                any(word in p.name for word in ('contract', 'verdict', 'handoff'))]
    for path in controls:
        assert 'FORGED WORKSPACE CONTROL' not in path.read_text()
        assert 'SYNTHETIC SECRET' not in path.read_text()
    assert not (task_out / 'verdict-99.json').exists()
    if not harness_on:
        assert not any('contract' in p.name or 'verdict' in p.name for p in controls)
    elif attack != 'invalid':
        assert json.loads((task_out / 'day-1-contract.json').read_text())['task_summary'] == 'Repair chunk tail'
        assert json.loads((task_out / 'day-2-verdict-1.json').read_text())['overall'] == 'pass'
    if attack in {'invalid', 'symlink'}:
        assert not (task_out / 'workspace').exists()


@pytest.mark.parametrize('target', ['day-2/contract.json', 'handoff.json', 'day-1/verdict-1.json',
                                    'day-1/contract.json', 'day-2', 'day-1/verdict-1.stdout'])
def test_executor_cannot_supply_runner_control_inputs(setup: tuple[Path, Path, Path],
                                                     monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                     target: str) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor()
    external = tmp_path / 'executor-directory'
    external.mkdir()
    selected = []

    def forge(argv: list[str], **kwargs: Any) -> ProcessResult:
        if '-m' in argv and argv[argv.index('-m') + 2] == 'handoff':
            selected.append(Path(argv[argv.index('--verdict') + 1]).name)
        result = executor(argv, **kwargs)
        if argv[0] == 'codex' and executor.calls == 1:
            if target == 'day-2/contract.json':
                (kwargs['cwd'].parent / 'day-1/verdict-99.json').write_text('{"forged": true}')
            path = kwargs['cwd'].parent / target
            path.parent.mkdir(exist_ok=True)
            if target == 'day-2':
                path.symlink_to(external, target_is_directory=True)
            else:
                path.write_text('{"executor_supplied": true}')
        return result

    report = json.loads(run(config, out, root, execute=forge,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.calls == 1 and executor.grades == 0
    assert report['tasks'][0]['outcome'] == 'invalid'
    assert 'control_cli_error' in report['tasks'][0]['invalid_reasons']
    if target in {'day-2/contract.json', 'handoff.json', 'day-1/verdict-1.json',
                  'day-2', 'day-1/verdict-1.stdout'}:
        assert 'runner_control_file_preexisting' in report['tasks'][0]['invalid_reasons']
    if target == 'day-2/contract.json':
        assert selected == ['verdict-1.json']
    assert executor.operations.count('contract') == 1
    assert 'executor_supplied' not in ''.join(p.read_text() for p in (out / 'bug-chunk-tail').iterdir()
                                             if p.is_file() and 'contract' in p.name)


@pytest.mark.parametrize('two', [False, True])
@pytest.mark.parametrize('process', [ProcessResult(-9, timed_out=True), ProcessResult(1)])
def test_regrade_preserves_executor_failure_class(setup: tuple[Path, Path, Path],
                                                 monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                                                 two: bool, process: ProcessResult) -> None:
    from eval.runner import regrade
    root, config, out = two_session_config(setup, monkeypatch, tmp_path) if two else setup
    executor = TwoSessionExecutor() if two else Executor()

    def fail_final(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        return process if argv[0] == 'codex' and executor.calls == (2 if two else 1) else result

    with pytest.raises(IncompleteRun):
        run(config, out, root, execute=fail_final, version='codex-cli 0.162.0-alpha.17.2')
    original = json.loads(run(config, out, root, execute=fail_final,
                              version='codex-cli 0.162.0-alpha.17.2').read_text())

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        pytest.fail('Failed executor sessions must not be graded into a pass')

    report = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=forbidden).read_text())
    assert report['tasks'][0]['outcome'] == original['tasks'][0]['outcome'] == (
        'timeout' if process.timed_out else 'error')
    assert report['tasks'][0]['grading'] is None
    if two:
        assert report['tasks'][0]['handoff']['day2_pass'] is False
        assert report['metrics']['handoff_success']['value'] == 0


def test_regrade_keeps_preday2_invalid_task_and_grades_rest(setup: tuple[Path, Path, Path],
                                                         monkeypatch: pytest.MonkeyPatch,
                                                         tmp_path: Path) -> None:
    from eval.runner import regrade
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    value = json.loads(config.read_text())
    value['tasks'].append('second-task')
    config.write_text(json.dumps(value))
    bad, good = TwoSessionExecutor(leak_day=1), Executor()

    def route(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            return run_process(argv, **kwargs)
        state = json.loads((out / 'checkpoint.json').read_text())
        task = next(t for t, e in state['tasks'].items() if Path(e['runtime']) == kwargs['cwd'].parent)
        return (bad if task == 'bug-chunk-tail' else good)(argv, **kwargs)

    run(config, out, root, execute=route, version='codex-cli 0.162.0-alpha.17.2')
    grades = []

    def only_grade(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] != 'codex'
        grades.append(kwargs['cwd'])
        return run_process(argv, **kwargs)

    report = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=only_grade).read_text())
    tasks = {t['task_id']: t for t in report['tasks']}
    assert tasks['bug-chunk-tail']['outcome'] == 'invalid'
    assert tasks['bug-chunk-tail']['grading'] is None
    assert tasks['second-task']['outcome'] == 'pass'
    assert len(grades) == 1 and bad.calls == good.calls == 1
    assert report['validity']['status'] == 'invalid'


@pytest.mark.parametrize('day', [1, 2])
def test_hard_crash_segment_recovers_without_repeating_finished_day(setup: tuple[Path, Path, Path],
                                                                  monkeypatch: pytest.MonkeyPatch,
                                                                  tmp_path: Path, day: int) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor()

    def crash(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex' and executor.calls + 1 == day:
            kwargs['stdout'].write_text(json.dumps({'type': 'thread.started', 'thread_id': 'crashed'}) + '\n')
            raise RuntimeError('hard runner crash')
        return executor(argv, **kwargs)

    with pytest.raises(RuntimeError, match='hard runner crash'):
        run(config, out, root, execute=crash, version='codex-cli 0.162.0-alpha.17.2')
    before = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert 'exit_code' not in before['segments'][-1]
    calls = []

    def resumed(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] == 'codex', 'Incomplete historical evidence must prevent grading'
        calls.append(argv)
        # Use a small transport mock that accepts resume and emits distinct ids.
        result = Executor.__call__(executor, argv, **kwargs)
        if 'resume' not in argv:
            kwargs['stdout'].write_text(kwargs['stdout'].read_text().replace('unit-session', 'fresh-day2'))
        return result

    report = json.loads(run(config, out, root, execute=resumed,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert 'resume' in calls[0] and 'crashed' in calls[0]
    assert len(calls) == (2 if day == 1 else 1)
    assert report['tasks'][0]['outcome'] == 'invalid'
    state = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert state['segments'][day - 1]['interrupted'] is True
    if day == 2:
        assert state['segments'][0] == before['segments'][0]


def test_paid_call_guard_includes_two_day_control_and_fallbacks(setup: tuple[Path, Path, Path],
                                                              monkeypatch: pytest.MonkeyPatch,
                                                              tmp_path: Path,
                                                              capsys: pytest.CaptureFixture[str]) -> None:
    from eval.runner import core
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    value = json.loads(config.read_text())
    value.update(harness=True, control_backend='codex_cli')
    assert core.paid_call_bound(value) == 11  # 2 exec + 6 contract + 3 handoff
    config.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='STOP-3.*11'):
        load_config(config)
    value.update(tasks=['second-task'], task_timeout_seconds={})
    assert core.paid_call_bound(value, {'second-task:1': 2}) == 10
    config.write_text(json.dumps(value))
    load_config(config)
    assert 'at most 4 calls' in capsys.readouterr().err
    with pytest.raises(ValueError, match='STOP-3.*10'):
        core.require_call_estimate(value, {'second-task:1': 2})
    value.update(retry_limit=1, reinstruction_limit=1, tasks=['bug-chunk-tail'])
    assert core.paid_call_bound(value, {'bug-chunk-tail:1': 2, 'bug-chunk-tail:2': 1}) == 35


def test_version_change_halts_before_day2_and_is_resumable(setup: tuple[Path, Path, Path],
                                                        monkeypatch: pytest.MonkeyPatch,
                                                        tmp_path: Path) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    executor = TwoSessionExecutor()
    versions = iter(['codex-cli 0.162.0-alpha.17.2'] * 2 + ['codex-cli 0.163.0-alpha.11.1'])
    with pytest.raises(IncompleteRun, match='version changed'):
        run(config, out, root, execute=executor, version=lambda: next(versions))
    assert executor.calls == 1 and not (out / 'report.json').exists()
    state = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert state['completed_days'] == [1] and state['active_day'] == 2
    with pytest.raises(IncompleteRun, match='version changed'):
        run(config, out, root, execute=executor, version='codex-cli 0.163.0-alpha.11.1')
    report = json.loads(run(config, out, root, execute=executor,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert executor.calls == 2 and report['tasks'][0]['outcome'] == 'pass'


def test_report_rejects_native_version_mismatch_and_missing_evidence(setup: tuple[Path, Path, Path]) -> None:
    from eval.runner.audit import digest
    from eval.runner.report import build, validate
    root, config, out = setup
    report = json.loads(run(config, out, root, execute=Executor(),
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    native = next(a for a in report['tasks'][0]['artifacts'] if '/sessions/' in a['path'])
    path = Path(native['path'])
    original = path.read_text()
    path.write_text(original.replace('0.162.0-alpha.17.2', '0.163.0-alpha.11.1'))
    native['sha256'] = digest(path.read_bytes())
    with pytest.raises(ValueError, match='mismatched_cli_version_evidence'):
        validate(report, REPOSITORY)
    rebuilt = build(json.loads(config.read_text()), json.loads((out / 'checkpoint.json').read_text()),
                    json.loads(json.dumps(report['tasks'])), report['metadata']['codex_version'], REPOSITORY)
    assert rebuilt['tasks'][0]['outcome'] == 'invalid'
    assert rebuilt['tasks'][0]['grading'] is None
    assert 'mismatched_cli_version_evidence' in rebuilt['tasks'][0]['invalid_reasons']
    path.write_text('\n'.join(line for line in original.splitlines() if 'session_meta' not in line) + '\n')
    native['sha256'] = digest(path.read_bytes())
    with pytest.raises(ValueError, match='missing_cli_version_evidence'):
        validate(report, REPOSITORY)
    rebuilt = build(json.loads(config.read_text()), json.loads((out / 'checkpoint.json').read_text()),
                    report['tasks'], report['metadata']['codex_version'], REPOSITORY)
    assert rebuilt['tasks'][0]['outcome'] == 'invalid'
    assert rebuilt['tasks'][0]['grading'] is None
    assert 'missing_cli_version_evidence' in rebuilt['tasks'][0]['invalid_reasons']


def test_report_comparison_refuses_mixed_codex_versions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
    from eval.runner import compare_versions
    reports = [tmp_path / 'a.json', tmp_path / 'b.json']
    for path in reports:
        path.write_text(json.dumps({'metadata': {'codex_version': 'codex-cli 0.162.0-alpha.17.2'}}))
    monkeypatch.setattr('sys.argv', ['compare_versions', *map(str, reports)])
    assert compare_versions.main() == 0
    assert capsys.readouterr().out.strip() == 'codex-cli 0.162.0-alpha.17.2'
    reports[1].write_text(json.dumps({'metadata': {'codex_version': 'codex-cli 0.163.0-alpha.11.1'}}))
    assert compare_versions.main() == 1
    captured = capsys.readouterr()
    assert captured.out == '' and 'different codex_version' in captured.err


@pytest.mark.parametrize('damage', ['missing_meta', 'missing_field', 'mismatch'])
def test_native_version_failure_invalidates_only_affected_task(setup: tuple[Path, Path, Path],
                                                             monkeypatch: pytest.MonkeyPatch,
                                                             tmp_path: Path, damage: str) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    executor = Executor()
    grades = []

    def damaged(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            grades.append(kwargs['cwd'])
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            state = json.loads((out / 'checkpoint.json').read_text())
            entry = state['tasks'].get('bug-chunk-tail')
            if entry and Path(entry['runtime']) == kwargs['cwd'].parent:
                native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
                events = [json.loads(line) for line in native.read_text().splitlines()]
                if damage == 'missing_meta':
                    events = events[1:]
                elif damage == 'missing_field':
                    events[0]['payload'].pop('cli_version')
                else:
                    events[0]['payload']['cli_version'] = '0.163.0-alpha.11.1'
                native.write_text(''.join(json.dumps(event) + '\n' for event in events))
        return result

    report = json.loads(run(config, out, root, execute=damaged,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    tasks = {task['task_id']: task for task in report['tasks']}
    invalid = tasks['bug-chunk-tail']
    assert invalid['outcome'] == 'invalid' and invalid['grading'] is None
    reason = 'mismatched_cli_version_evidence' if damage == 'mismatch' else 'missing_cli_version_evidence'
    assert reason in invalid['invalid_reasons']
    assert tasks['second-task']['outcome'] == 'pass'
    assert executor.calls == 2 and len(grades) == 1
    assert report['accounting']['invalid_tasks'] == report['accounting']['valid_tasks'] == 1
    assert report['accounting']['total_cost_usd'] == pytest.approx(.000221)
    assert report['validity']['status'] == 'invalid'


@pytest.mark.parametrize('name', ['verdict-99.json', 'verdict-final.json'])
def test_handoff_ignores_unowned_verdict_files(setup: tuple[Path, Path, Path],
                                             monkeypatch: pytest.MonkeyPatch,
                                             tmp_path: Path, name: str) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor()
    selected = []

    def forge(argv: list[str], **kwargs: Any) -> ProcessResult:
        if '-m' in argv and argv[argv.index('-m') + 2] == 'handoff':
            selected.append(Path(argv[argv.index('--verdict') + 1]).name)
        result = executor(argv, **kwargs)
        if argv[0] == 'codex' and executor.calls == 1:
            (kwargs['cwd'].parent / 'day-1' / name).write_text('{"forged": true}')
        return result

    report = json.loads(run(config, out, root, execute=forge,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert selected == ['verdict-1.json'] and executor.calls == 2
    assert not (out / 'bug-chunk-tail' / ('day-1-' + name)).exists()


def test_handoff_ignores_nonnumeric_verdict_even_in_manifest(tmp_path: Path) -> None:
    from eval.runner import harness
    runtime = tmp_path / 'runtime'
    day1 = runtime / 'day-1'
    day1.mkdir(parents=True)
    (day1 / 'verdict-final.json').write_text('{}')
    (day1 / 'verdict-1.json').write_text('{}')
    guard = harness.ControlFiles(runtime, {}, lambda: None)
    guard.remember(day1 / 'verdict-final.json')
    guard.remember(day1 / 'verdict-1.json')
    selected = []

    def invoke(module: str, operation: str, arguments: list[str], *args: Any, **kwargs: Any) -> dict[str, Any]:
        if operation == 'handoff':
            selected.append(Path(arguments[arguments.index('--verdict') + 1]).name)
        return {}

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(harness, 'invoke', invoke)
        harness.handoff(day1, runtime, [], {'control_backend': 'codex_cli', 'timeout_seconds': 30},
                        repository=REPOSITORY,
                        execute=lambda *a, **kw: ProcessResult(0), guard=guard)
    assert selected == ['verdict-1.json']
