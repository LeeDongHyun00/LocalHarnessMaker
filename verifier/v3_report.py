"""Completion reports, citation verification and the durable one-repair limit."""

from __future__ import annotations

from copy import deepcopy
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Callable

from jsonschema import ValidationError

from verifier.processes import CLEANUP_SECONDS, shutdown_scope
from verifier.sandbox import run_argv
from verifier.schema import validate
from verifier.v3_checks import ArgvRunner, evaluate_row
from verifier.v3_io import (
    atomic, check_call, confined, encoded, locked, reference, requirements,
    session_root, snapshot, supplied_file,
)


def unavailable_audit(reason: str) -> dict[str, Any]:
    return {"status": "unavailable", "audited_final_message": None, "claims": [],
            "reason": reason, "luna_call": None}


def merge_audit(
    audit: dict[str, Any], report: dict[str, Any], root: Path,
) -> dict[str, Any]:
    audit = deepcopy(audit)
    probe = dict(report, claim_audit=audit)
    try:
        validate(probe, "completion-report.schema.json")
    except ValidationError:
        return unavailable_audit("claim audit has an invalid shape")
    ids = {item["requirement_id"] for item in report["items"]}
    audited = audit["audited_final_message"]
    try:
        if audit["luna_call"] is not None:
            check_call(root, report["session_id"], audit["luna_call"], "claim_audit")
        elif audit["status"] != "unavailable":
            raise ValueError("audit lacks accounting")
        original_bytes = reference(root, audited) if audited else None
        original = original_bytes.decode("utf-8") if original_bytes is not None else None
    except (ValueError, OSError, UnicodeError, ValidationError) as exc:
        return unavailable_audit(f"audit provenance unavailable: {exc}")
    if any(c["requirement_id"] not in ids for c in audit["claims"]):
        return unavailable_audit("audit cites unknown requirement ID")
    if original_bytes is not None:
        retained = snapshot(root, "audited-final-message", original_bytes, "claim")
        audit["audited_final_message"] = {key: retained[key] for key in ("path", "sha256")}
    for claim in audit["claims"]:
        supported = bool(claim["cited_evidence"]) and original is not None and claim["claim_excerpt"] in original
        verified = []
        for citation in claim["cited_evidence"]:
            try:
                data = reference(root, citation)
                excerpt = citation["excerpt"]
                if excerpt != "(empty)" or data:
                    supported &= excerpt in data.decode("utf-8", errors="replace")
                verified.append(citation)
            except (ValueError, OSError, RuntimeError):
                supported = False
        # The original audit snapshot retains rejected citations for review.
        # Structured report references contain only confined, hash-checked data.
        claim["cited_evidence"] = verified
        if not supported:
            claim["assessment"] = "unsupported"
    current = report["current_final_message"]
    if current is None:
        audit["status"] = "unavailable"
        audit["reason"] = "current final message is missing; original audit retained"
    elif audited and audited["sha256"] != current["sha256"]:
        audit["status"] = "stale"
        audit["reason"] = "current final message changed after the original audit; no new call"
    return audit


def summary(report: dict[str, Any], warranted: bool = False) -> dict[str, Any]:
    failed = [i["requirement_id"] for i in report["items"] if i["status"] == "fail"]
    unknown = [i["requirement_id"] for i in report["items"] if i["status"] == "unverifiable"]
    return {"overall": "pass" if report["items"] and not failed and not unknown else "fail",
            "failed_rows": failed, "unverifiable_rows": unknown, "retry_warranted": warranted}


