"""Offline validation against the shared schema bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


def validate(value: Any, schema_name: str) -> None:
    registry: Registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        resource = Resource.from_contents(json.loads(path.read_text(encoding="utf-8")))
        registry = registry.with_resource(path.name, resource)
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(value)
