"""Mock executor behavior and prove grading occurs only after termination."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.core import REPOSITORY, load_config, run
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
        (session / "rollout-unit.jsonl").write_text(json.dumps({"type": "turn_context", "payload": {"model": "gpt-6.1-sol", "effort": "medium"}}) + "\n")
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


def test_baseline_grades_after_exit_and_completed_checkpoint_does_not_repeat(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor()
    report = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    result = report["tasks"][0]
    assert result["outcome"] == "pass"
    assert result["grading"]["passed_tests"] == 3
    assert result["grader_access_audit"]["status"] == "clean"
    assert result["calls"][0]["usage"]["usd"] is None
    assert report["accounting"]["total_cost_usd"] is None
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


def test_interrupted_turn_resumes_same_session_before_grading(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor(interrupt=True)
    first = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert first["tasks"][0]["grading"] is None
    assert first["tasks"][0]["outcome"] == "invalid"
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
    from eval.runner.report import validate
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
    # Report git provenance is read from the original repository, never a model.
    original_build = core.build
    monkeypatch.setattr(core, 'build', lambda c, s, t, v, r, **kw: original_build(c, s, t, v, REPOSITORY, **kw))


@pytest.mark.parametrize('absolute', [False, True])
@pytest.mark.parametrize('cross_run', [False, True])
def test_previous_grading_copy_access_invalidates(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch, absolute: bool, cross_run: bool) -> None:
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
            events.insert(1, json.dumps({'type': 'item.completed', 'item': {
                'type': 'command_execution', 'command': f'cat {target}/test_*.py'}}))
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


@pytest.mark.xfail(strict=True, reason="STOP-1: frozen schema requires valid when no task is invalid; aggregate-only halt invalidity needs Role 1 revision")
def test_stop_e1_partial_report_is_invalid_with_counts(setup: tuple[Path, Path, Path], tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    executor = Executor()

    def fail(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv[0] == 'codex'
        executor(argv, **kwargs)
        return ProcessResult(1)

    report = json.loads(run(config, out, root, execute=fail, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['validity']['status'] == 'invalid'
    assert any('STOP-E1' in reason and 'after 1 of 2 tasks' in reason for reason in report['validity']['reasons'])
    assert 'after 1 of 2 tasks' in capsys.readouterr().err
    assert executor.calls == 1


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
