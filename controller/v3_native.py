"""Read only the fresh control thread's native metadata from its Codex home."""

import json
import re
from pathlib import Path
from typing import Any


def records(events: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in events.splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("native event is not an object")
        result.append(value)
    return result


def native_models(events: str) -> list[str]:
    """Read explicit metadata fields, never assistant text or requested flags."""
    models: list[str] = []
    for event in records(events):
        kind = event.get("type")
        containers = [event] if kind in {"thread.started", "session.started", "turn.started"} else []
        payload = event.get("payload")
        if kind in {"session_meta", "turn_context"} and isinstance(payload, dict):
            containers.append(payload)
        if kind == "event_msg" and isinstance(payload, dict):
            if payload.get("type") == "thread_settings_applied":
                settings = payload.get("thread_settings")
                if isinstance(settings, dict):
                    containers.append(settings)
            elif payload.get("type") == "token_count":
                containers.append(payload)
                if isinstance(payload.get("info"), dict):
                    containers.append(payload["info"])
        for container in containers:
            if "model" in container:
                model = container["model"]
                if not isinstance(model, str) or not model:
                    raise ValueError("native model identity is invalid")
                models.append(model)
    return models


def rollout(events: str, codex_home: Path) -> str:
    """Select by thread.started ID, then verify the native session identity.

    Filename filtering avoids opening unrelated sessions. Metadata matching
    rejects mislabeled files and child threads before model/usage extraction.
    """
    ids = {e.get("thread_id") for e in records(events) if e.get("type") == "thread.started"}
    if len(ids) != 1:
        return ""
    thread_id = ids.pop()
    if not isinstance(thread_id, str) or not re.fullmatch(r"[a-zA-Z0-9-]{1,128}", thread_id):
        return ""
    sessions = codex_home / "sessions"
    selected: list[str] = []
    for path in sorted(sessions.rglob(f"rollout-*-{thread_id}.jsonl")):
        if path.is_symlink() or not path.resolve().is_relative_to(sessions.resolve()):
            continue
        text = path.read_text(encoding="utf-8")
        entries = records(text)
        session_ids = {e["payload"].get("id") for e in entries
                       if e.get("type") == "session_meta" and isinstance(e.get("payload"), dict)}
        if session_ids != {thread_id}:
            continue
        for event in entries:
            payload = event.get("payload")
            if event.get("type") == "event_msg" and isinstance(payload, dict):
                if payload.get("thread_id", thread_id) != thread_id:
                    continue
                if payload.get("type") in {"thread_settings_applied", "token_count"}:
                    selected.append(json.dumps(event, ensure_ascii=False))
    return "\n".join(selected)


def usage_event(events: str) -> str:
    """Map the final cumulative total of this new exec thread, never sum snapshots."""
    counts: dict[str, Any] | None = None
    for event in records(events):
        payload = event.get("payload")
        if (event.get("type") == "event_msg" and isinstance(payload, dict)
                and payload.get("type") == "token_count"):
            info = payload.get("info")
            counts = info.get("total_token_usage") if isinstance(info, dict) else None
    return json.dumps({"type": "turn.completed", "usage": counts}) if counts is not None else ""
