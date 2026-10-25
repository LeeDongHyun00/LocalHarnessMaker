"""Offline hook-path regression coverage; no live providers or grader access."""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from controller.__main__ import main
from controller.analyze import Prices
from controller.backends.base import Usage
from controller.errors import BackendError, InputError
from controller.generation import schema_validator
from controller.settings import PACKAGE_DIR, load_object
from controller.v3 import (_audit_validator, artifact_root, atomic_json, retain,
                           run_operation, validate_requirements)
from controller.v3_checks import derive_check, digest, safe_argv, signature_bytes
from controller.v3_client import IdentityUnobserved, PinMismatch, PinnedLunaClient, native_models
from controller.v3_wire import CLAIMS, REQUIREMENTS

SESSION = "native/session/한글"


def setup_session(tmp_path: Path) -> tuple[Path, Path]:
    directory = tmp_path / ".localharness/v3/sessions" / digest(SESSION.encode())
    directory.mkdir(parents=True)
    models = retain(directory, "evidence/models.json", b'{"models":[{"slug":"gpt-6-luna"}]}')
    prices = retain(directory, "evidence/prices.json", (PACKAGE_DIR / "prices.yaml").read_bytes())
    pin = load_object(PACKAGE_DIR.parent / "schemas/examples/pin-check.json")
    pin.update(session_id=SESSION, model_list=models, pricing_snapshot=prices,
               pricing_ref="test-pinned-controller-snapshot")
    atomic_json(directory / "pin-check.json", pin)
    prompt = tmp_path / "request.txt"
    prompt.write_text("Create `answer.py`. Return sorted results. Run `python -m unittest discover -v`.")
    return directory, prompt


def rows() -> dict[str, Any]:
    return {"requirements": [
        {"kind": "named_file", "text": "Create answer.py", "source_excerpt": "Create `answer.py`."},
        {"kind": "behavior", "text": "Sort results", "source_excerpt": "Return sorted results."},
        {"kind": "test_command", "text": "Run tests", "source_excerpt": "Run `python -m unittest discover -v`."},
    ], "open_questions": []}


class FakeClient:
    def __init__(self, value: dict[str, Any], *, fail: bool = False,
                 timeout: bool = False, model: str | None = "gpt-6-luna") -> None:
        self.value, self.fail, self.timeout, self.model = value, fail, timeout, model
        self.calls = 0
        self.events = ""
        self.messages: list[dict[str, str]] = []

    def generate(self, schema: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
        self.calls += 1
        assert self.calls == 1
        self.messages = messages
        if self.fail:
            raise BackendError("failed")
        return self.value

    def usage(self) -> Usage:
        return Usage(100, 50, 999.0, .2, 20)  # Code recomputes pinned cost.


def invoke(directory: Path, prompt: Path, client: FakeClient, **kwargs: Any) -> tuple[Path, int]:
    return run_operation("requirements", session_id=SESSION, artifacts=directory,
                         prompt_path=prompt, client_factory=lambda *_: client, **kwargs)


def accounting(directory: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in (directory / "luna-calls.jsonl").read_text().splitlines()]
    for record in records:
        schema_validator("luna-call.schema.json").validate(record)
    return records


@pytest.mark.parametrize("version", [None, "v1", "v2"])
def test_prompt_selection_both_phases_and_accounting_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str | None,
) -> None:
    from controller.v3_prompts import PROMPT_VERSION_ENV, select_prompt

    if version is None:
        monkeypatch.delenv(PROMPT_VERSION_ENV, raising=False)
    else:
        monkeypatch.setenv(PROMPT_VERSION_ENV, version)
    selected = version or "v2"
    directory, prompt = setup_session(tmp_path)
    requirements_client = FakeClient(rows())
    requirements_path, code = invoke(directory, prompt, requirements_client)
    assert code == 0
    final = tmp_path / "final.txt"
    final.write_text("Created answer.py.")
    audit_client = FakeClient({"claims": [{"requirement_id": "R-1", "claim_excerpt": "Created answer.py.",
                                         "citations": [], "assessment": "unverifiable"}]})
    audit_path, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                    requirements_path=requirements_path, final_path=final,
                                    client_factory=lambda *_: audit_client)
    assert code == 0
    records = accounting(directory)
    for phase, path, client, record in zip(
        ("requirements", "claim_audit"), (requirements_path, audit_path),
        (requirements_client, audit_client), records, strict=True,
    ):
        assert client.messages[0]["content"] == select_prompt(phase, selected)[1]
        assert load_object(path)["luna_call"] == {"path": "luna-calls.jsonl", "call_id": record["call_id"]}
        assert record["call_id"] == f"{phase}-{selected}-1"
        assert record["reasoning_effort"] == "low"
    # Replayed events preserve the original reference even after version changes.
    monkeypatch.setenv(PROMPT_VERSION_ENV, "v1" if selected == "v2" else "v2")
    assert invoke(directory, prompt, requirements_client) == (requirements_path, 0)
    assert requirements_client.calls == 1 and len(accounting(directory)) == 2