def check_requirements(
    requirements_file: Path, workspace: Path, session_id: str, artifacts: Path,
    round_number: int, claim_audit: Path | None = None, final_message: Path | None = None,
    *, runner: ArgvRunner = run_argv, clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Publish a schema-valid report and return only the hook-facing summary.

    Hold the session lock through execution/publication. Repeated rounds refresh
    only final-message/audit freshness and never authorize a second repair.
    """
    root = session_root(workspace, artifacts, session_id)
    workspace = workspace.resolve()
    if supplied_file(root, requirements_file) != root / "requirements.json":
        raise ValueError("requirements must be the session requirements.json")
    if round_number not in {1, 2}:
        raise ValueError("round must be 1 or 2")
    budget = float(os.environ.get("HARNESS_VERIFY_BUDGET_SECONDS", "450"))
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError("verification budget must be finite and positive")
    started = clock()
    with locked(root):
        table, req_ref = requirements(root, session_id)
        path = confined(root, "completion-report.json")
        prior = json.loads(path.read_bytes()) if path.exists() else None
        if prior:
            validate(prior, "completion-report.schema.json")
            if prior["session_id"] != session_id or prior["requirements"] != req_ref:
                raise ValueError("prior report identity or requirements changed")
            row_ids = [row["id"] for row in table["requirements"]]
            if ([i["requirement_id"] for i in prior["items"]] != row_ids
                    or set(prior["retry"]["failed_requirement_ids"]) - set(row_ids)):
                raise ValueError("prior report row or retry coverage mismatch")
            if (prior["check_round"] == 1 and prior["retry"]["used"]
                    and prior["retry"]["failed_requirement_ids"] != summary(prior)["failed_rows"]):
                raise ValueError("repair reservation does not match executed failures")
            if round_number < prior["check_round"]:
                raise ValueError("cannot rewind a completed round")
        if round_number == 2 and (not prior or prior["retry"]["used"] != 1):
            raise ValueError("round 2 requires a persisted executed failure and repair reservation")
        current = None
        if final_message is not None:
            try:
                data = supplied_file(root, final_message).read_bytes()
            except FileNotFoundError:
                pass
            else:
                retained = snapshot(root, f"round-{round_number}-final", data, "claim")
                current = {key: retained[key] for key in ("path", "sha256")}
        repeated = bool(prior and prior["check_round"] == round_number)
        if repeated:
            report = deepcopy(prior)
            report["current_final_message"] = current
        else:
            items: list[dict[str, Any]] = []
            # Cleanup must finish successfully before a report reserves repair.
            with shutdown_scope():
                for row in table["requirements"]:
                    remaining = budget - (clock() - started) - CLEANUP_SECONDS
                    reason = None
                    if table["state"] != "ready":
                        reason = "requirements unavailable or user questions remain unanswered"
                    elif remaining <= 0:
                        reason = "verification budget exhausted before check; not executed"
                    if reason:
                        items.append({"requirement_id": row["id"], "status": "unverifiable",
                                      "reason": reason, "evidence": []})
                    else:
                        items.append(evaluate_row(row, workspace, root, round_number, min(120.0, remaining), runner))
            failed = [i["requirement_id"] for i in items if i["status"] == "fail"]
            retry = deepcopy(prior["retry"]) if prior else {
                "used": int(bool(failed)), "failed_requirement_ids": failed,
                "reason": "one repair reserved for executed deterministic failures" if failed else None,
            }
            advice = None
            if round_number == 2 and failed:
                advice = {"recommendation": "human_review", "text": "Executed checks still fail after one repair; no further automatic repair."}
            elif any(i["status"] == "unverifiable" for i in items) or not items:
                advice = {"recommendation": "human_review", "text": "Unavailable coverage cannot establish completion and does not permit repair."}
            report = {"schema_version": 3, "session_id": session_id, "requirements": req_ref,
                      "current_final_message": current, "check_round": round_number, "items": items,
                      "claim_audit": unavailable_audit("no claim audit supplied"),
                      "retry": retry, "escalation_advice": advice}
        audit = prior["claim_audit"] if prior else unavailable_audit("no claim audit supplied")
        if claim_audit is not None and not prior:
            audit_file = supplied_file(root, claim_audit)
            try:
                audit_bytes = audit_file.read_bytes()
            except FileNotFoundError:
                audit = unavailable_audit("supplied claim audit file is missing")
            else:
                snapshot(root, "original-claim-audit", audit_bytes, "claim")
                try:
                    audit = json.loads(audit_bytes)
                except (ValueError, UnicodeError):
                    audit = unavailable_audit("supplied claim audit is not valid UTF-8 JSON")
        report["claim_audit"] = merge_audit(audit, report, root)
        # Commands may write inside the workspace. Detect tampering before
        # publishing any evidence/provenance as successful checked bytes.
        reference(root, req_ref)
        for item in report["items"]:
            for evidence in item["evidence"]:
                reference(root, evidence)
        validate(report, "completion-report.schema.json")
        snapshot(root, f"completion-report-round-{round_number}", encoded(report), "check_output")
        atomic(path, encoded(report))
        warranted = not prior and round_number == 1 and report["retry"]["used"] == 1
        return summary(report, warranted)
