"""Keep requested settings separate from observed session evidence."""

import json
from pathlib import Path
from typing import Any


def records(path: Path) -> list[dict[str, Any]]:
    """Read usable events without treating malformed records as success."""
    events: list[dict[str, Any]] = []
    for line in path.read_text(errors="replace").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def session_id(paths: list[Path]) -> str | None:
    """Find the explicit executor session identifier."""
    for path in paths:
        for event in records(path):
            if event.get("type") == "thread.started":
                return event.get("thread_id")
    return None


def collect(event_paths: list[Path], native_paths: list[Path], model: str, effort: str) -> dict[str, Any]:
    """Extract token counts, applied effort and account-wide plan snapshots."""
    events = [event for path in event_paths for event in records(path)]
    native = [event for path in native_paths for event in records(path)]
    contexts = [event["payload"] for event in native if event.get("type") == "turn_context"]
    observed = [{"model": p.get("model"), "effort": p.get("effort", p.get("reasoning_effort"))} for p in contexts]
    verified = bool(observed) and all(p == {"model": model, "effort": effort} for p in observed)
    totals: dict[str, int] = {}
    for event in events:
        if event.get("type") == "turn.completed":
            for key, value in event.get("usage", {}).items():
                if isinstance(value, int) and not isinstance(value, bool):
                    totals[key] = totals.get(key, 0) + value
    snapshots = [
        {"timestamp": event.get("timestamp"), "rate_limits": event["payload"]["rate_limits"]}
        for event in native
        if event.get("type") == "event_msg" and event.get("payload", {}).get("type") == "token_count"
        and event["payload"].get("rate_limits") is not None
    ]
    return {
        "settings_evidence": {"verified": verified, "source": "native_session_jsonl.turn_context",
                              "observed": observed,
                              "exec_json_exposes_effort": any("reasoning_effort" in event or "effort" in event for event in events)},
        "usage": {"billing_basis": "chatgpt_subscription", "tokens": totals or None, "billed_usd": None,
                  "plan_usage": {"availability": "account_snapshots" if snapshots else "unavailable",
                                 "snapshots": snapshots, "exact_task_consumption": None,
                                 "limitation": "Account-wide, rounded snapshots; first observation may follow usage. Concurrent sessions prevent exact task attribution."}},
    }