@pytest.mark.parametrize("version", ["", "v3", "2", "../../other"])
def test_invalid_prompt_version_rejected_before_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str,
) -> None:
    from controller.v3_prompts import PROMPT_VERSION_ENV

    monkeypatch.setenv(PROMPT_VERSION_ENV, version)
    directory, prompt = setup_session(tmp_path)
    client = FakeClient(rows())
    with pytest.raises(InputError, match="must be v1 or v2"):
        invoke(directory, prompt, client)
    assert client.calls == 0
    assert not (directory / "luna-calls.jsonl").exists()
    assert not (directory / "evidence/requirements-allocation.json").exists()


def test_prompt_version_switch_cannot_bypass_interrupted_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from controller.v3_prompts import PROMPT_VERSION_ENV

    directory, prompt = setup_session(tmp_path)
    retain(directory, "evidence/requirements-allocation.json",
           json.dumps({"call_id": "requirements-v1-1", "session_id": SESSION}).encode())
    monkeypatch.setenv(PROMPT_VERSION_ENV, "v2")
    client = FakeClient(rows())
    path, code = invoke(directory, prompt, client)
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert client.calls == 0 and not (directory / "luna-calls.jsonl").exists()


def test_failed_call_keeps_prompt_version_in_reference(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from controller.v3_prompts import PROMPT_VERSION_ENV

    monkeypatch.setenv(PROMPT_VERSION_ENV, "v2")
    directory, prompt = setup_session(tmp_path)
    path, code = invoke(directory, prompt, FakeClient(rows(), fail=True))
    record, = accounting(directory)
    assert code == 2 and record["status"] == "error"
    assert record["call_id"] == load_object(path)["luna_call"]["call_id"] == "requirements-v2-1"


def test_requirements_schema_checks_accounting_and_duplicate_event(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    client = FakeClient(rows())
    path, code = invoke(directory, prompt, client)
    assert code == 0
    value = load_object(path)
    validate_requirements(value, directory, SESSION)
    assert value["state"] == "ready"
    assert [row["id"] for row in value["requirements"]] == ["R-1", "R-2", "R-3"]
    assert value["requirements"][0]["check"] == {"type": "file_exists", "path": "answer.py"}
    assert value["requirements"][1]["check"]["type"] == "unavailable"
    assert value["requirements"][2]["check"]["argv"] == ["python", "-m", "unittest", "discover", "-v"]
    assert accounting(directory)[0]["usd"] == pytest.approx((80 * .1 + 20 * .01 + 50 * .5) / 1e6)
    assert invoke(directory, prompt, client) == (path, 0)
    assert client.calls == len(accounting(directory)) == 1
    assert "check" not in json.loads(client.messages[1]["content"])


def test_unanswered_questions_are_preserved(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    value = rows()
    value["open_questions"] = [{"text": "Which sort key?", "requirement_numbers": [2]}]
    path, code = invoke(directory, prompt, FakeClient(value))
    result = load_object(path)
    assert code == 0 and result["state"] == "pending_questions"
    assert result["open_questions"] == [{"id": "Q-1", "text": "Which sort key?", "requirement_ids": ["R-2"], "answer": None}]
    validate_requirements(result, directory, SESSION)


@pytest.mark.parametrize("mode,status", [("error", "error"), ("timeout", "timeout"),
                                          ("mismatch", "pin_mismatch"), ("missing", "error"),
                                          ("schema", "error"), ("excerpt", "error"), ("empty", "error")])
def test_failures_are_unavailable_recorded_once(tmp_path: Path, mode: str, status: str) -> None:
    directory, prompt = setup_session(tmp_path)
    value = rows()
    if mode == "schema":
        value["requirements"][0]["check"] = {"type": "command", "argv": ["evil"]}
    if mode == "excerpt":
        value["requirements"][0]["source_excerpt"] = "not in request"
    if mode == "empty":
        value["requirements"] = []
    client = FakeClient(value, fail=mode in {"error", "timeout"}, timeout=mode == "timeout",
                        model="other" if mode == "mismatch" else None if mode == "missing" else "gpt-6-luna")
    path, code = invoke(directory, prompt, client)
    result = load_object(path)
    assert code == 2 and result["state"] == "unavailable" and result["requirements"] == []
    schema_validator("requirements.schema.json").validate(result)
    record = accounting(directory)[0]
    assert record["status"] == status and record["usd"] is not None
    if mode == "missing":
        assert record["error"] == "identity_unobserved" and record["model"] is None
    assert invoke(directory, prompt, client)[1] == 2
    assert len(accounting(directory)) == client.calls == 1
    if status == "pin_mismatch" or mode == "missing":
        pin = load_object(directory / "pin-check.json")
        schema_validator("pin-check.schema.json").validate(pin)
        assert pin["status"] == "disabled"


@pytest.mark.parametrize("mode", ["disabled", "missing", "session", "hash", "model", "price"])
def test_pin_failure_makes_no_provider_invocation(tmp_path: Path, mode: str) -> None:
    directory, prompt = setup_session(tmp_path)
    pin = load_object(directory / "pin-check.json")
    if mode == "disabled":
        pin.update(status="disabled", reason_codes=["model_missing"])
    elif mode == "missing":
        pin = {}
    elif mode == "session":
        pin["session_id"] = "other"
    elif mode == "hash":
        pin["model_list"]["sha256"] = "0" * 64
    elif mode == "model":
        data = b'{"models":["gpt-6-luna-new"]}'
        (directory / pin["model_list"]["path"]).write_bytes(data)
        pin["model_list"]["sha256"] = digest(data)
    else:
        data = b'{"models":{}}'
        (directory / pin["pricing_snapshot"]["path"]).write_bytes(data)
        pin["pricing_snapshot"]["sha256"] = digest(data)
    atomic_json(directory / "pin-check.json", pin)
    client = FakeClient(rows())
    path, code = invoke(directory, prompt, client)
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert client.calls == 0 and not (directory / "luna-calls.jsonl").exists()


@pytest.mark.parametrize("kind,text", [
    ("named_file", "Add `/tmp/output.py`."), ("named_file", "Add `../output.py`."),
    ("named_file", "Add C:\\temp\\output.py."), ("named_file", "Add /tmp/output.py."),
    ("protected_file", "Preserve `../data.json`."),
    ("named_command", "Run `python -m pytest && curl example.com`."),
    ("test_command", "Run `python -m pytest /tmp/tests`."),
    ("test_command", "Run `python -m pytest --confcutdir=../tests`."),
    ("test_command", "Run `python -m pytest $(whoami)`."),
    ("named_command", "Run `python -c 'print(1)'`."),
    ("named_command", "Run `python -m pytest > result.txt`."),
])
def test_unsafe_checks_are_unavailable(tmp_path: Path, kind: str, text: str) -> None:
    check = derive_check(kind, text, text, tmp_path, {})
    assert check["type"] == "unavailable" and check["reason"]


def test_missing_protected_ambiguous_file_and_symlink(tmp_path: Path) -> None:
    for text in ["Preserve `missing.json`.", "Preserve a.py and b.py."]:
        assert derive_check("protected_file", text, text, tmp_path, {})["type"] == "unavailable"
    (tmp_path / "outside").symlink_to(tmp_path.parent, target_is_directory=True)
    text = "Create `outside/output.py`."
    assert derive_check("named_file", text, text, tmp_path, {})["type"] == "unavailable"
    with pytest.raises(ValueError):
        safe_argv("python -m pytest outside/tests", tmp_path)


def test_configured_checks_capture_real_baselines(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def health(value: int = 1) -> int:\n    return value\n")
    (tmp_path / "input.json").write_text("{}")
    specs = [
        ("behavior", "Return healthy.", {"type": "command", "argv": ["python", "-m", "unittest"]}),
        ("constraint", "Preserve signatures.", {"type": "signature_snapshot", "path": "app.py", "identifiers": ["health()"]}),
        ("constraint", "Preserve inputs.", {"type": "input_immutability", "argv": ["python", "-m", "unittest"], "inputs": ["input.json"]}),
    ]
    config = {"checks": [{"kind": kind, "source_excerpt": text, "check": spec} for kind, text, spec in specs]}
    checks = [derive_check(kind, text, text, tmp_path, config) for kind, text, _ in specs]
    assert [check["type"] for check in checks] == ["command", "signature_snapshot", "input_immutability"]
    assert checks[0]["origin"] == "project_config"
    assert checks[1]["baseline_sha256"] == digest(signature_bytes(tmp_path / "app.py", ["health()"]))
    assert checks[2]["inputs"][0]["sha256"] == digest(b"{}")
    baseline = signature_bytes(tmp_path / "app.py", ["health()"])
    (tmp_path / "app.py").write_text("def health(value: int = 1) -> int:\n    return 42\n")
    assert signature_bytes(tmp_path / "app.py", ["health()"]) == baseline
    text = "Do not edit `app.py`."
    assert derive_check("protected_file", text, text, tmp_path, {})["baseline_sha256"] == digest((tmp_path / "app.py").read_bytes())


def test_claim_audit_citations_verified_and_later_message_stale(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    requirements_path, _ = invoke(directory, prompt, FakeClient(rows()))
    retain(directory, "evidence/test.txt", b"3 tests passed\n")
    final = tmp_path / "final.txt"
    final.write_text("Tests passed: `evidence/test.txt`. Created answer.py.")
    value = {"claims": [{"requirement_id": "R-3", "claim_excerpt": "Tests passed",
                          "citations": [{"citation_excerpt": "`evidence/test.txt`"}], "assessment": "supported"}]}
    client = FakeClient(value)
    kwargs = dict(session_id=SESSION, artifacts=directory, requirements_path=requirements_path,
                  final_path=final, client_factory=lambda *_: client)
    path, code = run_operation("claim_audit", **kwargs)
    audit = load_object(path)
    _audit_validator().validate(audit)
    assert code == 0 and audit["status"] == "complete"
    evidence = audit["claims"][0]["cited_evidence"][0]
    assert evidence["sha256"] == digest(b"3 tests passed\n") and evidence["excerpt"] == "3 tests passed\n"
    assert len(accounting(directory)) == 2
    final.write_text("Changed after repair.")
    run_operation("claim_audit", **kwargs)
    stale = load_object(path)
    assert stale["status"] == "stale" and stale["audited_final_message"] == audit["audited_final_message"]
    assert len(accounting(directory)) == 2 and client.calls == 1


@pytest.mark.parametrize("citation", ["`../outside.txt`", "`/tmp/out.txt`", "`evidence/missing.txt`", "`evidence/test.txt` " + "0" * 64])
def test_forged_citations_are_unsupported(tmp_path: Path, citation: str) -> None:
    directory, prompt = setup_session(tmp_path)
    requirements_path, _ = invoke(directory, prompt, FakeClient(rows()))
    retain(directory, "evidence/test.txt", b"passed")
    final = tmp_path / "final.txt"
    final.write_text("Tests passed: " + citation)
    client = FakeClient({"claims": [{"requirement_id": "R-3", "claim_excerpt": "Tests passed",
                                     "citations": [{"citation_excerpt": citation}], "assessment": "supported"}]})
    path, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                               requirements_path=requirements_path, final_path=final,
                               client_factory=lambda *_: client)
    assert code == 0 and load_object(path)["claims"][0]["assessment"] == "unsupported"


@pytest.mark.parametrize("models", [["gpt-6-luna"], ["gpt-other"], [], ["gpt-6-luna", "gpt-other"]])
def test_native_pin_and_one_invocation_guard(tmp_path: Path, models: list[str], caplog: pytest.LogCaptureFixture) -> None:
    book = load_object(PACKAGE_DIR / "prices.yaml")
    calls: list[dict[str, Any]] = []
    parent = os.environ.get("HARNESS_NESTED")

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(kwargs)
        assert kwargs["env"]["HARNESS_NESTED"] == "1" and kwargs["shell"] is False
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        events = [json.dumps({"type": "turn_context", "payload": {"model": model}}) for model in models]
        events.append(json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 50}}))
        return subprocess.CompletedProcess(argv, 0, "\n".join(events), "")
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"], executable="/mock/codex")
    client = PinnedLunaClient(Prices.from_dict(book["models"]["gpt-6-luna"]), "test", runner=runner, config=config)
    with caplog.at_level(logging.INFO):
        if models == ["gpt-6-luna"]:
            assert client.generate(REQUIREMENTS, [{"role": "user", "content": "input"}]) == rows()
        else:
            with pytest.raises(PinMismatch if models else IdentityUnobserved):
                client.generate(REQUIREMENTS, [{"role": "user", "content": "input"}])
    with pytest.raises(BackendError, match="second"):
        client.generate(REQUIREMENTS, [{"role": "user", "content": "input"}])
    assert len(calls) == 1 and 'control_call ' in caplog.text
    assert os.environ.get("HARNESS_NESTED") == parent


def test_timeout_uses_override_retains_usage_and_records_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    directory, prompt = setup_session(tmp_path)
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", "9.5")
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        assert kwargs["timeout"] == 9.5
        events = json.dumps({"type": "session.started", "model": "gpt-6-luna"}) + "\n" + json.dumps({
            "type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 1}})
        raise subprocess.TimeoutExpired(argv, 9.5, output=events.encode())
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"], executable="/mock/codex")
    with caplog.at_level(logging.INFO):
        path, code = run_operation("requirements", session_id=SESSION, artifacts=directory, prompt_path=prompt,
                                   client_factory=lambda prices, ref: PinnedLunaClient(prices, ref, runner=runner, config=config))
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert count == 1 and accounting(directory)[0]["status"] == "timeout"
    assert accounting(directory)[0]["usd"] is not None
    assert caplog.text.count('control_failure ') == 1
    assert '"timeout_seconds": 9.5' in caplog.text


def test_invalid_artifact_root_and_allocation_refuse_calls(tmp_path: Path) -> None:
    with pytest.raises(InputError):
        artifact_root(tmp_path / "elsewhere", SESSION)
    directory, prompt = setup_session(tmp_path)
    (directory / "evidence/requirements-allocation.json").write_text("{}")
    client = FakeClient(rows())
    assert invoke(directory, prompt, client)[1] == 2 and client.calls == 0


def test_cli_new_operations_pin_failure_and_success_stdout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    directory, prompt = setup_session(tmp_path)
    client = FakeClient(rows())
    monkeypatch.setattr("controller.v3.PinnedLunaClient", lambda *_: client)
    assert main(["requirements", "--prompt", str(prompt), "--session-id", SESSION, "--artifacts", str(directory)]) == 0
    assert capsys.readouterr().out == str(directory / "requirements.json") + "\n"
    final = tmp_path / "final.txt"
    final.write_text("Nothing claimed.")
    monkeypatch.setattr("controller.v3.PinnedLunaClient", lambda *_: FakeClient({"claims": []}))
    assert main(["claim-audit", "--requirements", str(directory / "requirements.json"), "--final-message", str(final),
                 "--session-id", SESSION, "--artifacts", str(directory)]) == 0
    assert capsys.readouterr().out == str(directory / "claim-audit.json") + "\n"


def test_partial_model_excerpt_cannot_hide_shell_syntax(tmp_path: Path) -> None:
    request = "Run `python -m pytest && curl example.com`."
    check = derive_check("test_command", "python -m pytest", request, tmp_path, {})
    assert check["type"] == "unavailable"
    request = "Add `/tmp/out.py`."
    assert derive_check("named_file", "out.py", request, tmp_path, {})["type"] == "unavailable"


def test_unknown_usage_stays_null_and_claim_failure_is_accounted(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)

    class UnknownClient(FakeClient):
        def usage(self) -> Usage:
            return Usage(None, None, None, .1)
    path, _ = invoke(directory, prompt, UnknownClient(rows()))
    assert accounting(directory)[0]["usd"] is None
    final = tmp_path / "final.txt"
    final.write_text("Done.")
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: UnknownClient({}, fail=True))
    value = load_object(audit)
    _audit_validator().validate(value)
    assert code == 2 and value["status"] == "unavailable"
    assert accounting(directory)[1]["usd"] is None and accounting(directory)[1]["status"] == "error"


@pytest.mark.parametrize("model", ["renamed", None])
def test_identity_failure_disables_later_phase_without_call(tmp_path: Path, model: str | None) -> None:
    directory, prompt = setup_session(tmp_path)
    path, _ = invoke(directory, prompt, FakeClient(rows(), model=model))
    final = tmp_path / "final.txt"
    final.write_text("Done.")
    client = FakeClient({"claims": []})
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: client)
    assert code == 2 and load_object(audit)["status"] == "unavailable"
    assert client.calls == 0 and len(accounting(directory)) == 1


@pytest.mark.parametrize("mutate", ["unknown_id", "invented_excerpt", "invented_citation"])
def test_audit_output_cannot_invent_claims(tmp_path: Path, mutate: str) -> None:
    directory, prompt = setup_session(tmp_path)
    path, _ = invoke(directory, prompt, FakeClient(rows()))
    final = tmp_path / "final.txt"
    final.write_text("Created answer.py.")
    claim = {"requirement_id": "R-1", "claim_excerpt": "Created answer.py.", "citations": [], "assessment": "supported"}
    if mutate == "unknown_id":
        claim["requirement_id"] = "R-99"
    elif mutate == "invented_excerpt":
        claim["claim_excerpt"] = "Tests passed"
    else:
        claim["citations"] = [{"citation_excerpt": "`evidence/invented.txt`"}]
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: FakeClient({"claims": [claim]}))
    assert code == 2 and load_object(audit)["status"] == "unavailable"
    assert accounting(directory)[1]["status"] == "error"


