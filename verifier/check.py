"""Schema-validated verdict assembly without importing the controller."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import time
from typing import Any

from verifier.claims import claimed_criteria, last_report
from verifier.judge import judge_criterion
from verifier.reinstruct import reinstruct
from verifier.rules import evaluate
from verifier.sandbox import Runner, run_command
from verifier.schema import validate


def check_contract(
    contract: dict[str, Any], workspace: Path, transcript: Path, attempt: int,
    runner: Runner = run_command,
) -> dict[str, Any]:
    started = time.perf_counter()
    command_seconds = 0.0
    try:
        validate(contract, "contract.schema.json")
        if attempt < 1:
            raise ValueError("attempt must be at least 1")
        if not workspace.is_dir():
            raise ValueError("workspace must be an existing directory")
        report = last_report(transcript)
        limit = int(os.environ.get("HARNESS_MAX_ATTEMPTS", "3"))
        if limit < 1:
            raise ValueError("HARNESS_MAX_ATTEMPTS must be at least 1")
        backend = os.environ.get("HARNESS_BACKEND", "codex_cli")
        if backend not in {"codex_cli", "cheap_api", "local"}:
            raise ValueError("HARNESS_BACKEND must be codex_cli, cheap_api or local")
        criteria = contract["success_criteria"]
        ids = [criterion["id"] for criterion in criteria]
        if len(set(ids)) != len(ids):
            raise ValueError("success criterion IDs must be unique")
        claims = claimed_criteria(report, ids)
        quality_warning = not criteria or all(c["check"]["type"] == "llm_judge" for c in criteria)
        items = []
        if quality_warning:
            print("warning: contract has no mechanically verifiable success criteria", file=sys.stderr)
            # A diagnostic item is necessary because verdict.items has minItems=1.
            items = [
                {"id": c["id"], "status": "unverifiable",
                 "evidence": "contract quality warning: no mechanical success criteria",
                 "reason": "contract cannot be mechanically verified"}
                for c in criteria
            ] or [{"id": "contract-quality", "status": "unverifiable",
                   "evidence": "success_criteria is empty", "reason": "contract cannot be verified"}]
        else:
            for criterion in criteria:
                mechanical = criterion["check"]["type"] != "llm_judge"
                result = (evaluate(criterion["check"], workspace.resolve(), runner) if mechanical
                          else judge_criterion(criterion, workspace.resolve(), backend))
                command_seconds += result.command_duration
                reason = result.reason
                if mechanical and result.status == "fail" and criterion["id"] in claims:
                    reason = "claimed_without_evidence"
                items.append({"id": criterion["id"], "status": result.status,
                              "evidence": result.evidence, "reason": reason})
        verdict = {
            "items": items,
            "overall": "pass" if all(item["status"] == "pass" for item in items) else "fail",
            "reinstruct_message": reinstruct(criteria, items, attempt, limit),
            "attempt": attempt,
        }
        validate(verdict, "verdict.schema.json")
        return verdict
    finally:
        elapsed = time.perf_counter() - started
        print(f"verifier elapsed_seconds={elapsed:.6f} command_seconds={command_seconds:.6f} "
              f"overhead_seconds={max(0.0, elapsed - command_seconds):.6f}", file=sys.stderr)
