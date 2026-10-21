"""Offline schema validation and shared bounded structured generation."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from controller.backends.base import Backend, Message
from controller.errors import InputError, InvalidGeneration
from controller.settings import SCHEMA_DIR, load_object


def schema_validator(name: str) -> Draft202012Validator:
    """Resolve published relative references from a local-only registry."""
    resources = [(path.name, Resource.from_contents(load_object(path)))
                 for path in SCHEMA_DIR.glob("*.schema.json")]
    registry = Registry().with_resources(resources)
    return Draft202012Validator(load_object(SCHEMA_DIR / name), registry=registry,
                                format_checker=FormatChecker())


def validate_input(value: dict[str, Any], schema: str) -> None:
    if not schema_validator(schema).is_valid(value):
        raise InputError(f"Input failed {schema} validation")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"Cannot read UTF-8 input: {path}") from exc


def generate_validated(
    backend: Backend, schema: dict[str, Any], messages: list[Message],
    finish: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Regenerate invalid content only, without resetting backend call budgets."""
    for attempt in range(3):
        try:
            return finish(backend.generate(schema, messages))
        except InvalidGeneration:
            if attempt == 2:
                raise
            messages.append({"role": "system", "content": (
                "Regenerate the complete object from the original data. The preceding "
                "output violated the schema or cross-artifact consistency rules."
            )})
    raise InvalidGeneration("Generation exhausted")
