"""Offline golden tests for judge/handoff and the shared backend budget."""

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from controller.__main__ import main
from controller.backends.base import Usage
from controller.backends.cheap_api import CheapAPIBackend
from controller.backends.codex_cli import CodexCLIBackend
from controller.backends.routing import RoutedBackend
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.generation import schema_validator
from controller.handoff_gen import generate_handoff
from controller.judge import generate_judgment
from controller.settings import load_object
from tests.controller.support import ROOT, RecordingTransport, response
from tests.controller.test_codex_cli import MockRunner, events


def criterion() -> dict[str, Any]:
    return load_object(ROOT / "schemas/examples/criterion.json")


def judgment(status: str = "pass") -> dict[str, str]:
    return {"status": status, "reason": "Synthetic comparison result.",
            "evidence": "SYNTHETIC llm_judge: diff.txt contains the supplied comparison."}


def handoff() -> dict[str, Any]:
    return {"done": [{"criterion_id": "SC-1", "artifact": "app/main.py"},
                     {"criterion_id": "SC-2", "artifact": "app/main.py"}],
            "remaining": [{"criterion_id": "SC-3", "state": "tests missing"},
                          {"criterion_id": "SC-4", "state": "comparison failed"}],
            "decisions": [], "verify_commands": ["python -m pytest"], "do_not_touch": []}


def inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    return (load_object(ROOT / "schemas/examples/contract.json"),
            load_object(ROOT / "schemas/examples/verdict_fail.json"))


@pytest.fixture(autouse=True)
def offline_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-offline-key")


@pytest.mark.parametrize("status", ["pass", "fail", "unverifiable"])
@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api"])
def test_judge_status_identity_and_usage(status: str, selected: str, tmp_path: Path) -> None:
    artifact = tmp_path / "diff.txt"
    artifact.write_text("synthetic diff", encoding="utf-8")
    runner = MockRunner(output=judgment(status))
    transport = RecordingTransport([response(judgment(status))])
    routed = RoutedBackend(selected, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    result = generate_judgment(criterion(), artifact, routed)
    schema_validator("judgment.schema.json").validate(result)
    assert result["status"] == status and result["criterion_id"] == criterion()["id"]
    assert result["model"] == "gpt-6-luna"
    assert result["usage"]["cost_basis"] == "api_equivalent_usd"
    assert result["usage"]["pricing_ref"].startswith("controller/prices.yaml@2026-10-21#")
    assert len(routed.calls) == 1  # fail/unverifiable never trigger fallback.
    assert len(runner.calls) == (selected == "codex_cli")
    assert len(transport.calls) == (selected == "cheap_api")


@pytest.mark.parametrize("bad", [[], {"criterion": criterion()}, {},
    {**criterion(), "extra": 1}, {**criterion(), "check": {"type": "file_exists", "path": "x"}}])
def test_bad_judge_input_before_backend_call(bad: Any, tmp_path: Path) -> None:
    runner = MockRunner()
    backend = CodexCLIBackend(runner=runner, executable="/mock/codex")
    with pytest.raises(InputError):
        generate_judgment(bad, tmp_path, backend)
    assert not runner.calls


def test_judge_sums_invalid_schema_json_and_semantic_retries(tmp_path: Path) -> None:
    transport = RecordingTransport([response(text="invalid"),
        response({**judgment(), "evidence": "missing marker"}), response(judgment())])
    result = generate_judgment(criterion(), tmp_path, CheapAPIBackend(transport=transport))
    assert len(transport.calls) == 3
    assert result["usage"]["input_tokens"] == 3000
    assert result["usage"]["cached_input_tokens"] == 300
    assert result["usage"]["usd"] == pytest.approx(3 * .000191)


def test_judge_unknown_accounting_and_code_owned_fields(tmp_path: Path) -> None:
    class Backend:
        model = "synthetic-model"

        def generate(self, schema: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
            assert set(schema["required"]) == {"status", "reason", "evidence"}
            return {**judgment(), "criterion_id": "wrong", "model": "wrong", "usage": {"usd": 0}}

        def usage(self) -> Usage:
            return Usage(None, None, None, .1)

    result = generate_judgment(criterion(), tmp_path, Backend())
    assert result["criterion_id"] == criterion()["id"] and result["model"] == "synthetic-model"
    assert result["usage"]["usd"] is None and result["usage"]["pricing_ref"] is None


def test_judge_rejects_cache_over_input(tmp_path: Path) -> None:
    class Backend:
        model = "synthetic-model"

        def generate(self, schema: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
            return judgment()

        def usage(self) -> Usage:
            return Usage(1, 1, .1, .1, 2)

    with pytest.raises(InvalidGeneration):
        generate_judgment(criterion(), tmp_path, Backend())


@pytest.mark.parametrize("failure", ["nonzero", "timeout", "missing"])
def test_one_fallback_and_summed_accounting(failure: str, tmp_path: Path) -> None:
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal count
        count += 1
        assert kwargs["env"]["HARNESS_NESTED"] == "1" and kwargs["shell"] is False
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 1, output=events())
        if failure == "missing":
            raise FileNotFoundError("synthetic")
        return subprocess.CompletedProcess(argv, 1, events(), "not logged")

    transport = RecordingTransport([response({}), response(judgment())])
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    result = generate_judgment(criterion(), tmp_path, backend)
    assert count == 1 and len(transport.calls) == 2 and backend.count == 3
    assert [call["backend"] for call in backend.calls] == ["codex_cli", "cheap_api", "cheap_api"]
    assert backend.calls[0]["fallback_reason"]
    assert result["usage"]["input_tokens"] == (2000 if failure == "missing" else 3200)
    assert result["usage"]["usd"] == pytest.approx(sum(c["usd"] for c in backend.calls))


def test_fallback_cannot_reset_exhausted_budget(tmp_path: Path) -> None:
    runner = MockRunner(output={})
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
    })
    with pytest.raises(InvalidGeneration):
        generate_judgment(criterion(), tmp_path, backend)
    assert backend.count == len(runner.calls) == 3
    assert all(c["kwargs"]["env"]["HARNESS_NESTED"] == "1" for c in runner.calls)


