"""Schema-validated verdict assembly without importing the controller."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any

from jsonschema import Draft202012Validator

from verifier.rules import evaluate
from verifier.sandbox import Runner, run_command


SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def validate(value: Any, schema_name: str) -> None:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(value)


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
        # JSONL is the role's provisional assumption, not a claim parser contract.
        for number, line in enumerate(transcript.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip() and not isinstance(json.loads(line), dict):
                raise ValueError(f"transcript line {number} must be a JSON object")
        criteria = contract["success_criteria"]
        ids = [criterion["id"] for criterion in criteria]
        if len(set(ids)) != len(ids):
            raise ValueError("success criterion IDs must be unique")
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
                result = evaluate(criterion["check"], workspace.resolve(), runner)
                command_seconds += result.command_duration
                items.append({"id": criterion["id"], "status": result.status,
                              "evidence": result.evidence, "reason": result.reason})
        verdict = {
            "items": items,
            "overall": "pass" if all(item["status"] == "pass" for item in items) else "fail",
            # Bounded re-instruction is a D-2 deliverable, not inferred here.
            "reinstruct_message": None,
            "attempt": attempt,
        }
        validate(verdict, "verdict.schema.json")
        return verdict
    finally:
        elapsed = time.perf_counter() - started
        print(f"verifier elapsed_seconds={elapsed:.6f} command_seconds={command_seconds:.6f} "
              f"overhead_seconds={max(0.0, elapsed - command_seconds):.6f}", file=sys.stderr)
