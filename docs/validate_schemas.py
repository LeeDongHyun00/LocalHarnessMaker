"""Validate shared schemas and every reference sample without executing checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
REQUIRED_SCHEMAS = {"contract.schema.json", "verdict.schema.json", "handoff.schema.json"}
REQUIRED_EXAMPLES = {"prompt.json", "contract.json", "verdict_pass.json", "verdict_fail.json", "handoff.json"}


def read_json(path: Path) -> Any:
    """Read a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def validate_tree(schema_dir: Path = SCHEMA_DIR) -> tuple[int, int]:
    """Check each schema and sample; reject unmapped or missing sample files."""
    example_dir = schema_dir / "examples"
    schema_paths = sorted(path for path in schema_dir.rglob("*.json") if not path.is_relative_to(example_dir))
    schemas: dict[str, dict[str, Any]] = {}
    if not REQUIRED_SCHEMAS.issubset({path.relative_to(schema_dir).as_posix() for path in schema_paths}):
        raise ValueError("Missing required contract, verdict, or handoff schema")
    for path in schema_paths:
        schema = read_json(path)
        if not isinstance(schema, dict) or schema.get("$schema") != DRAFT:
            raise ValueError(f"{path}: expected JSON Schema draft 2020-12")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as error:
            raise ValueError(f"{path}: {error.message}") from error
        schemas[path.relative_to(schema_dir).as_posix()] = schema

    example_paths = sorted(path for path in example_dir.rglob("*") if path.is_file())
    if not REQUIRED_EXAMPLES.issubset({path.relative_to(example_dir).as_posix() for path in example_paths}):
        raise ValueError("Missing required reference sample")
    for path in example_paths:
        name = path.relative_to(example_dir).as_posix()
        if name == "prompt.json":
            schema = {"$schema": DRAFT, "$ref": "#/$defs/referencePrompt", "$defs": schemas["contract.schema.json"]["$defs"]}
        elif name in {"contract.json", "handoff.json"}:
            schema = schemas[f"{path.stem}.schema.json"]
        elif path.parent == example_dir and path.suffix == ".json" and path.stem.startswith("verdict_"):
            schema = schemas["verdict.schema.json"]
        else:
            raise ValueError(f"{path}: no schema mapping; all example files must be validated")
        try:
            Draft202012Validator(schema).validate(read_json(path))
        except ValidationError as error:
            raise ValueError(f"{path}: {error.message}") from error
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