def test_third_call_transport_failure_has_no_fourth_fallback(tmp_path: Path) -> None:
    runner = MockRunner(output={})

    def third_fails(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if len(runner.calls) == 2:
            runner.calls.append({})
            return subprocess.CompletedProcess(argv, 1, events(), "")
        return runner(argv, **kwargs)

    transport = RecordingTransport()
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=third_fails, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    with pytest.raises(BackendError):
        generate_judgment(criterion(), tmp_path, backend)
    assert backend.count == 3 and not transport.calls


def test_missing_fallback_key_is_internal_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY")
    runner = MockRunner(returncode=1)
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
    })
    with pytest.raises(BackendError, match="environment API key"):
        generate_judgment(criterion(), tmp_path, backend)
    assert backend.count == 1


def test_provider_model_mismatch_is_error_without_fallback(tmp_path: Path) -> None:
    envelope = response(judgment())
    envelope["model"] = "wrong-model"
    transport = RecordingTransport([envelope])
    with pytest.raises(BackendError, match="model identity"):
        generate_judgment(criterion(), tmp_path, CheapAPIBackend(transport=transport))
    assert len(transport.calls) == 1


@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api"])
def test_handoff_validated_against_verdict(selected: str) -> None:
    runner = MockRunner(output=handoff())
    transport = RecordingTransport([response(handoff())])
    backend = RoutedBackend(selected, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    result = generate_handoff("Assistant claimed everything done", *inputs(), backend)
    schema_validator("handoff.schema.json").validate(result)
    assert result == handoff()


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "false-done", "pass-remaining"])
def test_inconsistent_handoff_regenerates(kind: str) -> None:
    bad = copy.deepcopy(handoff())
    if kind == "missing":
        bad["remaining"].pop()
    elif kind == "extra":
        bad["done"].append({"criterion_id": "SC-unknown", "artifact": "x"})
    elif kind == "duplicate":
        bad["done"].append(bad["done"][0])
    elif kind == "false-done":
        bad["done"].append({"criterion_id": "SC-3", "artifact": "x"})
        bad["remaining"].pop(0)
    else:
        bad["remaining"].append({"criterion_id": "SC-1", "state": "x"})
        bad["done"].pop(0)
    transport = RecordingTransport([response(bad), response(handoff())])
    assert generate_handoff("transcript", *inputs(), CheapAPIBackend(transport=transport)) == handoff()
    assert len(transport.calls) == 2


@pytest.mark.parametrize("kind", ["id", "duplicate", "overall"])
def test_bad_verdict_rejected_before_calls(kind: str) -> None:
    contract, verdict = inputs()
    if kind == "id":
        verdict["items"][0]["id"] = "unknown"
    elif kind == "duplicate":
        verdict["items"].append(verdict["items"][0])
    else:
        verdict["overall"] = "pass"
    transport = RecordingTransport()
    with pytest.raises(InputError):
        generate_handoff("transcript", contract, verdict, CheapAPIBackend(transport=transport))
    assert not transport.calls


