"""Shared non-nested hook boundary. Never imported on the nested fast path."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time


def execute(event: str, started: float) -> int:
    """Publish output only after all processing succeeds; errors always fail open."""
    response = None
    payload = None
    error = None
    runtime = None
    try:
        from _runtime import Runtime
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != event:
            raise ValueError("hook event does not match entry point")
        runtime = Runtime(payload)
        response = runtime.dispatch(event)
        cli_seconds = runtime.cli_seconds
    except Exception as exc:
        cli_seconds = runtime.cli_seconds if runtime is not None else 0.0
        error = type(exc).__name__
        print(f"harness {event} warning: {type(exc).__name__}: {exc}", file=sys.stderr)
    elapsed = time.perf_counter() - started
    print(f"harness {event} elapsed_seconds={elapsed:.6f} cli_seconds={cli_seconds:.6f} "
          f"overhead_seconds={max(0.0, elapsed - cli_seconds):.6f}", file=sys.stderr)
    log_path = os.environ.get("HARNESS_EVENT_LOG")
    if log_path:
        try:
            with Path(log_path).open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"event": event, "input": payload, "output": response,
                                         "error": error, "elapsed_seconds": elapsed,
                                         "cli_seconds": cli_seconds}) + "\n")
        except Exception as exc:
            print(f"harness log warning: {type(exc).__name__}: {exc}", file=sys.stderr)
    if response is not None:
        print(json.dumps(response, ensure_ascii=False))
    return 0
