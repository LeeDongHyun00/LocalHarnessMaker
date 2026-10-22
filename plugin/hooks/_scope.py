"""Read-only project opt-in gate, evaluated before state, timing or runtime imports."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from typing import Any

MARKER = '.local-harness-maker'


def marked_project(payload: dict[str, Any]) -> bool:
    """Use canonical ancestors so siblings and symlink escapes do not inherit opt-in."""
    cwd = payload.get('cwd')
    if not isinstance(cwd, str):
        raise ValueError('hook cwd must be a string')
    directory = Path(cwd).resolve(strict=True)
    return any((parent / MARKER).is_file() for parent in (directory, *directory.parents))


def read_scoped_payload() -> dict[str, Any] | None:
    """Read only enough input to gate all subsequent hook work."""
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("hook input must be an object")
    return payload if marked_project(payload) else None
