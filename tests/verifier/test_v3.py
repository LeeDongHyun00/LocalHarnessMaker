"""V3 fixtures use injected runners; real Seatbelt acceptance stays host-only."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from verifier.__main__ import main
from verifier.ledger import InvalidLedger, validate_ledger
from verifier.python_identity import identifier_found, signature_snapshot_bytes
from verifier.sandbox import Execution, run_argv
from verifier.schema import validate
from verifier.stop_text import repair_instruction, reserve_ledger_request
from verifier.v3_checks import evaluate_row
from verifier.v3_io import confined, digest, encoded, reference, session_root
from verifier.v3_report import check_requirements


SESSION = "native/session ☃"
SOURCE = b"COUNT = 7\ndef health(x: int = 1) -> bool:\n    return True\n"
KINDS = ["file_exists", "file_unchanged", "signature_snapshot", "input_immutability", "command", "test_command"]


@pytest.fixture
def v3(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    root = workspace / ".localharness/v3/sessions" / digest(SESSION.encode())
    root.mkdir(parents=True)
    (root / "evidence").mkdir()
    (workspace / "app.py").write_bytes(SOURCE)
    (workspace / "input.txt").write_bytes(b"original\n")
    (root / "evidence/prompt.txt").write_text("Preserve health. Run checks. Add output.")
    call = json.loads(Path("schemas/examples/luna-call.json").read_text())
    call["session_id"] = SESSION
    audit = dict(call, call_id="audit-1", phase="claim_audit")
    (root / "luna-calls.jsonl").write_bytes(encoded(call).replace(b"\n", b"") + b"\n" + encoded(audit).replace(b"\n", b"") + b"\n")
    write_table(root, [make_row("file_exists")])
    return workspace, root


def make_row(kind: str, number: int = 1) -> dict[str, Any]:
    check: dict[str, Any]
    if kind in {"command", "test_command"}:
        check = {"type": "command", "argv": ["python", "-m", "unittest", "discover", "-v"],
                 "cwd": ".", "expected_exit_code": 0, "origin": "request"}
        row_kind = "test_command" if kind == "test_command" else "named_command"
    elif kind == "input_immutability":
        check = {"type": kind, "argv": ["python", "-c", "print(1)"], "cwd": ".", "expected_exit_code": 0,
                 "inputs": [{"path": "input.txt", "sha256": digest(b"original\n")}]}
        row_kind = "constraint"
    elif kind == "signature_snapshot":
        check = {"type": kind, "path": "app.py", "identifiers": ["health"],
                 "baseline_sha256": digest(signature_snapshot_bytes(SOURCE, ["health"]))}
        row_kind = "constraint"
    elif kind == "file_unchanged":
        check = {"type": kind, "path": "app.py", "baseline_sha256": digest(SOURCE)}
        row_kind = "protected_file"
    elif kind == "file_exists":
        check = {"type": kind, "path": "app.py"}
        row_kind = "named_file"
    else:
        check = {"type": "unavailable", "reason": "no configured oracle"}
        row_kind = "behavior"
    return {"id": f"R-{number}", "number": number, "text": "Preserve health.",
            "kind": row_kind, "source_excerpt": "Preserve health.", "check": check}


def write_table(root: Path, rows: list[dict[str, Any]], **changes: Any) -> dict[str, Any]:
    table = {"schema_version": 3, "session_id": SESSION, "state": "ready", "requirements": rows,
             "prompt": {"path": "evidence/prompt.txt", "sha256": digest((root / "evidence/prompt.txt").read_bytes())},
             "open_questions": [], "luna_call": {"path": "luna-calls.jsonl", "call_id": "requirements-1"}}
    table.update(changes)
    validate(table, "requirements.schema.json")
    (root / "requirements.json").write_bytes(encoded(table))
    return table


def report(root: Path) -> dict[str, Any]:
    result = json.loads((root / "completion-report.json").read_bytes())
    validate(result, "completion-report.schema.json")
    reference(root, result["requirements"])
    for item in result["items"]:
        for evidence in item["evidence"]:
            reference(root, evidence)
    return result


def run(v3: tuple[Path, Path], round_number: int = 1, **kwargs: Any) -> dict[str, Any]:
    workspace, root = v3
    return check_requirements(root / "requirements.json", workspace, SESSION, root, round_number, **kwargs)


def ok(argv: list[str], workspace: Path, cwd: Path, timeout: float) -> Execution:
    assert 0 < timeout <= 120 and cwd.is_relative_to(workspace)
    return Execution(exit_code=0, stdout="OK\n")


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("outcome", ["pass", "fail", "unverifiable"])
def test_every_check_kind(v3: tuple[Path, Path], kind: str, outcome: str) -> None:
    workspace, root = v3
    row = make_row(kind)
    if outcome == "fail":
        if kind == "file_exists":
            row["check"]["path"] = "missing.py"
        elif kind == "file_unchanged":
            (workspace / "app.py").write_bytes(SOURCE + b"# edited\n")
        elif kind == "signature_snapshot":
            (workspace / "app.py").write_bytes(SOURCE.replace(b"x: int = 1", b"y: int = 2"))
    elif outcome == "unverifiable" and kind in {"file_exists", "file_unchanged", "signature_snapshot"}:
        row["check"]["path"] = "../outside.py"
    def runner(argv: list[str], ws: Path, cwd: Path, timeout: float) -> Execution:
        if outcome == "unverifiable":
            return Execution(error="mock deadline expired")
        if kind == "input_immutability" and outcome == "fail":
            (workspace / "input.txt").write_bytes(b"changed")
        return Execution(exit_code=1 if outcome == "fail" and kind in {"command", "test_command"} else 0,
                         stdout_bytes=b"exact\xff\x00bytes\r\n", stderr_bytes=b"", stdout="lossy")
    write_table(root, [row])
    result = run(v3, runner=runner)
    saved = report(root)
    assert saved["items"][0]["status"] == outcome
    assert result["retry_warranted"] == (outcome == "fail")
    if kind in {"command", "test_command", "input_immutability"}:
        evidence = saved["items"][0]["evidence"]
        assert any(reference(root, e) == b"exact\xff\x00bytes\r\n" for e in evidence) if outcome != "unverifiable" else True


@pytest.mark.parametrize("kind", ["file_exists", "file_unchanged", "signature_snapshot", "input_immutability", "command"])
@pytest.mark.parametrize("spelling", ["absolute", "parent", "symlink"])
def test_check_path_confinement(v3: tuple[Path, Path], kind: str, spelling: str) -> None:
    workspace, root = v3
    outside = workspace.parent / "outside.py"
    outside.write_bytes(SOURCE)
    (workspace / "escape.py").symlink_to(outside)
    path = {"absolute": str(outside), "parent": "../outside.py", "symlink": "escape.py"}[spelling]
    row = make_row(kind)
    if kind == "input_immutability":
        row["check"]["inputs"][0]["path"] = path
    elif kind == "command":
        row["check"]["cwd"] = path
    else:
        row["check"]["path"] = path
    def forbidden(*args: Any) -> Execution:
        pytest.fail("unsafe path must not reach runner")
    write_table(root, [row])
    assert run(v3, runner=forbidden)["unverifiable_rows"] == ["R-1"]
    assert outside.read_bytes() == SOURCE
    report(root)


def test_unavailable_and_pending_never_execute(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    write_table(root, [make_row("unavailable")])
    assert not run(v3)["retry_warranted"]
    assert report(root)["items"][0]["status"] == "unverifiable"


@pytest.mark.parametrize("state", ["pending_questions", "unavailable"])
def test_unready_table_never_assumes_answer(v3: tuple[Path, Path], state: str) -> None:
    _, root = v3
    questions = [{"id": "Q-1", "text": "Which output?", "requirement_ids": ["R-1"], "answer": None}]
    write_table(root, [make_row("command")], state=state, open_questions=questions)
    def forbidden(*args: Any) -> Execution:
        pytest.fail("unanswered work must not run")
    assert run(v3, runner=forbidden)["unverifiable_rows"] == ["R-1"]
    report(root)


def test_zero_rows_is_not_pass(v3: tuple[Path, Path]) -> None:
    _, root = v3
    write_table(root, [], state="unavailable", luna_call=None)
    assert run(v3)["overall"] == "fail"
    report(root)


@pytest.mark.parametrize("execution", [
    Execution(exit_code=1, stderr="ModuleNotFoundError: example"),
    Execution(exit_code=1, stderr="Traceback (most recent call last):\nValueError: bad input"),
    Execution(exit_code=None), Execution(exit_code=-9), Execution(error="sandbox unavailable"),
])
def test_infrastructure_is_not_executed_failure(v3: tuple[Path, Path], execution: Execution) -> None:
    _, root = v3
    write_table(root, [make_row("command")])
    assert run(v3, runner=lambda *args: execution)["unverifiable_rows"] == ["R-1"]
    assert report(root)["retry"]["used"] == 0


@pytest.mark.parametrize("exception", [OSError("missing executable"), subprocess.TimeoutExpired(["python"], 1), RuntimeError("runner error")])
def test_runner_exceptions_are_unverifiable(v3: tuple[Path, Path], exception: Exception) -> None:
    _, root = v3
    write_table(root, [make_row("command")])
    def broken(*args: Any) -> Execution:
        raise exception
    assert not run(v3, runner=broken)["retry_warranted"]
    assert report(root)["items"][0]["status"] == "unverifiable"


@pytest.mark.parametrize("state", ["missing", "changed", "removed-by-probe"])
def test_input_baseline_and_missing_fixtures(v3: tuple[Path, Path], state: str) -> None:
    workspace, root = v3
    row = make_row("input_immutability")
    if state == "missing":
        row["check"]["inputs"][0]["path"] = "missing-input"
    elif state == "changed":
        row["check"]["inputs"][0]["sha256"] = "0" * 64
    write_table(root, [row])
    def runner(*args: Any) -> Execution:
        assert state != "missing"
        if state == "removed-by-probe":
            (workspace / "input.txt").rename(workspace / "moved-input.txt")
        return Execution(exit_code=0)
    result = run(v3, runner=runner)
    assert report(root)["items"][0]["status"] == ("unverifiable" if state == "missing" else "fail")
    assert result["retry_warranted"] == (state != "missing")


def test_expected_nonzero_and_cwd(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    (workspace / "sub").mkdir()
    row = make_row("command")
    row["check"].update(cwd="sub", expected_exit_code=7)
    write_table(root, [row])
    def runner(argv: list[str], ws: Path, cwd: Path, timeout: float) -> Execution:
        assert cwd == workspace / "sub" and argv == row["check"]["argv"]
        return Execution(exit_code=7)
    assert run(v3, runner=runner)["overall"] == "pass"
    report(root)


def test_rounds_and_duplicate_stop(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    write_table(root, [dict(make_row("file_exists"), check={"type": "file_exists", "path": "output"}), make_row("unavailable", 2)])
    assert run(v3)["retry_warranted"]
    first = report(root)
    assert first["retry"]["used"] == 1
    text = repair_instruction(first, root)
    assert text and "R-1" in text and "R-2" not in text
    assert not run(v3)["retry_warranted"]
    with pytest.raises(ValueError, match="not settled"):
        reserve_ledger_request(root)
    (workspace / "output").write_bytes(b"done")
    second = run(v3, 2)
    assert not second["retry_warranted"] and second["failed_rows"] == []
    assert report(root)["retry"] == first["retry"]
    assert repair_instruction(report(root), root) is None
    ledger_text = reserve_ledger_request(root)
    assert ledger_text and "validation null" in ledger_text and "Preserve the application completion summary" in ledger_text
    assert reserve_ledger_request(root) is None
    assert run(v3, 2) == second
    with pytest.raises(ValueError, match="rewind"):
        run(v3)


def test_repeated_failure_advises_without_retry(v3: tuple[Path, Path]) -> None:
    _, root = v3
    row = make_row("file_exists")
    row["check"]["path"] = "missing"
    write_table(root, [row])
    run(v3)
    assert run(v3, 2)["retry_warranted"] is False
    assert report(root)["escalation_advice"]["recommendation"] == "human_review"
    assert reserve_ledger_request(root) is not None


def test_round_two_without_failure_is_error(v3: tuple[Path, Path]) -> None:
    with pytest.raises(ValueError, match="round 2 requires"):
        run(v3, 2)
    run(v3)
    with pytest.raises(ValueError, match="round 2 requires"):
        run(v3, 2)


def write_audit(root: Path, *, bad_hash: bool = False) -> Path:
    final = b"R-1: completed health."
    (root / "evidence/final.txt").write_bytes(final)
    audit = {"status": "complete", "audited_final_message": {"path": "evidence/final.txt", "sha256": digest(final)},
             "claims": [{"requirement_id": "R-1", "claim_excerpt": final.decode(), "assessment": "supported",
                         "cited_evidence": [{"kind": "file", "path": "evidence/prompt.txt",
                                            "sha256": "0" * 64 if bad_hash else digest((root / "evidence/prompt.txt").read_bytes()),
                                            "excerpt": "Preserve health."}]}],
             "reason": None, "luna_call": {"path": "luna-calls.jsonl", "call_id": "audit-1"}}
    path = root / "audit.json"
    path.write_bytes(encoded(audit))
    return path


@pytest.mark.parametrize("bad_hash", [False, True])
def test_claim_hashes_and_stale_audit(v3: tuple[Path, Path], bad_hash: bool) -> None:
    _, root = v3
    row = make_row("file_exists")
    row["check"]["path"] = "missing"
    write_table(root, [row])
    audit_path = write_audit(root, bad_hash=bad_hash)
    result = run(v3, claim_audit=audit_path, final_message=root / "evidence/final.txt")
    first = report(root)
    assert first["claim_audit"]["claims"][0]["assessment"] == ("unsupported" if bad_hash else "supported")
    for citation in first["claim_audit"]["claims"][0]["cited_evidence"]:
        reference(root, citation)
    assert result["failed_rows"] == ["R-1"]  # audit cannot override code
    (root / "evidence/revised.txt").write_text("R-1 remains failed; ledger saved.")
    run(v3, 2, final_message=root / "evidence/revised.txt")
    second = report(root)
    assert second["claim_audit"]["status"] == "stale"
    assert second["claim_audit"]["audited_final_message"] == first["claim_audit"]["audited_final_message"]


@pytest.mark.parametrize("source", ["report", "supplied", "sidecar"])
@pytest.mark.parametrize("changed_final", [False, True])
@pytest.mark.parametrize("bad_hash", [False, True])
def test_round_two_retains_audit(
    v3: tuple[Path, Path], source: str, changed_final: bool, bad_hash: bool,
) -> None:
    workspace, root = v3
    row = make_row("file_exists")
    row["check"]["path"] = "output.py"
    write_table(root, [row])
    audit_path = write_audit(root, bad_hash=bad_hash)
    final = root / "evidence/final.txt"
    calls = (root / "luna-calls.jsonl").read_bytes()
    assert run(v3, claim_audit=audit_path if source == "report" else None,
               final_message=final)["retry_warranted"]
    first = report(root)
    if source == "report":
        # A later supplied replacement must not overwrite the verified original.
        audit_path.write_text("malformed replacement")
    elif source == "sidecar":
        (root / "claim-audit.json").write_bytes(audit_path.read_bytes())
    audit_bytes = audit_path.read_bytes()
    sidecar = root / "claim-audit.json"
    sidecar_bytes = sidecar.read_bytes() if sidecar.exists() else None
    (workspace / "output.py").write_text("# repaired\n")
    if changed_final:
        final = root / "evidence/revised.txt"
        final.write_text("Created output.py. R-1: completed health.")
    supplied = audit_path if source in {"report", "supplied"} else None
    assert run(v3, 2, claim_audit=supplied, final_message=final) == {
        "overall": "pass", "failed_rows": [], "unverifiable_rows": [], "retry_warranted": False,
    }
    saved = report(root)
    audit = saved["claim_audit"]
    assert audit["status"] == ("stale" if changed_final else "complete")
    assert audit["audited_final_message"]["sha256"] == digest(b"R-1: completed health.")
    assert reference(root, audit["audited_final_message"]) == b"R-1: completed health."
    assert audit["luna_call"] == {"path": "luna-calls.jsonl", "call_id": "audit-1"}
    claim = audit["claims"][0]
    assert claim["assessment"] == ("unsupported" if bad_hash else "supported")
    assert len(claim["cited_evidence"]) == (0 if bad_hash else 1)
    if source == "report":
        assert audit["claims"] == first["claim_audit"]["claims"]
    assert saved["retry"] == first["retry"]
    # Later bookkeeping Stop events preserve citation results and recompute freshness.
    run(v3, 2, final_message=root / "evidence/final.txt")
    refreshed = report(root)["claim_audit"]
    assert refreshed["status"] == "complete"
    assert refreshed["claims"] == audit["claims"]
    assert refreshed["audited_final_message"] == audit["audited_final_message"]
    assert (root / "luna-calls.jsonl").read_bytes() == calls
    assert audit_path.read_bytes() == audit_bytes
    if sidecar_bytes is not None:
        assert sidecar.read_bytes() == sidecar_bytes


def test_round_two_without_audit_stays_unavailable(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    row = make_row("file_exists")
    row["check"]["path"] = "output.py"
    write_table(root, [row])
    final = root / "evidence/final.txt"
    final.write_text("Created output.py.")
    calls = (root / "luna-calls.jsonl").read_bytes()
    assert run(v3, final_message=final)["retry_warranted"]
    original = report(root)["claim_audit"]
    (workspace / "output.py").write_text("# repaired\n")
    assert run(v3, 2, final_message=final)["overall"] == "pass"
    assert report(root)["claim_audit"] == original == {
        "status": "unavailable", "audited_final_message": None, "claims": [],
        "reason": "no claim audit supplied", "luna_call": None,
    }
    assert (root / "luna-calls.jsonl").read_bytes() == calls


@pytest.mark.parametrize("mutation", ["escape", "unknown", "accounting", "excerpt", "missing"])
def test_invented_claim_provenance(v3: tuple[Path, Path], mutation: str) -> None:
    _, root = v3
    path = write_audit(root)
    audit = json.loads(path.read_bytes())
    if mutation == "escape":
        audit["claims"][0]["cited_evidence"][0]["path"] = "../outside"
    elif mutation == "unknown":
        audit["claims"][0]["requirement_id"] = "R-99"
    elif mutation == "accounting":
        audit["luna_call"]["call_id"] = "invented"
    elif mutation == "excerpt":
        audit["claims"][0]["claim_excerpt"] = "Invented success"
    else:
        audit["claims"][0]["cited_evidence"][0]["path"] = "missing"
    path.write_bytes(encoded(audit))
    assert not run(v3, claim_audit=path, final_message=root / "evidence/final.txt")["retry_warranted"]
    saved = report(root)["claim_audit"]
    assert saved["status"] == "unavailable" if mutation in {"unknown", "accounting"} else saved["claims"][0]["assessment"] == "unsupported"


def test_missing_message_and_malformed_audit_remain_reportable(v3: tuple[Path, Path]) -> None:
    _, root = v3
    path = root / "audit.json"
    path.write_text('{"not": "an audit"}')
    assert run(v3, claim_audit=path, final_message=root / "absent-message")["overall"] == "pass"
    saved = report(root)
    assert saved["current_final_message"] is None
    assert saved["claim_audit"]["status"] == "unavailable"


def test_duplicate_stop_refreshes_message_without_check_or_audit_rerun(v3: tuple[Path, Path]) -> None:
    _, root = v3
    write_table(root, [make_row("command")])
    audit = write_audit(root)
    count = 0
    def runner(*args: Any) -> Execution:
        nonlocal count
        count += 1
        return Execution(exit_code=0)
    calls = (root / "luna-calls.jsonl").read_bytes()
    run(v3, runner=runner, claim_audit=audit, final_message=root / "evidence/final.txt")
    (root / "evidence/later.txt").write_text("Application summary retained. Ledger saved.")
    # A supplied replacement audit is ignored after the original was retained.
    audit.write_text("malformed replacement")
    assert not run(v3, runner=runner, claim_audit=audit, final_message=root / "evidence/later.txt")["retry_warranted"]
    assert count == 1 and report(root)["claim_audit"]["status"] == "stale"
    assert (root / "luna-calls.jsonl").read_bytes() == calls


def test_audited_bytes_survive_input_message_replacement(v3: tuple[Path, Path]) -> None:
    _, root = v3
    audit = write_audit(root)
    run(v3, claim_audit=audit, final_message=root / "evidence/final.txt")
    original = report(root)["claim_audit"]["audited_final_message"]
    (root / "evidence/final.txt").write_text("Application summary now includes ledger evidence.")
    run(v3, final_message=root / "evidence/final.txt")
    assert report(root)["claim_audit"]["status"] == "stale"
    assert reference(root, original) == b"R-1: completed health."


def test_malformed_audit_bytes_are_retained_without_blocking_report(v3: tuple[Path, Path]) -> None:
    _, root = v3
    bad = b"{invalid json\xff\n"
    path = root / "audit.json"
    path.write_bytes(bad)
    assert run(v3, claim_audit=path)["overall"] == "pass"
    assert report(root)["claim_audit"]["status"] == "unavailable"
    snapshots = list((root / "evidence").glob("original-claim-audit-*.bin"))
    assert len(snapshots) == 1 and snapshots[0].read_bytes() == bad


def test_report_evidence_tampering_is_rejected(v3: tuple[Path, Path]) -> None:
    _, root = v3
    run(v3)
    saved = report(root)
    (root / saved["items"][0]["evidence"][0]["path"]).write_text("changed evidence")
    before = (root / "completion-report.json").read_bytes()
    with pytest.raises(ValueError, match="hash mismatch"):
        run(v3)
    assert (root / "completion-report.json").read_bytes() == before


def test_budget_exhaustion_is_unverifiable(v3: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    _, root = v3
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "1")
    assert not run(v3, runner=ok)["retry_warranted"]
    assert report(root)["items"][0]["status"] == "unverifiable"


def test_check_never_delegates_judgments(v3: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    _, root = v3
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("historical judgment must not be invoked")
    monkeypatch.setattr("verifier.check.judge_criterion", forbidden)
    write_table(root, [make_row("unavailable")])
    assert run(v3)["unverifiable_rows"] == ["R-1"]


def write_ledger(root: Path, *, kind: str = "signature", value: str = "health(x: int=1) -> bool") -> Path:
    ledger = {"schema_version": 3, "session_id": SESSION,
              "requirements": {"path": "requirements.json", "sha256": digest((root / "requirements.json").read_bytes())},
              "decisions": [{"id": "D-1", "what": "Preserve the entry point.", "rationale": "Public callers rely on it.",
                             "fixes": [{"kind": kind, "value": value, "path": "app.py"}]}],
              "open_items": [], "validation": None}
    path = root / "ledger.json"
    validate(ledger, "ledger.schema.json")
    path.write_bytes(encoded(ledger))
    return path


@pytest.mark.parametrize("kind,value", [("name", "health"), ("signature", "health(x: int=1) -> bool"),
                                       ("constant", "COUNT"), ("constant", "COUNT = 7")])
def test_ledger_found_and_atomic_latest(v3: tuple[Path, Path], kind: str, value: str) -> None:
    workspace, root = v3
    path = write_ledger(root, kind=kind, value=value)
    result = validate_ledger(path, workspace, SESSION, root)
    validate(result, "ledger.schema.json")
    assert result["validation"]["status"] == "valid"
    assert result["validation"]["files"] == [{"path": "app.py", "sha256": digest(SOURCE)}]
    assert path.read_bytes() == (workspace / ".localharness/v3/latest-ledger.json").read_bytes()
    assert validate_ledger(path, workspace, SESSION, root)["validation"]["status"] == "valid"


@pytest.mark.parametrize("kind,value", [("name", "absent"), ("signature", "health()"), ("constant", "COUNT = 8")])
def test_ledger_missing_identity(v3: tuple[Path, Path], kind: str, value: str) -> None:
    workspace, root = v3
    path = write_ledger(root, kind=kind, value=value)
    result = validate_ledger(path, workspace, SESSION, root)
    validate(result, "ledger.schema.json")
    assert result["validation"]["status"] == "invalid"
    assert not result["validation"]["identifiers"][0]["found"]
    assert not (workspace / ".localharness/v3/latest-ledger.json").exists()


def test_ledger_hash_mismatch_on_revalidation(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    path = write_ledger(root)
    assert validate_ledger(path, workspace, SESSION, root)["validation"]["status"] == "valid"
    latest = (workspace / ".localharness/v3/latest-ledger.json").read_bytes()
    (workspace / "app.py").write_bytes(SOURCE + b"# unrelated edit still invalidates identity snapshot\n")
    result = validate_ledger(path, workspace, SESSION, root)
    validate(result, "ledger.schema.json")
    assert result["validation"]["status"] == "invalid" and "stale workspace hash" in result["validation"]["reason"]
    assert (workspace / ".localharness/v3/latest-ledger.json").read_bytes() == latest
    assert validate_ledger(path, workspace, SESSION, root)["validation"]["status"] == "invalid"
    assert (workspace / ".localharness/v3/latest-ledger.json").read_bytes() == latest


@pytest.mark.parametrize("mutation", ["parent", "absolute", "symlink", "unsupported", "forged", "coverage"])
def test_ledger_confinement_and_forged_validation(v3: tuple[Path, Path], mutation: str) -> None:
    workspace, root = v3
    path = write_ledger(root)
    ledger = validate_ledger(path, workspace, SESSION, root)
    if mutation in {"forged", "coverage"}:
        if mutation == "forged":
            ledger["validation"]["identifiers"][0]["sha256"] = "0" * 64
        else:
            ledger["validation"]["identifiers"] = []
    else:
        ledger["validation"] = None
        (workspace / "escape.py").symlink_to(workspace.parent / "outside.py")
        (workspace.parent / "outside.py").write_bytes(SOURCE)
        (workspace / "other.js").write_bytes(SOURCE)
        ledger["decisions"][0]["fixes"][0]["path"] = {
            "parent": "../outside.py", "absolute": str(workspace.parent / "outside.py"),
            "symlink": "escape.py", "unsupported": "other.js"}[mutation]
    path.write_bytes(encoded(ledger))
    result = validate_ledger(path, workspace, SESSION, root)
    validate(result, "ledger.schema.json")
    assert result["validation"]["status"] == "invalid"


@pytest.mark.parametrize("mutation", ["session", "requirements", "unknown-field", "open-id", "duplicate"])
def test_ledger_invalid_input_advisory(v3: tuple[Path, Path], mutation: str, capsys: pytest.CaptureFixture[str]) -> None:
    workspace, root = v3
    path = write_ledger(root)
    ledger = json.loads(path.read_bytes())
    if mutation == "session":
        ledger["session_id"] = "foreign"
    elif mutation == "requirements":
        ledger["requirements"]["sha256"] = "0" * 64
    elif mutation == "unknown-field":
        ledger["forged"] = True
    elif mutation == "duplicate":
        ledger["decisions"].append(deepcopy(ledger["decisions"][0]))
    else:
        ledger["open_items"] = [{"requirement_id": "R-99", "text": "unknown"}]
    path.write_bytes(encoded(ledger))
    original = path.read_bytes()
    assert main(["ledger-validate", "--ledger", str(path), "--workspace", str(workspace),
                 "--session-id", SESSION, "--artifacts", str(root)]) == 1
    assert "Ledger advisory:" in capsys.readouterr().out
    assert path.read_bytes() == original


def test_v3_cli_actual_module(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    command = [sys.executable, "-m", "verifier", "check", "--requirements", str(root / "requirements.json"),
               "--workspace", str(workspace), "--session-id", SESSION, "--artifacts", str(root), "--round", "1"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"overall": "pass", "failed_rows": [], "unverifiable_rows": [], "retry_warranted": False}
    assert len(result.stdout.splitlines()) == 1
    report(root)
    path = write_ledger(root)
    result = subprocess.run([sys.executable, "-m", "verifier", "ledger-validate", "--ledger", str(path),
                             "--workspace", str(workspace), "--session-id", SESSION, "--artifacts", str(root)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    validate(json.loads(path.read_bytes()), "ledger.schema.json")


@pytest.mark.parametrize("mutation", ["session", "prompt-hash", "source", "row-id", "call-ref", "call-identity", "extra-call"])
def test_provenance_errors_do_not_publish(v3: tuple[Path, Path], mutation: str) -> None:
    _, root = v3
    table = json.loads((root / "requirements.json").read_bytes())
    if mutation == "session":
        table["session_id"] = "wrong"
    elif mutation == "prompt-hash":
        table["prompt"]["sha256"] = "0" * 64
    elif mutation == "source":
        table["requirements"][0]["source_excerpt"] = "invented"
    elif mutation == "row-id":
        table["requirements"][0]["id"] = "R-99"
    elif mutation == "call-ref":
        table["luna_call"]["call_id"] = "absent"
    else:
        calls = [json.loads(l) for l in (root / "luna-calls.jsonl").read_text().splitlines()]
        if mutation == "call-identity":
            calls[0]["model"] = "different-model"
        else:
            calls.append(calls[0])
        (root / "luna-calls.jsonl").write_bytes(b"".join(encoded(c).replace(b"\n", b"") + b"\n" for c in calls))
    (root / "requirements.json").write_bytes(encoded(table))
    with pytest.raises(Exception):
        run(v3)
    assert not (root / "completion-report.json").exists()


def test_unsupported_llm_judge_is_never_dispatched(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    row = make_row("unavailable")
    row["check"] = {"type": "llm_judge"}
    assert evaluate_row(row, workspace, root, 1, 1)["status"] == "unverifiable"


def test_signature_body_changes_do_not_change_snapshot() -> None:
    assert signature_snapshot_bytes(SOURCE, ["health"]) == signature_snapshot_bytes(SOURCE.replace(b"return True", b"return False"), ["health"])
    assert not identifier_found(b"# health\ntext = 'health'\n", "name", "health")


def test_python_identities_are_extracted_without_execution(tmp_path: Path) -> None:
    target = tmp_path / "must-not-exist"
    source = f"open({str(target)!r}, 'w').write('bad')\nclass Service:\n    async def health(self, *, flag: bool=True) -> int:\n        return 1\nLIMIT: int = 4\n".encode()
    assert identifier_found(source, "signature", "async Service.health(self, *, flag: bool=True) -> int")
    assert identifier_found(source, "constant", "LIMIT = 4")
    assert not target.exists()


def test_argv_adapter_preserves_workspace_boundary_and_raw_bytes(
    v3: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, _ = v3
    cwd = workspace / "sub"
    cwd.mkdir()
    monkeypatch.setattr(sys, "platform", "darwin")
    is_file = Path.is_file
    monkeypatch.setattr(Path, "is_file", lambda path: str(path) == "/usr/bin/sandbox-exec" or is_file(path))
    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        from verifier.sandbox import seatbelt_profile
        assert argv[:3] == ["/usr/bin/sandbox-exec", "-p", seatbelt_profile(workspace)]
        assert argv[3:] == [sys.executable, "-m", "unittest", "discover"]
        assert kwargs["cwd"] == cwd and kwargs["timeout"] == 3
        assert "(deny network*)" in argv[2] and kwargs["env"]["HOME"] == str(workspace)
        return subprocess.CompletedProcess(argv, 0, b"\xff\r\n", b"\x00stderr")
    monkeypatch.setattr("verifier.sandbox.run_owned", runner)
    result = run_argv(["python", "-m", "unittest", "discover"], workspace, cwd, 3)
    assert result.stdout_bytes == b"\xff\r\n" and result.stderr_bytes == b"\x00stderr"


@pytest.mark.parametrize("argv", [["sh", "-c", "echo bad"], ["python", "-m", "pytest", "../outside"],
                                 ["python", "-m", "pytest", "/tmp/outside"], ["python", "-m", "pytest", ";"]])
def test_argv_adapter_rejects_before_launch(v3: tuple[Path, Path], argv: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    workspace, _ = v3
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("rejected argv must not launch")
    monkeypatch.setattr("verifier.sandbox.run_owned", forbidden)
    assert run_argv(argv, workspace, workspace, 1).error


def test_wrong_artifact_directory_and_symlink_are_rejected(v3: tuple[Path, Path]) -> None:
    workspace, root = v3
    with pytest.raises(ValueError):
        session_root(workspace, root, "other-session")
    alias = workspace / "alias"
    alias.symlink_to(root)
    with pytest.raises(ValueError, match="symlink"):
        session_root(workspace, alias, SESSION)


def test_check_internal_error_stdout_empty(v3: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    workspace, root = v3
    assert main(["check", "--requirements", str(root / "missing"), "--workspace", str(workspace),
                 "--session-id", SESSION, "--artifacts", str(root), "--round", "1"]) == 2
    assert capsys.readouterr().out == ""