@pytest.mark.parametrize("command", ["judge", "handoff"])
@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api"])
def test_cli_new_commands_one_path_stdout(command: str, selected: str, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    value = judgment("unverifiable") if command == "judge" else handoff()
    runner = MockRunner(output=value)
    transport = RecordingTransport([response(value)])
    monkeypatch.setattr("controller.__main__.RoutedBackend", lambda selected: RoutedBackend(selected, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    }))
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("untrusted transcript", encoding="utf-8")
    args = (["--criterion", str(ROOT / "schemas/examples/criterion.json"), "--artifact", str(transcript)]
        if command == "judge" else ["--transcript", str(transcript), "--contract",
        str(ROOT / "schemas/examples/contract.json"), "--verdict", str(ROOT / "schemas/examples/verdict_fail.json")])
    output = tmp_path / "output.json"
    assert main([command, *args, "--backend", selected, "--out", str(output)]) == 0
    assert capsys.readouterr().out == f"{output}\n"
    schema_validator("judgment.schema.json" if command == "judge" else "handoff.schema.json").validate(load_object(output))


def test_missing_artifact_exit_one_no_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["judge", "--criterion", str(ROOT / "schemas/examples/criterion.json"),
        "--artifact", str(tmp_path / "absent"), "--backend", "codex_cli", "--out", str(tmp_path / "out")]) == 1
    assert capsys.readouterr().out == ""


def test_contract_cli_codex_with_retrieved_example(tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from tests.controller.test_cli import arguments
    from tests.controller.support import model_contract
    runner = MockRunner(output=model_contract())
    monkeypatch.setattr("controller.__main__.RoutedBackend", lambda selected: RoutedBackend(selected, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
    }))
    library = tmp_path / "cases"
    library.mkdir()
    (library / "case.jsonl").write_text(json.dumps(inputs()[0]) + "\n")
    out = tmp_path / "contract.json"
    args = arguments(out)
    args[args.index("--backend") + 1] = "codex_cli"
    args[args.index("--cases") + 1] = str(library)
    assert main(args) == 0
    assert capsys.readouterr().out == f"{out}\n"
    assert "<examples_data>\n[]" not in runner.calls[0]["kwargs"]["input"]
    assert load_object(ROOT / "controller/config.yaml")["default_backend"] == "codex_cli"


def test_cli_judge_exhaustion_preserves_existing_output(tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    runner = MockRunner(output={})
    monkeypatch.setattr("controller.__main__.RoutedBackend", lambda selected: RoutedBackend(selected, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
    }))
    out = tmp_path / "output.json"
    out.write_text("existing")
    assert main(["judge", "--criterion", str(ROOT / "schemas/examples/criterion.json"),
        "--artifact", str(tmp_path), "--backend", "codex_cli", "--out", str(out)]) == 2
    assert out.read_text() == "existing" and capsys.readouterr().out == ""
    assert len(runner.calls) == 3


def test_judge_snapshot_records_unavailable_evidence(tmp_path: Path) -> None:
    from controller.judge import artifact_snapshot
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "private-object").write_bytes(b"\xff")
    (tmp_path / "diff.txt").write_text("public comparison")
    (tmp_path / "image.bin").write_bytes(b"\xff")
    (tmp_path / "oversized.txt").write_text("x" * 1_000_001)
    snapshot = artifact_snapshot(tmp_path)
    assert snapshot["files"] == {"diff.txt": "public comparison"}
    assert set(snapshot["omitted"]) == {".git", "image.bin", "oversized.txt"}
    assert "private-object" not in json.dumps(snapshot)


def test_judge_symlink_rejected_before_model_calls(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("text")
    link = tmp_path / "link"
    link.symlink_to(target)
    transport = RecordingTransport()
    with pytest.raises(InputError):
        generate_judgment(criterion(), tmp_path, CheapAPIBackend(transport=transport))
    assert not transport.calls


def test_cli_model_conflict_does_not_fall_back(tmp_path: Path) -> None:
    runner = MockRunner(output=judgment(), stdout=json.dumps({"type": "session.started", "model": "wrong"}) + "\n" + events())
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: pytest.fail("Identity conflicts must not trigger fallback"),
    })
    with pytest.raises(BackendError, match="model identity"):
        generate_judgment(criterion(), tmp_path, backend)
    assert len(runner.calls) == 1 and backend.usage().input_tokens == 1200


def test_cli_unavailability_falls_back_without_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("controller.backends.codex_cli.shutil.which", lambda _: None)
    transport = RecordingTransport([response(judgment())])
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": CodexCLIBackend,
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    result = generate_judgment(criterion(), tmp_path, backend)
    assert backend.count == 2 and result["usage"]["usd"] == pytest.approx(.000191)
    assert backend.calls[0]["backend"] == "codex_cli"


