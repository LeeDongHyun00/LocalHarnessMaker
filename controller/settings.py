"""Load the JSON-compatible YAML configuration without extra dependencies."""

import json
from pathlib import Path
from typing import Any

from controller.errors import InputError

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = PACKAGE_DIR.parent / "schemas"


def load_object(path: Path) -> dict[str, Any]:
    """Read a JSON object; configuration files use the JSON subset of YAML."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"Cannot read JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise InputError(f"Expected a JSON object: {path}")
    return value


def pricing_snapshot() -> tuple[Path, bytes, dict[str, Any]]:
    """Read the package snapshot once, independent of the caller's directory."""
    path = PACKAGE_DIR / "prices.yaml"
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise InputError(f"pricing snapshot not found at path {path}") from exc
    except OSError as exc:
        raise InputError(f"pricing snapshot unreadable at path {path}: {exc}") from exc
    try:
        book = json.loads(data)
        if not isinstance(book, dict):
            raise ValueError("expected a JSON object")
    except ValueError as exc:
        raise InputError(f"invalid pricing snapshot at path {path}: {exc}") from exc
    return path, data, book
