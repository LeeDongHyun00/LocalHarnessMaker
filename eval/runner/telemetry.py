"""Keep requested settings separate from observed session evidence."""

import json
from pathlib import Path
from typing import Any


def records(path: Path) -> list[dict[str, Any]]:
    """Read usable events without treating malformed records as success."""
    events: list[dict[str, Any]] = []
    if not path.is_file():
        return events
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
    tiers = {p.get("service_tier", "standard") for p in contexts}
    pricing_tier = next(iter(tiers)) if len(tiers) == 1 else "unknown" if tiers else "standard"
    return {
        "pricing_evidence": {"tier": pricing_tier,
                             "basis": "native turn_context when present; otherwise Standard baseline assumption"},
        "settings_evidence": {"verified": verified, "source": "native_session_jsonl.turn_context",
                              "observed": observed,
                              "exec_json_exposes_effort": any("reasoning_effort" in event or "effort" in event for event in events)},
        "usage": {"billing_basis": "chatgpt_subscription", "tokens": totals or None, "billed_usd": None,
                  "plan_usage": {"availability": "account_snapshots" if snapshots else "unavailable",
                                 "snapshots": snapshots, "exact_task_consumption": None,
                                 "limitation": "Account-wide, rounded snapshots; first observation may follow usage. Concurrent sessions prevent exact task attribution."}},
    }


def collect_runs(event_paths: list[Path], native_paths: list[Path],
                 segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep per-process tokens and timestamp-bounded native plan observations.

    A snapshot inside a run is not a pre-run baseline. If the native session
    has no earlier observation, before remains null instead of inventing one.
    """
    from datetime import datetime

    def timestamp(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else None
        except ValueError:
            return None

    snapshots = []
    for path in native_paths:
        for event in records(path):
            payload = event.get("payload", {})
            if event.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            limits = payload.get("rate_limits")
            primary = limits.get("primary") if isinstance(limits, dict) else None
            used = primary.get("used_percent") if isinstance(primary, dict) else None
            instant = timestamp(event.get("timestamp"))
            if instant is not None and type(used) in {int, float}:
                snapshots.append((instant, {"timestamp": event["timestamp"], "primary_used_percent": used,
                                            "rate_limits": limits}))
    snapshots.sort(key=lambda item: item[0])
    result = []
    for path, segment in zip(event_paths, segments):
        start, end = timestamp(segment.get("started_at")), timestamp(segment.get("exited_at"))
        before = [s for t, s in snapshots if start is not None and t <= start]
        during = [s for t, s in snapshots if start is not None and end is not None and start < t <= end]
        evidence = collect([path], [], "", "")["usage"]
        result.append({"attempt": segment["attempt"], "events": path.name,
                       "started_at": segment.get("started_at"), "exited_at": segment.get("exited_at"),
                       "tokens": evidence["tokens"],
                       "plan_usage": {"source": "native_session_jsonl.event_msg.token_count.rate_limits.primary.used_percent",
                                      "before": before[-1] if before else None,
                                      "after": during[-1] if during else None,
                                      "first_observed_during_run": during[0] if during else None,
                                      "exact_task_consumption": None,
                                      "limitation": "Account-wide rounded observations; no pre-run observation means before=null. After is the last observation during the process, not a post-exit measurement."}})
    return result
