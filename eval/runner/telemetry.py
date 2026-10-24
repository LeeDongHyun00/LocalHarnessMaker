"""Keep requested settings separate from observed session evidence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _pricing_tier(values: list[Any], model: str | None,
                  requested: str | None) -> tuple[str, bool]:
    """Apply known CLI model defaults only when no tier was requested."""
    default = {'gpt-6.1-sol': 'standard', 'gpt-6-luna': 'priority'}.get(model or '')
    inferred = requested is None and default is not None and (not values or None in values)
    tiers = {('standard' if value == 'default' else value) if isinstance(value, str)
             else default if inferred and value is None else 'unknown' for value in values}
    if not values:
        tiers = {default if inferred else 'unknown'}
    return (next(iter(tiers)) if len(tiers) == 1 else 'unknown', inferred)


def _instant(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else None
    except (ValueError, AttributeError, TypeError):
        return None


def interrupted_pricing_evidence(segment: dict[str, Any], paths: list[Path]) -> dict[str, Any] | None:
    """Recover a missing exit capture only from timestamp-bounded applied records."""
    from hashlib import sha256

    start, end = _instant(segment.get('started_at')), _instant(segment.get('exited_at'))
    if start is None or end is None or end < start:
        return None
    observations = []
    for path in paths:
        for event in records(path):
            when, payload = _instant(event.get('timestamp')), event.get('payload')
            if (when is None or not start <= when <= end or event.get('type') != 'event_msg' or
                    not isinstance(payload, dict) or payload.get('type') != 'thread_settings_applied'):
                continue
            settings = payload.get('thread_settings')
            tier = settings.get('service_tier') if isinstance(settings, dict) else None
            observations.append({'native_log': str(path), 'observed_service_tier': tier,
                                 'record_sha256': sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()})
    tiers = {o['observed_service_tier'] for o in observations if isinstance(o['observed_service_tier'], str)}
    if not observations or len(tiers) != 1 or any(o['observed_service_tier'] != next(iter(tiers)) for o in observations):
        return None
    return {'tier': next(iter(tiers)), 'records': observations,
            'basis': 'Timestamp-bounded native applied records; historical exit capture absent'}


def recover_partial_usage(segments: list[dict[str, Any]], paths: list[Path]) -> None:
    """Retain interrupted cumulative counters as evidence, never billable usage.

    Bound observations by process timestamps so a later resume in the same
    rollout cannot supply counters for the interrupted process. Keep each
    rollout separate: cumulative session counters are not process deltas.
    """
    for segment in segments:
        if not (segment.get("interrupted") is True or segment.get("exit_code") == -2):
            continue
        start, end = _instant(segment.get("started_at")), _instant(segment.get("exited_at"))
        if start is None or end is None or end < start:
            continue
        observations = []
        for path in paths:
            last = None
            for event in records(path):
                payload = event.get("payload")
                when = _instant(event.get("timestamp"))
                if (event.get("type") != "event_msg" or not isinstance(payload, dict) or
                        payload.get("type") != "token_count" or when is None or not start <= when <= end):
                    continue
                info = payload.get("info")
                counts = info.get("total_token_usage") if isinstance(info, dict) else None
                if (isinstance(counts, dict) and counts and
                        all(type(v) is int and v >= 0 for v in counts.values())):
                    last = {"native_log": str(path), "timestamp": event["timestamp"],
                            "tokens": counts}
            if last:
                observations.append(last)
        if observations:
            segment["partial_usage"] = {
                "source": "native event_msg.token_count.info.total_token_usage",
                "lower_bound": True,
                "note": "Lower bound of cumulative session usage at interruption; may include earlier processes. Evidence only, never used for costs.",
                "rollouts": observations,
            }


def records(path: Path) -> list[dict[str, Any]]:
    """Read usable events without treating malformed records as success."""
    events: list[dict[str, Any]] = []
    if not path.is_file():
        return events
    for line in path.read_text(errors="replace").split("\n"):
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


def collect(event_paths: list[Path], native_paths: list[Path], model: str, effort: str, service_tier: str | None = None) -> dict[str, Any]:
    """Extract token counts, applied effort and account-wide plan snapshots."""
    events = [event for path in event_paths for event in records(path)]
    native = [event for path in native_paths for event in records(path)]
    contexts = [event["payload"] for event in native
                if event.get("type") == "turn_context" and isinstance(event.get("payload"), dict)]
    applied = [event["payload"].get("thread_settings", {}) for event in native
               if event.get("type") == "event_msg" and isinstance(event.get("payload"), dict)
               and event["payload"].get("type") == "thread_settings_applied"]
    observed = [{"model": p.get("model"), "effort": p.get("effort", p.get("reasoning_effort"))}
                if isinstance(p, dict) else {"model": None, "effort": None} for p in [*contexts, *applied]]
    settings_source = " + ".join((["native_session_jsonl.turn_context"] if contexts else []) +
                                 (["native_session_jsonl.event_msg.thread_settings_applied"] if applied else []))
    verified = bool(observed) and all(p == {"model": model, "effort": effort} for p in observed)
    tier_verified = service_tier is None or (bool(applied) and
        all(isinstance(p, dict) and p.get("service_tier") == service_tier for p in applied) and
        all(p["service_tier"] == service_tier for p in contexts if "service_tier" in p))
    if service_tier is not None:
        verified = verified and tier_verified
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
    values = [p.get("service_tier") if isinstance(p, dict) else None for p in applied]
    # A context's explicit tier is not applied-tier evidence and cannot justify
    # inferring an omitted tier when the applied record itself is unavailable.
    can_infer = bool(applied) or not any(p.get('service_tier') is not None for p in contexts)
    pricing_tier, inferred = _pricing_tier(values, model if can_infer else None, service_tier)
    return {
        "pricing_evidence": {"tier": pricing_tier,
                             "basis": ("Tier inferred from the model default; native applied service_tier omitted/null"
                                       if inferred else "native event_msg.thread_settings_applied.service_tier only")},
        "settings_evidence": {"verified": verified, "source": settings_source or "native_session_jsonl",
                              "observed": observed,
                              **({"requested_service_tier": service_tier, "service_tier_verified": tier_verified,
                                  "observed_service_tiers": [p.get("service_tier") if isinstance(p, dict) else None for p in applied]}
                                 if service_tier is not None else {}),
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
                       "tokens": segment.get("capacity_refusal_usage", segment.get("native_usage", evidence["tokens"])),
                       **({"partial_usage": segment["partial_usage"]} if "partial_usage" in segment else {}),
                       "plan_usage": {"source": "native_session_jsonl.event_msg.token_count.rate_limits.primary.used_percent",
                                      "before": before[-1] if before else None,
                                      "after": during[-1] if during else None,
                                      "first_observed_during_run": during[0] if during else None,
                                      "exact_task_consumption": None,
                                      "limitation": "Account-wide rounded observations; no pre-run observation means before=null. After is the last observation during the process, not a post-exit measurement."}})
    return result


def native_token_totals(paths: list[Path]) -> dict[str, tuple[int, dict[str, int]]]:
    """Read cumulative native counters once per session, without billing reasoning twice."""
    result: dict[str, tuple[int, dict[str, int]]] = {}
    for path in paths:
        counters = [e.get("payload", {}).get("info", {}).get("total_token_usage")
                    for e in records(path) if e.get("type") == "event_msg"
                    and e.get("payload", {}).get("type") == "token_count"
                    and isinstance(e.get("payload", {}).get("info"), dict)]
        if counters and isinstance(counters[-1], dict):
            counts = {k: counters[-1].get(k) for k in
                      ("input_tokens", "cached_input_tokens", "output_tokens")}
            if all(type(v) is int and v >= 0 for v in counts.values()):
                result[str(path)] = (len(counters), counts)
    return result


def native_token_delta(before: dict[str, tuple[int, dict[str, int]]],
                       after: dict[str, tuple[int, dict[str, int]]]) -> dict[str, int] | None:
    """Price only newly observed native counters; absent counters remain unknown."""
    deltas = []
    for name, (length, counts) in after.items():
        old_length, old = before.get(name, (0, dict.fromkeys(counts, 0)))
        if length <= old_length:
            continue
        delta = {k: v - old[k] for k, v in counts.items()}
        if any(v < 0 for v in delta.values()):
            return None
        deltas.append(delta)
    return {k: sum(d[k] for d in deltas) for k in deltas[0]} if deltas else None


def request_usage(events: list[dict[str, Any]], *, offset: int = 0,
                  segment: dict[str, Any] | None = None) -> list[dict[str, int]] | None:
    """Read native request counters, excluding repeated total/rate-limit updates.

    Scan earlier counters even when selecting a resumed process so an absent
    last_token_usage can use its actual preceding cumulative counter.
    """
    keys = ('input_tokens', 'cached_input_tokens', 'output_tokens')

    def counts(value: Any) -> dict[str, int] | None:
        if not isinstance(value, dict) or not all(type(value.get(k)) is int and value[k] >= 0 for k in keys):
            return None
        return {k: value[k] for k in keys}

    previous = dict.fromkeys(keys, 0)
    result = []
    index = 0
    start = _instant((segment or {}).get('started_at'))
    end = _instant((segment or {}).get('exited_at'))
    for event in events:
        payload = event.get('payload', {})
        if event.get('type') != 'event_msg' or not isinstance(payload, dict) or payload.get('type') != 'token_count':
            continue
        info = payload.get('info')
        if not isinstance(info, dict):
            continue
        index += 1
        current = counts(info.get('total_token_usage'))
        delta = {k: current[k] - previous[k] for k in keys} if current is not None else None
        if current == previous:
            continue
        if current is not None:
            previous = current
        when = _instant(event.get('timestamp'))
        if index <= offset or (start is not None and end is not None and when is not None
                               and not start <= when <= end):
            continue
        turn = counts(info.get('last_token_usage'))
        if info.get('last_token_usage') is not None and turn is None:
            return None
        if turn is None:
            turn = delta
        elif delta is not None and turn != delta:
            return None
        if (turn is None or any(v < 0 for v in turn.values()) or
                turn['cached_input_tokens'] > turn['input_tokens']):
            return None
        result.append(turn)
    return result or None


def native_request_usage(paths: list[Path], totals: dict[str, int], *,
                         before: dict[str, tuple[int, dict[str, int]]] | None = None,
                         segment: dict[str, Any] | None = None) -> list[dict[str, int]] | None:
    """Accept a process's request evidence only when it reproduces its usage.

    Historical streams may contain later resumes. Timestamp selection and an
    exact totals check prevent borrowing their requests to price an old call.
    """
    turns = []
    for path in dict.fromkeys(paths):
        selected = request_usage(records(path), offset=(before or {}).get(str(path), (0, {}))[0],
                                 segment=segment)
        if selected:
            turns.extend(selected)
    if turns and all(sum(t[k] for t in turns) == totals.get(k) for k in
                     ('input_tokens', 'cached_input_tokens', 'output_tokens')):
        return turns
    return None


def applied_tier_records(paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    """Read applied records separately so later resumes cannot reprice old calls."""
    return {str(path): [event for event in records(path) if event.get("type") == "event_msg"
            and isinstance(event.get("payload"), dict)
            and event["payload"].get("type") == "thread_settings_applied"] for path in paths}


def capture_tier(paths: list[Path], before: dict[str, list[dict[str, Any]]], *,
                 model: str | None = None, service_tier: str | None = None) -> dict[str, Any]:
    """Capture only newly emitted applied settings, including repeated records."""
    from collections import Counter
    from hashlib import sha256

    def fingerprint(event: dict[str, Any]) -> str:
        return sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()

    observations = []
    for path, events in applied_tier_records(paths).items():
        prior = Counter(fingerprint(event) for event in before.get(path, []))
        for event in events:
            identity = fingerprint(event)
            if prior[identity]:
                prior[identity] -= 1
                continue
            settings = event["payload"].get("thread_settings", {})
            value = settings.get("service_tier") if isinstance(settings, dict) else None
            observations.append({"native_log": path, "record_sha256": identity,
                                 "observed_service_tier": value})
    tier, inferred = _pricing_tier([o['observed_service_tier'] for o in observations], model, service_tier)
    return {"tier": tier,
            "basis": ("Tier inferred from the model default; new native applied service_tier omitted/null at process exit"
                      if inferred else "new native thread_settings_applied records captured at process exit"),
            "records": observations}
