"""Recognize resumable infrastructure limits from retained Codex error events."""

import json
from pathlib import Path
import re
from typing import Any


class UsageLimitError(RuntimeError):
    """A model call reached an account usage limit; preserve the provider message."""


def usage_limit_message(paths: list[Path]) -> str | None:
    """Inspect JSON errors, including controller stderr's control_cli_events envelope.

    Assistant/tool prose and arbitrary stderr text are not limit evidence.
    """
    pattern = re.compile(r"\b(?:you(?:'ve|’ve| have) hit your usage limit|usage limit (?:has been )?(?:reached|exceeded))\b", re.I)

    def message(event: Any) -> str | None:
        if not isinstance(event, dict) or event.get("type") not in {"error", "turn.failed"}:
            return None
        error = event.get("error")
        candidates = [event.get("message"), error.get("message") if isinstance(error, dict) else None]
        return next((text for text in candidates if isinstance(text, str) and pattern.search(text)), None)

    def scan(text: str, *, envelopes: bool = False) -> str | None:
        for line in text.splitlines():
            envelope = envelopes and "control_cli_events " in line
            raw = line.split("control_cli_events ", 1)[1] if envelope else line
            try:
                event = json.loads(raw)
            except ValueError:
                continue
            found = message(event)
            if found:
                return found
            if envelope and isinstance(event, dict) and isinstance(event.get("events"), str):
                found = scan(event["events"])
                if found:
                    return found
        return None

    for path in paths:
        if path.is_file():
            found = scan(path.read_text(errors="replace"), envelopes=True)
            if found:
                return found
    return None