def test_no_citation_cannot_support_claim(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    path, _ = invoke(directory, prompt, FakeClient(rows()))
    final = tmp_path / "final.txt"
    final.write_text("Created answer.py.")
    client = FakeClient({"claims": [{"requirement_id": "R-1", "claim_excerpt": "Created answer.py.", "citations": [], "assessment": "supported"}]})
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: client)
    assert code == 0 and load_object(audit)["claims"][0]["assessment"] == "unverifiable"


def test_answers_require_visible_nonempty_strings_without_call(tmp_path: Path) -> None:
    from controller.v3 import record_answers
    directory, prompt = setup_session(tmp_path)
    value = rows()
    value["open_questions"] = [{"text": "Which key?", "requirement_numbers": [2]}]
    client = FakeClient(value)
    path, _ = invoke(directory, prompt, client)
    with pytest.raises(InputError):
        record_answers(artifacts=directory, session_id=SESSION, answers={"Q-1": ""})
    record_answers(artifacts=directory, session_id=SESSION, answers={"Q-1": "Sort by name ascending."})
    assert load_object(path)["state"] == "ready"
    assert load_object(path)["open_questions"][0]["answer"] == "Sort by name ascending."
    assert client.calls == len(accounting(directory)) == 1


def test_partial_citation_cannot_hide_forged_final_hash(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    path, _ = invoke(directory, prompt, FakeClient(rows()))
    retain(directory, "evidence/test.txt", b"3 tests passed\n")
    final = tmp_path / "final.txt"
    final.write_text("Tests passed: `evidence/test.txt` sha256=" + "0" * 64 + ".")
    client = FakeClient({"claims": [{"requirement_id": "R-3", "claim_excerpt": "Tests passed",
                                     "citations": [{"citation_excerpt": "`evidence/test.txt`"}], "assessment": "supported"}]})
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: client)
    assert code == 0 and load_object(audit)["claims"][0]["assessment"] == "unsupported"


