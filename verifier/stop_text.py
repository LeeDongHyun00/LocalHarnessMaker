"""Exact Stop continuation texts for Role 2; no model calls or application edits."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from verifier.schema import validate
from verifier.v3_io import confined, locked, reference


REPAIR_INSTRUCTION = """One application repair is authorized for the executed deterministic failures below only.
Use the retained concrete evidence to repair only these failing requirement rows. Make no other changes.
Unverifiable rows and claim-audit opinions do not authorize changes. Re-run the failing checks and preserve their results in your application completion summary. This is the only repair; another failure permits advice, not another repair.
Failure evidence:
{failures}"""

LEDGER_REQUEST = """Application checks have settled. This is one bookkeeping continuation, not application repair.
Write {ledger_path} as UTF-8 JSON matching the version 3 ledger schema. The complete top-level shape is: schema_version 3, session_id {session_id}, requirements {requirements}, decisions array, open_items array, validation null. Use only these fields; the hook owns validation.
Each decision has exactly id (unique nonempty string), what (nonempty string), rationale (nonempty string), fixes (array). Each fix has exactly kind (one of "name", "signature", "constant"), value (nonempty string), path (workspace-relative Python file). Each open item has exactly requirement_id (existing R-n ID or null), text (nonempty string). Empty arrays are allowed when there are no actual decisions/fixes/open items. Signature values use canonical Python spelling, such as health(x: int=1) -> bool; constants may use NAME = literal to pin the value. Never populate validation yourself.
Record the decisions and reasons, exact fixed Python names, signatures and literal constants with their paths, and unresolved items. Do not change application code or repair failed/unverifiable rows. Do not invent decisions or identifiers. No additional ledger repair continuation will be issued.
Preserve the application completion summary, claims, limitations and verification evidence in your final response. A ledger-save notice alone must not replace that summary."""


def repair_instruction(report: dict[str, Any], artifacts: Path) -> str | None:
    """Render only reserved round-one failures, with hash-verified evidence."""
    validate(report, "completion-report.schema.json")
    if report["check_round"] != 1 or report["retry"]["used"] != 1:
        return None
    ids = set(report["retry"]["failed_requirement_ids"])
    failures = []
    for item in report["items"]:
        if item["requirement_id"] not in ids or item["status"] != "fail":
            continue
        for evidence in item["evidence"]:
            reference(artifacts, evidence)
        failures.append({"requirement_id": item["requirement_id"], "reason": item["reason"],
                         "evidence": item["evidence"]})
    return REPAIR_INSTRUCTION.format(failures=json.dumps(failures, ensure_ascii=False, indent=2)) if failures else None


def reserve_ledger_request(artifacts: Path) -> str | None:
    """Persist at-most-once request before returning a Stop bookkeeping text.

    Role 2 invokes this only after consuming the check summary. Round one with
    failures must reach round two first. Repeated Stop events return None.
    """
    with locked(artifacts):
        report = json.loads(confined(artifacts, "completion-report.json").read_bytes())
        validate(report, "completion-report.schema.json")
        if report["check_round"] == 1 and report["retry"]["used"]:
            raise ValueError("application repair has not settled")
        reference(artifacts, report["requirements"])
        text = LEDGER_REQUEST.format(
            ledger_path=str(artifacts / "ledger.json"),
            session_id=json.dumps(report["session_id"]),
            requirements=json.dumps(report["requirements"]),
        )
        marker = confined(artifacts, "evidence/ledger-request.txt")
        marker.parent.mkdir(exist_ok=True)
        try:
            with marker.open("xb") as stream:
                stream.write(text.encode())
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            return None
        return text
