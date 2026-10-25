"""Validate shared schemas and every reference sample without executing checks."""

from __future__ import annotations

import json
from datetime import datetime
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
EXAMPLE_SCHEMAS = {
    "contract.json": "contract.schema.json",
    "verdict_pass.json": "verdict.schema.json",
    "verdict_fail.json": "verdict.schema.json",
    "handoff.json": "handoff.schema.json",
    "criterion.json": "judgment-input.schema.json",
    "judgment.json": "judgment.schema.json",
    "evaluation_report.json": "evaluation-report.schema.json",
    "requirements.json": "requirements.schema.json",
    "completion-report.json": "completion-report.schema.json",
    "ledger.json": "ledger.schema.json",
    "pin-check.json": "pin-check.schema.json",
    "pin-check-probe.json": "pin-check.schema.json",
    "luna-call.json": "luna-call.schema.json",
}
REQUIRED_SCHEMAS = set(EXAMPLE_SCHEMAS.values())
REQUIRED_EXAMPLES = {"prompt.json", *EXAMPLE_SCHEMAS}


def check_date_time(value: object) -> bool:
    """Check offset timestamps even without jsonschema's optional format extras."""
    if not isinstance(value, str):
        return True
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}[Tt](?:[01]\d|2[0-3]):[0-5]\d:)"
        r"([0-5]\d|60)(\.\d+)?([Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)", value,
    )
    if match is None:
        return False
    prefix, second, fraction, zone = match.groups()
    # Python datetime does not represent leap seconds; check their date/offset
    # using the preceding second while retaining the RFC timestamp syntax.
    candidate = prefix.upper() + ("59" if second == "60" else second) + (fraction or "") + zone.upper()
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def format_checker() -> FormatChecker:
    """Keep schema format checks deterministic with the declared dependencies."""
    checker = FormatChecker()
    checker.checks("date-time")(check_date_time)
    return checker


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tree(schema_dir: Path = SCHEMA_DIR) -> tuple[int, int]:
    """Check each schema and sample; reject unmapped or missing sample files."""
    example_dir = schema_dir / "examples"
    schema_paths = sorted(path for path in schema_dir.rglob("*.json") if not path.is_relative_to(example_dir))
    schemas: dict[str, dict[str, Any]] = {}
    if not REQUIRED_SCHEMAS.issubset({path.relative_to(schema_dir).as_posix() for path in schema_paths}):
        raise ValueError("Missing required shared schema")
    for path in schema_paths:
        schema = read_json(path)
        if not isinstance(schema, dict) or schema.get("$schema") != DRAFT:
            raise ValueError(f"{path}: expected JSON Schema draft 2020-12")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as error:
            raise ValueError(f"{path}: {error.message}") from error
        schemas[path.relative_to(schema_dir).as_posix()] = schema

    # Register relative references and file URIs explicitly; never fetch schemas.
    registry: Registry = Registry()
    for name, schema in schemas.items():
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(name, resource)
        registry = registry.with_resource((schema_dir / name).resolve().as_uri(), resource)

    example_paths = sorted(path for path in example_dir.rglob("*") if path.is_file())
    if not REQUIRED_EXAMPLES.issubset({path.relative_to(example_dir).as_posix() for path in example_paths}):
        raise ValueError("Missing required reference sample")
    for path in example_paths:
        name = path.relative_to(example_dir).as_posix()
        if name == "prompt.json":
            schema = {"$schema": DRAFT, "$ref": "#/$defs/referencePrompt", "$defs": schemas["contract.schema.json"]["$defs"]}
        elif name in EXAMPLE_SCHEMAS:
            schema = schemas[EXAMPLE_SCHEMAS[name]]
        elif path.parent == example_dir and path.suffix == ".json" and path.stem.startswith("verdict_"):
            schema = schemas["verdict.schema.json"]
        else:
            raise ValueError(f"{path}: no schema mapping; all example files must be validated")
        try:
            Draft202012Validator(schema, registry=registry, format_checker=format_checker()).validate(read_json(path))
        except (ValidationError, Unresolvable) as error:
            raise ValueError(f"{path}: {error}") from error
    return len(schema_paths), len(example_paths)


def main() -> int:
    """Print a compact validation report and a nonzero exit code on failure."""
    try:
        schema_count, example_count = validate_tree()
    except (OSError, ValueError, SchemaError, ValidationError) as error:
        print(f"Schema validation failed: {error}", file=sys.stderr)
        return 1
    print(f"Validated {schema_count} draft 2020-12 schemas and {example_count} examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
