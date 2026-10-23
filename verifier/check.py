"""Schema-validated verdict assembly without importing the controller."""

from __future__ import annotations

import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

from verifier.causes import Cause
from verifier.claims import claim_observations, extract_claims, last_report
from verifier.judge import judge_criterion, judge_timeout
from verifier.processes import CLEANUP_SECONDS
from verifier.reinstruct import reinstruct
from verifier.rules import evaluate
from verifier.sandbox import Runner, run_command
from verifier.schema import validate


def check_contract(
    contract: dict[str, Any], workspace: Path, transcript: Path, attempt: int,
    runner: Runner = run_command, *, clock: Callable[[], float] = time.monotonic,
    observations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = clock()
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
        timeout = judge_timeout()
        try:
            budget = float(os.environ.get("HARNESS_VERIFY_BUDGET_SECONDS", "450"))
        except ValueError as exc:
            raise ValueError("HARNESS_VERIFY_BUDGET_SECONDS must be finite and positive") from exc
        if not math.isfinite(budget) or budget <= 0:
            raise ValueError("HARNESS_VERIFY_BUDGET_SECONDS must be finite and positive")
        deadline = started + budget
        criteria = contract["success_criteria"]
        ids = [criterion["id"] for criterion in criteria]
        if len(set(ids)) != len(ids):
            raise ValueError("success criterion IDs must be unique")
        claims = extract_claims(report, ids, {c["id"]: c["description"] for c in criteria})
        quality_warning = not criteria or all(c["check"]["type"] == "llm_judge" for c in criteria)
        items = []
        causes: dict[str, Cause] = {}
        if quality_warning:
            print("warning: contract has no mechanically verifiable success criteria", file=sys.stderr)
            # A diagnostic item is necessary because verdict.items has minItems=1.
            items = [
                {"id": c["id"], "status": "unverifiable",
                 "evidence": "contract quality warning: no mechanical success criteria",
                 "reason": "contract quality warning: no mechanical success criteria"}
                for c in criteria
            ] or [{"id": "contract-quality", "status": "unverifiable",
                   "evidence": "success_criteria is empty", "reason": "contract quality warning: success_criteria is empty"}]
            causes.update({item["id"]: Cause.CONTRACT for item in items})
        else:
            for criterion in criteria:
                remaining = deadline - clock() - CLEANUP_SECONDS
                if remaining <= 0:
                    causes[criterion["id"]] = Cause.BUDGET
                    items.append({
                        "id": criterion["id"], "status": "unverifiable",
                        "evidence": "criterion not started: HARNESS_VERIFY_BUDGET_SECONDS exhausted",
                        "reason": f"verification budget ({budget:g} seconds) exhausted; cleanup reserve retained",
                    })
                    continue
                mechanical = criterion["check"]["type"] != "llm_judge"
                if mechanical:
                    result = evaluate(criterion["check"], workspace.resolve(), runner, min(120.0, remaining))
                else:
                    result = judge_criterion(
                        criterion, workspace.resolve(), backend, timeout=min(timeout, remaining),
                    )
                causes[criterion["id"]] = result.cause
                command_seconds += result.command_duration
                reason = result.reason
                if mechanical and result.status == "fail" and criterion["id"] in claims:
                    reason = "claimed_without_evidence"
                items.append({"id": criterion["id"], "status": result.status,
                              "evidence": result.evidence, "reason": reason})
        verdict = {
            "items": items,
            "overall": "pass" if all(item["status"] == "pass" for item in items) else "fail",
            "reinstruct_message": reinstruct(criteria, items, attempt, limit, causes=causes),
            "attempt": attempt,
        }
        validate(verdict, "verdict.schema.json")
        if observations is not None:
            observations.update(claim_observations(criteria, claims, verdict))
        return verdict
    finally:
        elapsed = clock() - started
        print(f"verifier elapsed_seconds={elapsed:.6f} command_seconds={command_seconds:.6f} "
              f"overhead_seconds={max(0.0, elapsed - command_seconds):.6f}", file=sys.stderr)
