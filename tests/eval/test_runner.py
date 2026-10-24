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
        if not any(v.startswith('service_tier=') for v in argv):
            fixture = Path(__file__).parent / 'fixtures/native-session-0.163.jsonl'
            applied = next(json.loads(line) for line in fixture.read_text().splitlines()
                           if json.loads(line).get('payload', {}).get('type') == 'thread_settings_applied')
            applied['ordinal'] = self.calls
            applied['payload']['thread_id'] = 'unit-session'
            applied['payload']['thread_settings']['service_tier'] = 'standard'
            with (session / "rollout-unit.jsonl").open('a') as stream:
                stream.write(json.dumps(applied) + '\n')
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
    # Only the interrupted stream's missing terminal is exempted.
    assert second["tasks"][0]["outcome"] == "pass"
    assert second["tasks"][0]["grader_access_audit"]["status"] == "clean"
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


@pytest.mark.parametrize("with_session", [False, True])
def test_executor_usage_limit_halts_without_outcome_and_resumes(setup: tuple[Path, Path, Path],
                                                               with_session: bool) -> None:
    root, config, out = setup
    value = json.loads(config.read_text())
    value["retry_limit"] = 1
    config.write_text(json.dumps(value))
    executor = Executor()
    limited_calls = 0
    fixture = Path(__file__).parent / "fixtures/usage-limit.jsonl"
    message = json.loads(fixture.read_text().splitlines()[0])["message"]

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal limited_calls
        assert argv[0] == "codex", "Usage limits must stop before grading or another call"
        limited_calls += 1
        if with_session:
            executor(argv, **kwargs)
        prefix = '{"type":"thread.started","thread_id":"unit-session"}\n' if with_session else ""
        kwargs["stdout"].write_text(prefix + fixture.read_text())
        kwargs["stderr"].write_text("")
        return ProcessResult(1)

    with pytest.raises(IncompleteRun, match="usage limit") as stopped:
        run(config, out, root, execute=limited, version="codex-cli 0.162.0-alpha.17.2")
    assert message in str(stopped.value)
    assert limited_calls == 1
    assert not (out / "report.json").exists()
    assert not (out / "bug-chunk-tail/result.json").exists()
    entry = json.loads((out / "checkpoint.json").read_text())["tasks"]["bug-chunk-tail"]
    assert entry["phase"] == "usage_limited" and "result" not in entry
    assert entry.get("transport_retries", 0) == 0
    assert not list(Path(entry["runtime"]).glob("grading-*"))
    assert (out / "bug-chunk-tail/exec-1.jsonl").read_text().endswith(fixture.read_text())
    assert message in json.loads((out / "run-diagnostics.json").read_text())["stop_reason"]

    def recovered(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == "codex":
            assert ("resume" in argv) == with_session
        return executor(argv, **kwargs)

    report = json.loads(run(config, out, root, execute=recovered, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert report["tasks"][0]["outcome"] == "pass"
    assert report["tasks"][0]["attempts"] == 2
    assert report["accounting"]["total_cost_usd"] is None, "Missing usage on the limited call is unknown"


def test_executor_usage_limit_cli_prints_reset_time_only_on_stderr(setup: tuple[Path, Path, Path],
                                                                  monkeypatch: pytest.MonkeyPatch,
                                                                  capsys: pytest.CaptureFixture[str]) -> None:
    import eval.__main__ as cli

    root, config, out = setup
    fixture = Path(__file__).parent / "fixtures/usage-limit.jsonl"

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        kwargs["stdout"].write_text(fixture.read_text())
        kwargs["stderr"].write_text("")
        return ProcessResult(1)

    monkeypatch.setenv("LHM_PRIVATE_GRADERS", str(root))
    monkeypatch.setattr("sys.argv", ["eval", "run", "--config", str(config), "--out", str(out)])
    monkeypatch.setattr(cli, "run", lambda c, o, r: run(c, o, r, execute=limited, version="codex-cli 0.162.0-alpha.17.2"))
    assert cli.main() == 2
    capture = capsys.readouterr()
    assert capture.out == ""
    assert "STOP-E1" in capture.err and "You've hit your usage limit" in capture.err
    assert "Oct 28th, 2026 1:03 PM" in capture.err


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


@pytest.mark.parametrize('backend', ['codex_cli', 'cheap_api', 'local'])
@pytest.mark.parametrize('deadline', [False, True])
def test_control_failure_deadline_classification(setup: tuple[Path, Path, Path],
                                                 backend: str, deadline: bool) -> None:
    root, config, out = setup
    harness_config(config)
    value = json.loads(config.read_text())
    value['control_backend'] = backend
    config.write_text(json.dumps(value))

    def failure(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert '-m' in argv and argv[argv.index('-m') + 1] == 'controller'
        assert argv[argv.index('--backend') + 1] == backend
        kwargs['stdout'].write_text('')
        kwargs['stderr'].write_text('other diagnostic\ncontrol_failure ' + json.dumps({
            'reason': 'deadline' if deadline else 'transport', 'operation': 'contract'}) + '\n')
        return ProcessResult(2)

    report = json.loads(run(config, out, root, execute=failure,
                            version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None
    assert report['validity']['status'] == 'invalid'
    reason = 'control_timeout' if deadline else 'control_cli_error'
    assert reason in task['invalid_reasons']
    assert ('control_cli_error' if deadline else 'control_timeout') not in task['invalid_reasons']
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert entry['control_invalid_reason'] == reason
    assert (out / 'bug-chunk-tail/contract.stderr').read_text().startswith('other diagnostic\n')


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
    monkeypatch.setattr(core, "current_commit", lambda _: __import__("eval.runner.report", fromlist=["current_commit"]).current_commit(REPOSITORY))
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


def test_usage_limit_stops_the_entire_task_loop(setup: tuple[Path, Path, Path], tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    calls = 0

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal calls
        assert argv[0] == 'codex'
        calls += 1
        kwargs['stdout'].write_text((Path(__file__).parent / 'fixtures/usage-limit.jsonl').read_text())
        kwargs['stderr'].write_text('')
        return ProcessResult(1)

    with pytest.raises(IncompleteRun, match='after 1 of 2 tasks'):
        run(config, out, root, execute=limited, version='codex-cli 0.162.0-alpha.17.2')
    assert calls == 1
    assert len(json.loads((out / 'checkpoint.json').read_text())['tasks']) == 1
    assert not list(out.glob('*/result.json'))


def test_repeated_control_limits_retain_logs_then_resume_verifier_reinstruction(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor()
    failures = 0

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal failures
        if '-m' in argv and argv[argv.index('-m') + 1] == 'verifier' and failures < 2:
            failures += 1
            kwargs['stdout'].write_text('')
            # Retain the actual controller logger envelope, including its prefix.
            kwargs['stderr'].write_text('INFO:controller.backends.codex_cli:control_cli_events ' + json.dumps({
                'model': 'gpt-6-luna', 'events': (Path(__file__).parent / 'fixtures/usage-limit.jsonl').read_text()}) + '\n')
            return ProcessResult(2)
        return executor(argv, **kwargs)

    for expected in (1, 2):
        with pytest.raises(IncompleteRun, match='usage limit'):
            run(config, out, root, execute=limited, version='codex-cli 0.162.0-alpha.17.2')
        assert executor.calls == 1 and failures == expected
        assert not (out / 'bug-chunk-tail/result.json').exists()
    report = json.loads(run(config, out, root, execute=limited, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'pass' and executor.calls == 2
    assert executor.operations == ['contract', 'check', 'check']
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert len([name for name in entry['control_files'] if name.startswith('control-interruptions/')]) == 6
    assert len([a for a in report['tasks'][0]['artifacts'] if 'control-interruptions' in a['path']]) == 6


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
    assert set(diagnostics['audit_code_version']) == {
        'audit.py', 'protected_listing.py', 'javascript.py', 'javascript_derived.py', 'fingerprint_history.py', 'regrade.py', 'telemetry.py',
        'core.py', 'workspace_verification.py'}
    assert diagnostics['audit_code_version']['protected_listing.py'] == digest(
        (Path(regrade.__file__).parent / 'protected_listing.py').read_bytes())
    assert diagnostics['audit_code_version']['workspace_verification.py'] == digest(
        (Path(regrade.__file__).parent / 'workspace_verification.py').read_bytes())
    assert diagnostics['audit_code_version']['telemetry.py'] == digest(
        (Path(regrade.__file__).parent / 'telemetry.py').read_bytes())


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


def test_two_session_0163_settings_record_allows_day2_and_is_published(setup: tuple[Path, Path, Path],
                                                                    monkeypatch: pytest.MonkeyPatch,
                                                                    tmp_path: Path) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path)
    value = json.loads(config.read_text())
    value['codex_version'] = 'codex-cli 0.163.0-alpha.11.1'
    config.write_text(json.dumps(value))
    executor = TwoSessionExecutor()

    def native_0163(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex':
            fixture = Path(__file__).parent / 'fixtures/native-session-0.163.jsonl'
            events = [json.loads(line) for line in fixture.read_text().splitlines()]
            events[0]['payload']['id'] = f'day-{executor.calls}'
            native = Path(kwargs['env']['CODEX_HOME']) / f'sessions/rollout-day-{executor.calls}.jsonl'
            native.write_text(''.join(json.dumps(e) + '\n' for e in events))
        return result

    report = json.loads(run(config, out, root, execute=native_0163, version='codex-cli 0.163.0-alpha.11.1').read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert executor.calls == 2 and executor.grades == 1
    evidence = [json.loads(line) for line in (out / 'bug-chunk-tail/session-evidence.jsonl').read_text().splitlines()]
    applied = [e for e in evidence if e.get('payload', {}).get('type') == 'thread_settings_applied']
    assert len(applied) == 2
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert all(s['settings_verified'] for s in entry['segments'])


@pytest.mark.parametrize('stage', ['contract', 'check', 'handoff', 'validate-handoff', 'day2-contract', 'day2-check'])
def test_control_usage_limit_retries_pending_operation_without_reexecuting_days(setup: tuple[Path, Path, Path],
                                                                               monkeypatch: pytest.MonkeyPatch,
                                                                               tmp_path: Path, stage: str) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor()
    fixture = Path(__file__).parent / 'fixtures/usage-limit.jsonl'
    message = json.loads(fixture.read_text().splitlines()[0])['message']
    limited_calls = 0

    def limited(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal limited_calls
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            key = ('day2-' + operation if operation in {'contract', 'check'} and executor.calls >=
                   (1 if operation == 'contract' else 2) else operation)
            if key == stage and not limited_calls:
                limited_calls += 1
                kwargs['stdout'].write_text('')
                kwargs['stderr'].write_text('control_cli_events ' + json.dumps({
                    'model': 'gpt-6-luna', 'events': fixture.read_text()}) + '\n')
                if operation != 'validate-handoff':
                    # Even a partial output must be preserved without blocking retry.
                    Path(argv[argv.index('--out') + 1]).write_text('{partial output')
                return ProcessResult(2)
        return executor(argv, **kwargs)

    with pytest.raises(IncompleteRun, match='usage limit') as stopped:
        run(config, out, root, execute=limited, version='codex-cli 0.162.0-alpha.17.2')
    assert message in str(stopped.value)
    assert executor.grades == 0 and limited_calls == 1
    assert not (out / 'bug-chunk-tail/result.json').exists()
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert entry['phase'] == 'usage_limited'
    assert 'result' not in entry and 'control_error' not in entry
    archived = {name: value for name, value in entry['control_files'].items() if name.startswith('control-interruptions/')}
    assert len(archived) == (3 if stage == 'validate-handoff' else 4)
    from eval.runner.audit import digest
    for name, expected in archived.items():
        assert digest((Path(entry['runtime']) / name).read_bytes()) == expected
        if not name.endswith('.json'):
            assert (out / 'bug-chunk-tail' / name).is_file()

    report = json.loads(run(config, out, root, execute=limited, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert report['tasks'][0]['attempts'] == 2
    assert executor.calls == 2 and executor.grades == 1
    assert executor.operations == ['contract', 'check', 'handoff', 'validate-handoff', 'contract', 'check']
    retained = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']['control_files']
    assert archived.items() <= retained.items()
    assert len([a for a in report['tasks'][0]['artifacts'] if 'control-interruptions' in a['path']]) == len(archived)


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

    if process.timed_out:
        run(config, out, root, execute=fail_final, version='codex-cli 0.162.0-alpha.17.2')
    else:
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


@pytest.mark.parametrize('two', [False, True])
def test_control_costs_survive_days_and_reinstructions(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, two: bool) -> None:
    from tests.eval.test_control_accounting import generation, delegation
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True) if two else setup
    if not two:
        harness_config(config)
    executor = TwoSessionExecutor() if two else HarnessExecutor()

    def logged(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            text = '' if operation == 'validate-handoff' else generation()
            if operation == 'check':
                text += delegation()
            kwargs['stderr'].write_text(text)
        return result

    report = json.loads(run(config, out, root, execute=logged, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    controls = [c for c in task['calls'] if c['purpose'] != 'executor']
    assert len(controls) == (5 if two else 3)
    assert task['costs']['control_usd'] == pytest.approx(len(controls) * .000132)
    assert task['costs']['total_usd'] == pytest.approx(task['costs']['executor_usd'] + len(controls) * .000132)
    assert report['metadata']['control_model'] == 'gpt-6-luna'
    assert report['metrics']['cost_per_pass']['value'] == task['costs']['total_usd']
    assert task['attempts'] == 2


def test_checkpoint_records_start_provenance_and_warns_on_drift(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from eval.runner import core, report as reports
    root, config, out = setup
    monkeypatch.setattr(core, 'current_commit', lambda _: 'a' * 40)
    monkeypatch.setattr(reports, 'current_commit', lambda _: 'b' * 40)
    report = json.loads(run(config, out, root, execute=Executor(), version='codex-cli 0.162.0-alpha.17.2').read_text())
    state = json.loads((out / 'checkpoint.json').read_text())
    assert state['git_commit'] == report['metadata']['git_commit'] == 'a' * 40
    assert state['pricing_snapshot_id'] == report['metadata']['pricing']['snapshot_id']
    assert 'a' * 40 in capsys.readouterr().err
    state['pricing_snapshot_id'] = 'starting-snapshot'
    reports.build(json.loads(config.read_text()), state, report['tasks'], report['metadata']['codex_version'], REPOSITORY)
    warning = capsys.readouterr().err
    assert 'starting-snapshot' in warning and state['pricing_snapshot_id'] != report['metadata']['pricing']['snapshot_id']
    assert report['metadata']['pricing']['snapshot_id'] in warning
    state.pop('git_commit')
    state.pop('pricing_snapshot_id')
    legacy = reports.build(json.loads(config.read_text()), state, report['tasks'], report['metadata']['codex_version'], REPOSITORY)
    assert legacy['metadata']['git_commit'] == 'b' * 40
    assert 'differs from build' not in capsys.readouterr().err


def test_multiple_control_models_warn_and_keep_metadata_null(setup: tuple[Path, Path, Path],
        capsys: pytest.CaptureFixture[str]) -> None:
    from tests.eval.test_control_accounting import generation, delegation
    root, config, out = setup
    harness_config(config)
    executor = HarnessExecutor()

    def logged(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            kwargs['stderr'].write_text(generation(model='gpt-6-luna' if operation == 'contract' else 'another-model') +
                                        (delegation() if operation == 'check' else ''))
        return result

    report = json.loads(run(config, out, root, execute=logged, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['metadata']['control_model'] is None
    assert report['tasks'][0]['costs']['total_usd'] is None
    warning = capsys.readouterr().err
    assert 'another-model' in warning and 'gpt-6-luna' in warning


def test_static_templates_pinned_injection_and_resume(setup: tuple[Path, Path, Path]) -> None:
    from eval.runner.audit import digest
    root, config, out = setup
    templates = config.parent / 'templates'
    templates.mkdir()
    template = templates / 'bug-chunk-tail.md'
    template.write_text('Task summary: fix chunk tail.\n')
    cfg = json.loads(config.read_text())
    cfg['static_template_dir'] = str(templates)
    config.write_text(json.dumps(cfg))
    executor = Executor()
    prompts = []

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] == 'codex':
            prompts.append(kwargs['stdin'])
        return executor(argv, **kwargs)

    report = json.loads(run(config, out, root, execute=execute, version=cfg['codex_version']).read_text())
    original = (REPOSITORY / 'eval/tasks/bug-chunk-tail/prompt.md').read_text()
    assert prompts == [original + '\n\nApproved evaluation contract (benchmark runner authorization):\n' + template.read_text()]
    hashes = json.loads((out / 'checkpoint.json').read_text())['static_templates']
    assert hashes == {'bug-chunk-tail': digest(template.read_bytes())}
    assert {'path': str(out / 'bug-chunk-tail/static-template.md'), 'sha256': hashes['bug-chunk-tail']} in report['tasks'][0]['artifacts']
    run(config, out, root, execute=execute, version=cfg['codex_version'])
    assert executor.calls == 1
    template.write_text('Changed after start')
    with pytest.raises(ValueError, match='templates changed'):
        run(config, out, root, execute=execute, version=cfg['codex_version'])
    assert executor.calls == 1


@pytest.mark.parametrize('content', [None, '__HUMAN_FILL__', ''])
def test_static_templates_preflight_before_any_process(setup: tuple[Path, Path, Path], content: str | None) -> None:
    root, config, out = setup
    templates = config.parent / 'templates'
    templates.mkdir()
    if content is not None:
        (templates / 'bug-chunk-tail.md').write_text(content)
    cfg = json.loads(config.read_text())
    cfg['static_template_dir'] = str(templates)
    config.write_text(json.dumps(cfg))

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail('Preflight launched a process')

    with pytest.raises(ValueError, match='static template'):
        run(config, out, root, execute=forbidden, version=forbidden)
    assert not out.exists()


def test_population_digest_separate_from_selected_inputs(setup: tuple[Path, Path, Path]) -> None:
    from eval.runner.core import taskset_digest
    root, config, out = setup
    other = 'bug-fix-adjacent-runs'
    (root / other).mkdir()
    (root / other / 'test_private_synthetic.py').write_text('import unittest\n')
    cfg = json.loads(config.read_text())
    cfg['task_population'] = ['bug-chunk-tail', other]
    config.write_text(json.dumps(cfg))
    report = json.loads(run(config, out, root, execute=Executor(), version=cfg['codex_version']).read_text())
    expected = taskset_digest({task: PrivateGraders.load(root, task, REPOSITORY) for task in cfg['task_population']})
    checkpoint = json.loads((out / 'checkpoint.json').read_text())
    assert report['metadata']['task_set_sha256'] == checkpoint['task_set_sha256'] == expected
    assert checkpoint['selected_task_set_sha256'] != expected
    assert [t['task_id'] for t in report['tasks']] == ['bug-chunk-tail']
    (root / other / 'test_private_synthetic.py').write_text('import unittest\n# changed\n')
    with pytest.raises(ValueError, match='task set differs'):
        run(config, out, root, execute=Executor(), version=cfg['codex_version'])


CAPACITY_MESSAGE = 'Selected model is at capacity. Please try a different model.'
CAPACITY_STREAM = (json.dumps({'type': 'error', 'message': CAPACITY_MESSAGE}) + '\n' +
                   json.dumps({'type': 'turn.failed', 'error': {'message': CAPACITY_MESSAGE}}) + '\n')


@pytest.mark.parametrize('persistent', [False, True])
def test_executor_capacity_recovery_is_not_an_attempt(setup: tuple[Path, Path, Path],
                                                      monkeypatch: pytest.MonkeyPatch,
                                                      persistent: bool) -> None:
    root, config, out = setup
    executor = Executor()
    waits: list[int] = []
    monkeypatch.setattr('eval.runner.core.sleep', waits.append)
    refusals = 0
    calls = 0

    def capacity(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal refusals, calls
        if argv[0] == 'codex':
            calls += 1
            if calls > 1:
                assert 'resume' in argv and 'unit-session' in argv
                assert kwargs['stdin'] == 'Continue the original task from the current workspace.'
            if persistent or refusals == 0:
                executor(argv, **kwargs)
                kwargs['stdout'].write_text(json.dumps({'type': 'thread.started', 'thread_id': 'unit-session'}) +
                                            '\n' + CAPACITY_STREAM)
                refusals += 1
                return ProcessResult(1)
        return executor(argv, **kwargs)

    if persistent:
        with pytest.raises(IncompleteRun, match='capacity error.*resumable'):
            run(config, out, root, execute=capacity, version='codex-cli 0.162.0-alpha.17.2')
        assert waits == [60, 120, 300, 600] and calls == 5
        entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
        assert entry['phase'] == 'capacity_limited' and 'result' not in entry
        assert not (out / 'bug-chunk-tail/result.json').exists()
        assert all(s['capacity_error'] for s in entry['segments'])
        persistent = False
    report = json.loads(run(config, out, root, execute=capacity, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['attempts'] == 1
    assert report['metrics']['avg_attempts']['value'] == 1
    assert len(task['executor_segments']) == refusals + 1
    assert all(c['usage']['input_tokens'] == 0 and c['usage']['usd'] == 0 for c in task['calls'][:-1])
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    assert len(diagnostics['infrastructure_recoveries']) >= refusals
    assert all(s['infrastructure_recovery'] for s in diagnostics['infrastructure_recoveries'])
    if refusals == 1:
        assert waits == [60]


@pytest.mark.parametrize('stage', ['contract', 'check', 'handoff', 'day2-contract', 'day2-check'])
@pytest.mark.parametrize('persistent', [False, True])
def test_control_capacity_retries_archives_and_never_reinstructs(setup: tuple[Path, Path, Path],
                                                                monkeypatch: pytest.MonkeyPatch,
                                                                tmp_path: Path, stage: str,
                                                                persistent: bool) -> None:
    root, config, out = two_session_config(setup, monkeypatch, tmp_path, harness_on=True)
    executor = TwoSessionExecutor()
    waits: list[int] = []
    monkeypatch.setattr('eval.runner.harness.sleep', waits.append)
    refusals = 0

    def capacity(argv: list[str], **kwargs: Any) -> ProcessResult:
        nonlocal refusals
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            key = ('day2-' + operation if operation in {'contract', 'check'} and executor.calls >=
                   (1 if operation == 'contract' else 2) else operation)
            if key == stage and (persistent or refusals == 0):
                refusals += 1
                kwargs['stdout'].write_text('')
                kwargs['stderr'].write_text('INFO:verifier:control_cli_events ' + json.dumps({
                    'model': 'gpt-6-luna', 'events': CAPACITY_STREAM}) + '\n')
                Path(argv[argv.index('--out') + 1]).write_text('{partial output')
                return ProcessResult(2)
        return executor(argv, **kwargs)

    if persistent:
        with pytest.raises(IncompleteRun, match='capacity error'):
            run(config, out, root, execute=capacity, version='codex-cli 0.162.0-alpha.17.2')
        assert waits == [60, 120, 300, 600] and refusals == 5
        entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
        assert 'result' not in entry and 'control_error' not in entry
        assert not (out / 'bug-chunk-tail/result.json').exists()
        assert executor.grades == 0
        diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
        assert len(diagnostics['infrastructure_recoveries']) == 5
        persistent = False
    report = json.loads(run(config, out, root, execute=capacity, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'pass'
    assert report['tasks'][0]['attempts'] == 2 and executor.calls == 2
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    assert not entry.get('reinstruction') and 'control_error' not in entry
    archived = [n for n in entry['control_files'] if n.endswith('.stderr') and n.startswith('control-interruptions/')]
    assert len(archived) == refusals
    assert all((out / 'bug-chunk-tail' / n).is_file() for n in archived)
    if refusals == 1:
        assert waits == [60]


def test_timeout_records_sample_and_continues_next_task(setup: tuple[Path, Path, Path],
                                                       monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    executor = Executor()

    def timeout(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = executor(argv, **kwargs)
        if argv[0] == 'codex' and executor.calls == 1:
            return ProcessResult(-9, timed_out=True)
        return result

    report = json.loads(run(config, out, root, execute=timeout, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert sorted(t['outcome'] for t in report['tasks']) == ['pass', 'timeout']
    assert report['accounting']['valid_tasks'] == 2 and executor.calls == 2
    assert json.loads((out / 'run-diagnostics.json').read_text())['stop_reason'] is None


@pytest.mark.parametrize('items', [False, True])
def test_executor_capacity_usage_and_native_counts(tmp_path: Path, items: bool) -> None:
    from eval.runner.report import usage
    from eval.runner.telemetry import native_token_delta, native_token_totals
    path = tmp_path / 'events'
    item = json.dumps({'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'work'}}) + '\n'
    path.write_text((item if items else '') + CAPACITY_STREAM)
    pricing = json.loads((REPOSITORY / 'eval/prices.yaml').read_text())
    priced = usage(path, 1, 'gpt-6.1-sol', pricing, tier='standard')
    assert priced['input_tokens'] == (None if items else 0)
    assert priced['usd'] == (None if items else 0)
    native = tmp_path / 'native'
    native.write_text(json.dumps({'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
        'total_token_usage': {'input_tokens': 100, 'cached_input_tokens': 20, 'output_tokens': 30,
                              'reasoning_output_tokens': 10}}}}) + '\n')
    counts = native_token_delta({}, native_token_totals([native]))
    assert counts == {'input_tokens': 100, 'cached_input_tokens': 20, 'output_tokens': 30}
    assert native_token_delta(native_token_totals([native]), native_token_totals([native])) is None
    priced = usage(path, 1, 'gpt-6.1-sol', pricing, native_counts=counts)
    assert priced['output_tokens'] == (30 if items else 0)


def test_capacity_after_work_retains_native_cost_and_resume_delta(setup: tuple[Path, Path, Path],
                                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    root, config, out = setup
    executor = Executor()
    monkeypatch.setattr('eval.runner.core.sleep', lambda seconds: None)

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            return executor(argv, **kwargs)
        native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
        before = native.read_text() if native.exists() else ''
        result = executor(argv, **kwargs)
        counts = {'input_tokens': 100 if executor.calls == 1 else 120,
                  'cached_input_tokens': 0, 'output_tokens': 10 if executor.calls == 1 else 18,
                  'reasoning_output_tokens': 3}
        native.write_text(before + native.read_text() + json.dumps({'type': 'event_msg',
            'payload': {'type': 'token_count', 'info': {'total_token_usage': counts}}}) + '\n')
        if executor.calls == 1:
            kwargs['stdout'].write_text(json.dumps({'type': 'thread.started', 'thread_id': 'unit-session'}) + '\n' +
                json.dumps({'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'work'}}) + '\n' + CAPACITY_STREAM)
            return ProcessResult(1)
        return result

    report = json.loads(run(config, out, root, execute=execute, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass' and task['attempts'] == 1
    assert [c['usage']['input_tokens'] for c in task['calls']] == [100, 20]
    assert [c['usage']['output_tokens'] for c in task['calls']] == [10, 8]
    assert task['costs']['executor_usd'] == pytest.approx(.00042)


def test_failing_grader_content_never_published(setup: tuple[Path, Path, Path], tmp_path: Path) -> None:
    from eval.runner import regrade
    root, config, out = setup
    assertion = "self.assertEqual('PRIVATE_ASSERT_SOURCE_724', 'other', 'PRIVATE_ASSERT_MESSAGE_931')"
    (root / 'bug-chunk-tail/test_private_synthetic.py').write_text(
        'import unittest\nclass Checks(unittest.TestCase):\n'
        f' def test_failure(self): {assertion}\n'
        " def test_error(self): raise RuntimeError('PRIVATE_ERROR_MESSAGE_892')\n"
        " @unittest.skip('PRIVATE_SKIP_REASON_623')\n def test_skip(self): pass\n")
    executor = Executor()
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    assert report['tasks'][0]['outcome'] == 'fail'
    state = json.loads((out / 'checkpoint.json').read_text())
    retained = Path(state['tasks']['bug-chunk-tail']['runtime']) / 'grading.log'
    assert assertion in retained.read_text() and 'PRIVATE_ASSERT_MESSAGE_931' in retained.read_text()
    new = tmp_path / 'regraded'
    regrade.regrade(root, out, new, execute=executor)
    for destination in (out, new):
        published = '\n'.join(p.read_text() for p in destination.rglob('*') if p.is_file())
        for secret in (assertion, 'PRIVATE_ASSERT_SOURCE_724', 'PRIVATE_ASSERT_MESSAGE_931',
                       'PRIVATE_ERROR_MESSAGE_892', 'PRIVATE_SKIP_REASON_623'):
            assert secret not in published
        log = (destination / 'bug-chunk-tail/grading.log').read_text()
        assert 'test_failure (test_private_synthetic.Checks.test_failure) ... FAIL' in log
        assert 'test_error (test_private_synthetic.Checks.test_error) ... ERROR' in log
        assert 'test_skip (test_private_synthetic.Checks.test_skip) ... skipped' in log
        assert 'Ran 3 tests' in log and 'FAILED (failures=1, errors=1, skipped=1)' in log


def test_checkout_paths_are_relative_and_resolve_outside_checkout(
    setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from eval.runner import core, regrade
    from eval.runner.report import validate
    root, config, _ = two_session_config(setup, monkeypatch, tmp_path)
    out = core.REPOSITORY / 'eval/generated-smoke'
    executor = TwoSessionExecutor()
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['handoff']['evidence']['path'] == 'eval/generated-smoke/bug-chunk-tail/handoff-evidence.json'
    assert task['grading']['log']['path'] == 'eval/generated-smoke/bug-chunk-tail/grading.log'
    monkeypatch.chdir(tmp_path)
    validate(report, core.REPOSITORY)
    legacy = json.loads(json.dumps(report))
    legacy['tasks'][0]['handoff']['evidence']['path'] = str(
        core.REPOSITORY / task['handoff']['evidence']['path'])
    validate(legacy, core.REPOSITORY)
    run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2')
    # Historical review copies can still contain the checkout prefix.
    (out / 'bug-chunk-tail/legacy-review.log').write_text(str(core.REPOSITORY / 'eval/tasks') + '\n')
    new = core.REPOSITORY / 'eval/generated-regrade'
    regrade.regrade(root, out, new, execute=executor)
    assert (new / 'bug-chunk-tail/legacy-review.log').read_text() == 'eval/tasks\n'
    # The retained source stays unchanged; only the new review copy is normalized.
    assert str(core.REPOSITORY) in (out / 'bug-chunk-tail/legacy-review.log').read_text()
    for destination in (out, new):
        assert str(core.REPOSITORY) not in '\n'.join(
            p.read_text() for p in destination.rglob('*') if p.is_file()
            and p.name != 'legacy-review.log')


@pytest.mark.parametrize('output_first', [False, True])
def test_runner_uses_full_native_authorship_before_retry_or_grading(
    setup: tuple[Path, Path, Path], output_first: bool,
) -> None:
    root, config, out = setup
    harness_config(config)
    assertion = 'assert "opaque-runner-91735" != "opaque-runner-82419"'
    grader = root / 'bug-chunk-tail/test_private_synthetic.py'
    grader.write_text(grader.read_text() + assertion + '\n')

    class ProvenanceExecutor(HarnessExecutor):
        def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
            result = super().__call__(argv, **kwargs)
            if argv[0] != 'codex':
                return result
            session = Path(kwargs['env']['CODEX_HOME']) / 'sessions'
            events: list[dict[str, Any]] = [{'type': 'session_meta', 'payload': {
                'id': 'unit-session', 'cli_version': '0.162.0-alpha.17.2'}}]
            echo = {'type': 'event_msg', 'timestamp': f'2000-01-01T00:00:0{self.calls * 2}Z',
                    'payload': {'type': 'item_completed', 'item': {'type': 'CommandExecution',
                    'id': 'proof-' + str(self.calls), 'command': ['sh', '-lc', 'cat test_regression.py'],
                    'aggregated_output': assertion}}}
            if self.calls == 1:
                patch = '*** Begin Patch\n*** Add File: test_regression.py\n+' + assertion + '\n*** End Patch'
                writing = [{'type': 'response_item', 'timestamp': '2000-01-01T00:00:01Z',
                            'payload': {'type': 'custom_tool_call', 'name': 'apply_patch',
                                        'call_id': 'own-writing', 'input': patch}},
                           {'type': 'response_item', 'timestamp': '2000-01-01T00:00:01Z',
                            'payload': {'type': 'custom_tool_call_output', 'call_id': 'own-writing', 'output': 'Success'}}]
                if output_first:
                    events.append(dict(echo, timestamp='2000-01-01T00:00:00Z'))
                events.extend(writing)
            events.append(echo)
            (session / f'proof-{self.calls}.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
            (kwargs['cwd'] / 'test_regression.py').write_text(assertion + '\n')
            capture = [json.loads(line) for line in kwargs['stdout'].read_text().splitlines()]
            capture.insert(-1, {'type': 'item.completed', 'item': {
                'type': 'command_execution', 'id': 'proof-' + str(self.calls),
                'command': 'cat test_regression.py', 'aggregated_output': assertion}})
            kwargs['stdout'].write_text(''.join(json.dumps(event) + '\n' for event in capture))
            return result

    executor = ProvenanceExecutor()
    report = json.loads(run(config, out, root, execute=executor, version='codex-cli 0.162.0-alpha.17.2').read_text())
    task = report['tasks'][0]
    assert task['outcome'] == ('invalid' if output_first else 'pass')
    assert task['grader_access_audit']['status'] == ('access_detected' if output_first else 'clean')
    assert executor.calls == (1 if output_first else 2)
    assert executor.operations == (['contract'] if output_first else ['contract', 'check', 'check'])
