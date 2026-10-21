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
            events.append({"type": "item.completed", "text": "test_private_synthetic.py"})
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
    assert result["usage"]["billed_usd"] is None
    assert result["usage"]["plan_usage"]["availability"] == "unavailable"
    assert report["metrics"]["pass_rate"] == 1
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
    assert result["metrics"]["sample_size"] == 0


def test_interrupted_turn_resumes_same_session_before_grading(setup: tuple[Path, Path, Path]) -> None:
    root, config, out = setup
    executor = Executor(interrupt=True)
    first = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert first["tasks"][0]["grading"] is None
    assert first["tasks"][0]["outcome"] == "invalid"
    second = json.loads(run(config, out, root, execute=executor, version="codex-cli 0.162.0-alpha.17.2").read_text())
    assert second["tasks"][0]["outcome"] == "pass"
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
