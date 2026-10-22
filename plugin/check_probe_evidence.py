"""Audit saved compatibility evidence offline without another model call."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from plugin.versions import validate_version


def audit(root: Path, expected_version: str | None = None) -> dict[str, Any]:
    """Require captured inputs, context delivery, bounded Stop, and final reply."""
    metadata = json.loads((root / "experiment.json").read_text())
    version = validate_version(metadata["version"])
    if expected_version is not None:
        assert version == validate_version(expected_version), (version, expected_version)
    records = [json.loads(p.read_text()) for p in sorted((root / "hooks").glob("*.json"))]
    events = [r["input"]["hook_event_name"] for r in records]
    assert events == ["SessionStart", "UserPromptSubmit", "Stop", "Stop"], events
    assert len({r["input"]["session_id"] for r in records}) == 1
    assert records[2]["input"]["stop_hook_active"] is False
    assert records[2]["output"] == {"decision": "block", "reason": "test: print one more line"}
    assert records[3]["input"]["stop_hook_active"] is True
    assert records[3]["input"]["last_assistant_message"] == "SECOND_REPLY"
    assert records[3]["output"] == {}
    rows = [json.loads(line) for line in (root / "transcript-excerpt.jsonl").read_text().splitlines()]
    messages: list[tuple[str, str]] = []
    for row in rows:
        if row["type"] == "response_item" and row["payload"].get("type") == "message":
            payload = row["payload"]
            text = "\n".join(c.get("text", "") for c in payload["content"])
            messages.append((payload["role"], text))
    for marker in ("HARNESS_SESSION_CONTEXT_4D91", "HARNESS_CONTRACT_CONTEXT_8B62"):
        assert any(role == "developer" and marker in text for role, text in messages)
        assert any(role == "assistant" and marker in text for role, text in messages)
    assert any(role == "user" and "<hook_prompt " in text and "test: print one more line" in text
               for role, text in messages)
    assistant = [text for role, text in messages if role == "assistant"]
    assert len(assistant) == 2
    assert "FIRST_REPLY" in assistant[0]
    assert assistant[1] == "SECOND_REPLY"
    result = json.loads((root / "result.json").read_text())
    assert result["exit_code"] == 0
    return {"directory": str(root), "version": version, "events": events, "assistant_messages": len(assistant),
            "context_visible": True, "continued_once": True, "exit_code": 0}


def main() -> int:
    """Check one or more previously captured runs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--expected-version", help="exact codex-cli identity to verify")
    args = parser.parse_args()
    for root in args.directories:
        print(json.dumps(audit(root, args.expected_version), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