@pytest.mark.parametrize("failure", ["not_on_path", "file_not_found", "permission"])
@pytest.mark.parametrize("command", ["contract", "judge"])
def test_cli_never_started_uses_only_http_accounting(
    failure: str, command: str, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from tests.controller.support import model_contract
    from tests.controller.test_cli import arguments

    runner_calls = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal runner_calls
        runner_calls += 1
        if failure == "permission":
            raise PermissionError("synthetic spawn denied")
        raise FileNotFoundError("synthetic missing executable")

    monkeypatch.setattr("controller.backends.codex_cli.shutil.which", lambda _: None)
    transport = RecordingTransport([response(model_contract() if command == "contract" else judgment())])
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(
            runner=runner, executable="missing-codex" if failure == "not_on_path" else "/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    monkeypatch.setattr("controller.__main__.RoutedBackend", lambda selected: backend)
    out = tmp_path / "output.json"
    args = arguments(out) if command == "contract" else [
        "judge", "--criterion", str(ROOT / "schemas/examples/criterion.json"),
        "--artifact", str(tmp_path), "--backend", "codex_cli", "--out", str(out)]
    args[args.index("--backend") + 1] = "codex_cli"
    assert main(args) == 0
    assert capsys.readouterr().out == f"{out}\n"
    result = load_object(out)
    schema_validator(f"{command if command == 'contract' else 'judgment'}.schema.json").validate(result)
    usage = result["cost_estimate" if command == "contract" else "usage"]
    assert usage["input_tokens"] == 1000 and usage["output_tokens"] == 200
    assert usage["usd"] == pytest.approx(.000191)
    if command == "judge":
        assert usage["cached_input_tokens"] == 100
    assert runner_calls == (0 if failure == "not_on_path" else 1)
    assert len(transport.calls) == 1 and backend.count == 2
    assert [call["backend"] for call in backend.calls] == ["codex_cli", "cheap_api"]
    cli_call, http_call = backend.calls
    assert cli_call["fallback_reason"]
    for field in ("input_tokens", "cached_input_tokens", "output_tokens", "usd"):
        assert cli_call[field] == 0
        assert getattr(backend.usage(), field) == http_call[field]


@pytest.mark.parametrize("failure", ["deadline", "nonzero", "no_usage"])
@pytest.mark.parametrize("command", ["contract", "judge"])
def test_started_cli_unknown_usage_remains_unknown_after_fallback(
    failure: str, command: str, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from tests.controller.support import model_contract
    from tests.controller.test_cli import arguments

    runner_calls = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal runner_calls
        runner_calls += 1
        if failure == "deadline":
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"], output='{"type":"turn.started"}\n')
        # Successful exit with no final-message file is also a transport failure.
        return subprocess.CompletedProcess(argv, 1 if failure == "nonzero" else 0, "", "")

    transport = RecordingTransport([response(model_contract() if command == "contract" else judgment())])
    backend = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    monkeypatch.setattr("controller.__main__.RoutedBackend", lambda selected: backend)
    out = tmp_path / "output.json"
    if command == "contract":
        out.write_text("existing", encoding="utf-8")
        args = arguments(out)
        args[args.index("--backend") + 1] = "codex_cli"
        assert main(args) == 2
        captured = capsys.readouterr()
        assert captured.out == "" and "no reliable usage accounting" in captured.err
        assert out.read_text(encoding="utf-8") == "existing"
    else:
        assert main(["judge", "--criterion", str(ROOT / "schemas/examples/criterion.json"),
            "--artifact", str(tmp_path), "--backend", "codex_cli", "--out", str(out)]) == 0
        assert capsys.readouterr().out == f"{out}\n"
        result = load_object(out)
        schema_validator("judgment.schema.json").validate(result)
        for field in ("input_tokens", "cached_input_tokens", "output_tokens", "usd"):
            assert result["usage"][field] is None
    assert runner_calls == len(transport.calls) == 1
    assert backend.calls[0]["fallback_reason"]
    for field in ("input_tokens", "cached_input_tokens", "output_tokens", "usd"):
        assert backend.calls[0][field] is None
        assert getattr(backend.usage(), field) is None


def test_fallback_rejects_different_model_before_http_call(tmp_path: Path) -> None:
    config = copy.deepcopy(load_object(ROOT / "controller/config.yaml"))
    config["cheap_api"]["model"] = "different-model"
    runner = MockRunner(returncode=1)
    transport = RecordingTransport([response(judgment())])
    backend = RoutedBackend("codex_cli", config=config, factories={
        "codex_cli": lambda: CodexCLIBackend(runner=runner, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    with pytest.raises(BackendError, match="same model"):
        generate_judgment(criterion(), tmp_path, backend)
    assert len(runner.calls) == backend.count == 1
    assert not transport.calls
