"""Audit the saved D-2 fixture loop without running Codex or reading temp state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXAMPLES = Path(__file__).resolve().parents[1] / "schemas/examples"


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root: Path) -> dict[str, Any]:
    """Check captured boundary messages against saved state and unchanged fixtures."""
    metadata = read(root / "experiment.json")
    real = metadata.get("mode") == "real"
    if real:
        initial = read(root / "initial-workspace.json")
        requested = read(root / "request-workspace.json")
        before_approval = read(root / "before-approval-workspace.json")
        if initial != {"files": {}} or requested != initial or before_approval != initial:
            raise ValueError("task files changed before approval")
    events = [json.loads(line) for line in (root / "hooks.jsonl").read_text().splitlines()]
    if not events or any(event["error"] is not None for event in events):
        raise ValueError("missing or failed hooks")
    request_result, approval_result = read(root / "request-result.json"), read(root / "approval-result.json")
    if request_result["exit_code"] != 0 or approval_result["exit_code"] != 0:
        raise ValueError("an executor stage did not exit successfully")
    if request_result["command"].count("exec") != 1 or "resume" in request_result["command"]:
        raise ValueError("request must launch one initial codex exec")
    if "resume" not in approval_result["command"]:
        raise ValueError("approval must resume the displayed contract")
    pending = read(root / "request-state/session.json")
    completed = read(root / "approval-state/session.json")
    if pending["phase"] != "awaiting_approval" or read(root / "request-state/state.json")["attempt"] != 0:
        raise ValueError("request did not wait for approval")
    if (root / "request-state/verdict.json").exists():
        raise ValueError("verification ran before approval")
    attempt = read(root / "approval-state/state.json")["attempt"]
    if completed["phase"] != "complete" or (not real and attempt != 2):
        raise ValueError("loop did not complete in two verification attempts")
    if completed["session_id"] != pending["session_id"]:
        raise ValueError("approval changed sessions")
    if (root / "request-state/contract.json").read_bytes() != (root / "approval-state/contract.json").read_bytes():
        raise ValueError("approved contract changed")
    if real:
        from plugin.hooks._runtime import validate
        if (root / "result.txt").read_bytes() != b"ok\n":
            raise ValueError("real artifact contents mismatch")
        contract = validate(root / "approval-state/contract.json", "contract.schema.json")
        verdict = validate(root / "approval-state/verdict.json", "verdict.schema.json")
        validate(root / "approval-state/handoff.json", "handoff.schema.json")
        if (verdict["overall"] != "pass" or verdict["attempt"] != attempt
                or not 1 <= attempt <= metadata.get("max_attempts", 3)
                or any(item["status"] != "pass" for item in verdict["items"])):
            raise ValueError("real verdict did not pass at recorded attempt")
        if {item["id"] for item in verdict["items"]} != {item["id"] for item in contract["success_criteria"]}:
            raise ValueError("real verdict criteria mismatch")
    for stage in (() if real else ("request", "approval")):
        if (root / f"{stage}-state/contract.json").read_bytes() != (EXAMPLES / "contract.json").read_bytes():
            raise ValueError("stub contract was mutated")
    if not real and (root / "approval-state/verdict.json").read_bytes() != (EXAMPLES / "verdict_pass.json").read_bytes():
        raise ValueError("stub pass verdict was mutated")
    submitted = [event for event in events if event["event"] == "UserPromptSubmit"]
    if len(submitted) != 2 or submitted[1]["input"]["prompt"] != "approve":
        raise ValueError("expected request followed by explicit demo approval")
    context = submitted[0]["output"]["hookSpecificOutput"]["additionalContext"]
    if (root / "request-state/contract.json").read_text() not in context:
        raise ValueError("missing full contract injection")
    blocks = [event for event in events if event["event"] == "Stop" and event["output"]
              and event["output"].get("decision") == "block"]
    if (not real and (len(blocks) != 1 or blocks[0]["output"]["reason"] != read(EXAMPLES / "verdict_fail.json")["reinstruct_message"])) or (real and len(blocks) != attempt - 1):
        raise ValueError("expected exactly the fixture re-instruction once")
    transcript = [json.loads(line) for line in (root / "approval-transcript.jsonl").read_text().splitlines()]
    texts = [(row["payload"].get("role"), "\n".join(part.get("text", "") for part in row["payload"].get("content", [])))
             for row in transcript if row["type"] == "response_item"]
    if not any(role == "developer" and text == context for role, text in texts):
        raise ValueError("contract absent from model context")
    for block in blocks:
        if not any(role == "user" and "<hook_prompt " in text and block["output"]["reason"] in text for role, text in texts):
            raise ValueError("re-instruction absent from model context")
    overhead = max(event["elapsed_seconds"] - event["cli_seconds"] for event in events)
    return {"contract_visible": True, "approval_gate": True, "reinstructions": len(blocks),
            "attempts": attempt, "overall": "pass", "synthetic": not real, "real_task_verified": real,
            "max_hook_overhead_seconds": round(overhead, 6)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