def test_explicit_exit_code_and_unquoted_commands_derive_from_request(tmp_path: Path) -> None:
    for kind, text, expected in [
        ("named_command", "Run `python -m compileall app` with exit code 1.", 1),
        ("named_command", "Run python verify.py.", 0),
        ("test_command", "Verify with python -m unittest discover -v.", 0),
    ]:
        check = derive_check(kind, text, text, tmp_path, {})
        assert check["type"] == "command" and check["expected_exit_code"] == expected
        assert check["origin"] == "request"


def test_timeout_without_native_identity_remains_unobserved_and_once(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"], executable="/mock/codex")
    path, code = run_operation("requirements", session_id=SESSION, artifacts=directory, prompt_path=prompt,
                               client_factory=lambda prices, ref: PinnedLunaClient(prices, ref, runner=runner, config=config))
    record = accounting(directory)[0]
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert record["status"] == "error" and record["model"] is None
    assert record["error"] == "identity_unobserved"
    assert record["usd"] is record["input_tokens"] is record["output_tokens"] is None
    assert count == 1


def test_native_failure_preserves_known_usage_without_retry(tmp_path: Path) -> None:
    directory, prompt = setup_session(tmp_path)
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal count
        count += 1
        events = json.dumps({"type": "session_meta", "payload": {"model": "gpt-6-luna"}}) + "\n" + json.dumps({
            "type": "turn.completed", "usage": {"input_tokens": 200, "cached_input_tokens": 20, "output_tokens": 10}})
        return subprocess.CompletedProcess(argv, 17, events, "do not expose provider stderr")
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"], executable="/mock/codex")
    path, code = run_operation("requirements", session_id=SESSION, artifacts=directory, prompt_path=prompt,
                               client_factory=lambda prices, ref: PinnedLunaClient(prices, ref, runner=runner, config=config))
    record = accounting(directory)[0]
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert record["status"] == "error" and record["model"] == "gpt-6-luna"
    assert record["usd"] == pytest.approx((180 * .1 + 20 * .01 + 10 * .5) / 1e6)
    assert count == 1


def test_atomic_replace_leaves_valid_old_artifact_until_replacement(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    atomic_json(path, {"old": True})
    with pytest.raises(ValueError):
        atomic_json(path, {"bad": float("nan")})
    assert load_object(path) == {"old": True}


@pytest.mark.parametrize("missing", [True, False])
def test_missing_or_empty_final_message_publishes_unavailable_without_call(tmp_path: Path, missing: bool) -> None:
    directory, prompt = setup_session(tmp_path)
    path, _ = invoke(directory, prompt, FakeClient(rows()))
    final = tmp_path / "final.txt"
    if not missing:
        final.write_text("  \n")
    client = FakeClient({"claims": []})
    audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                requirements_path=path, final_path=final,
                                client_factory=lambda *_: client)
    value = load_object(audit)
    _audit_validator().validate(value)
    assert code == 2 and value["status"] == "unavailable" and "final message unavailable" in value["reason"]
    assert value["audited_final_message"] is None and client.calls == 0
    assert len(accounting(directory)) == 1
