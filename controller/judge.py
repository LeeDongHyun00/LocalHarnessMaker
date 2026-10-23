"""Generate a single rubric judgment with code-owned identity and accounting."""

import copy
import os
import time
from pathlib import Path
from typing import Any

from controller.backends.base import Backend, Message, Usage
from controller.backends.routing import sum_usage
from controller.contract_gen import data_block
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.generation import generate_validated, read_text, schema_validator, validate_input
from controller.settings import PACKAGE_DIR, SCHEMA_DIR, load_object


def artifact_snapshot(path: Path) -> dict[str, Any]:
    """Read evidence explicitly; reject symlink escapes and oversized snapshots."""
    config = load_object(PACKAGE_DIR / "config.yaml")
    limit = config.get("artifact_max_bytes", 1_000_000)
    excluded = set(config.get("artifact_exclude_dirs", []))
    if not path.exists() or path.is_symlink():
        raise InputError("--artifact must be a readable file or directory, not a symlink")
    files: dict[str, str] = {}
    omitted: dict[str, str] = {}
    size = 0

    def walk_error(error: OSError) -> None:
        raise error

    try:
        paths = []
        if path.is_dir():
            for root, directories, names in os.walk(path, onerror=walk_error, followlinks=False):
                parent = Path(root)
                for name in sorted(directories):
                    directory = parent / name
                    if name in excluded:
                        omitted[str(directory.relative_to(path))] = "configured directory exclusion"
                        directories.remove(name)
                    elif directory.is_symlink():
                        raise InputError("Artifact contains a symlink; supply a materialized evidence copy")
                directories.sort()
                paths.extend(parent / name for name in sorted(names))
        else:
            paths = [path]
        for item in paths:
            if item.is_symlink():
                raise InputError("Artifact contains a symlink; supply a materialized evidence copy")
            name = str(item.relative_to(path)) if path.is_dir() else item.name
            if size + item.stat().st_size > limit:
                omitted[name] = "exceeds remaining artifact_max_bytes"
                continue
            try:
                content = item.read_text(encoding="utf-8")
            except UnicodeError:
                omitted[name] = "not UTF-8 text; content unavailable to judge"
                continue
            size += item.stat().st_size
            files[name] = content
        return {"path": str(path), "files": files, "omitted": omitted}
    except OSError as exc:
        raise InputError("Cannot read artifact snapshot") from exc


def generate_judgment(
    criterion: dict[str, Any], artifact: Path, backend: Backend, *, prompt_version: str = "v2",
) -> dict[str, Any]:
    validate_input(criterion, "judgment-input.schema.json")
    if prompt_version not in ("v1", "v2"):
        raise InputError("Unknown judge prompt version")
    snapshot = artifact_snapshot(artifact)
    schema = load_object(SCHEMA_DIR / "judgment.schema.json")
    model_schema = copy.deepcopy(schema)
    for field in ("criterion_id", "model", "usage"):
        model_schema["properties"].pop(field)
        model_schema["required"].remove(field)
    model_schema.pop("$defs")
    messages: list[Message] = [
        {"role": "system", "content": read_text(PACKAGE_DIR / "prompts" / (
            "judge-v1.md" if prompt_version == "v1" else "judge.md"))},
        {"role": "user", "content": data_block("criterion", criterion) + "\n" + data_block("artifact", snapshot)},
    ]
    usages: list[Usage] = []
    started = time.monotonic()

    def finish(value: dict[str, Any]) -> dict[str, Any]:
        usages.append(backend.usage())
        usage = sum_usage(usages)
        model = getattr(backend, "model", None)
        if not isinstance(model, str) or not model:
            raise BackendError("Judge backend has no selected model identity")
        result = {**value, "criterion_id": criterion["id"], "model": model, "usage": {
            "input_tokens": usage.input_tokens, "cached_input_tokens": usage.cached_input_tokens,
            "output_tokens": usage.output_tokens, "usd": usage.usd,
            "latency_seconds": max(0.0, time.monotonic() - started),
            "cost_basis": "api_equivalent_usd", "pricing_ref": getattr(backend, "pricing_ref", None),
        }}
        if (not schema_validator("judgment.schema.json").is_valid(result)
                or "llm_judge" not in result.get("evidence", "")
                or (usage.input_tokens is not None and usage.cached_input_tokens is not None
                    and usage.cached_input_tokens > usage.input_tokens)):
            raise InvalidGeneration("Judgment failed schema or accounting validation")
        return result

    # Account for invalid JSON/schema calls too, before the next regeneration.
    class AccountedBackend:
        def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
            try:
                return backend.generate(schema, messages)
            except InvalidGeneration:
                usages.append(backend.usage())
                raise

        def usage(self) -> Usage:
            return backend.usage()

    return generate_validated(AccountedBackend(), model_schema, messages, finish)
