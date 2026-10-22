"""Capture real hook payloads and exercise documented context/continuation output.

Experiment only; this does not implement controller or verifier behavior.
"""

import os

if os.environ.get("HARNESS_NESTED") == "1":
    raise SystemExit(0)

import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import time
from typing import Any
from uuid import uuid4


def probe(payload: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Record one invocation and return a bounded experiment response."""
    output_dir.mkdir(parents=True, exist_ok=True)
    event = payload["hook_event_name"]
    if event not in {"SessionStart", "UserPromptSubmit", "Stop"}:
        raise ValueError("unexpected hook event")
    response: dict[str, Any] = {}
    if event in {"SessionStart", "UserPromptSubmit"}:
        marker = {
            "SessionStart": "HARNESS_SESSION_CONTEXT_4D91",
            "UserPromptSubmit": "HARNESS_CONTRACT_CONTEXT_8B62",
        }[event]
        response = {"hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": f"When first replying, include this exact marker: {marker}",
        }}
    else:
        # An exclusive file also bounds continuation if stop_hook_active is absent.
        flag = output_dir / "stop-requested"
        if not payload.get("stop_hook_active", False):
            try:
                with flag.open("x", encoding="utf-8") as stream:
                    stream.write("requested once\n")
            except FileExistsError:
                pass
            else:
                response = {"decision": "block", "reason": "test: print one more line"}
    record = {"input": payload, "output": response}
    path = output_dir / f"{time.time_ns()}-{event}-{uuid4().hex}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return response


def main() -> int:
    """Fail open on all ordinary hook errors and log elapsed time to stderr."""
    if os.environ.get("HARNESS_NESTED") == "1":
        return 0
    started = None
    try:
        from _scope import read_scoped_payload
        payload = read_scoped_payload()
        if payload is None:
            return 0
        started = time.perf_counter()
        response = probe(payload, Path(os.environ["HARNESS_PROBE_DIR"]))
        print(json.dumps(response))
    except Exception as exc:
        print(f"harness probe warning: {type(exc).__name__}: {exc}", file=sys.stderr)
    elapsed = time.perf_counter() - started if started is not None else 0.0
    print(f"harness probe elapsed_seconds={elapsed:.6f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
