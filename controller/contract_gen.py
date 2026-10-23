"""Version-two contract prompting and bounded validation retries."""

import copy
import json
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from controller.analyze import reasoning_effort
from controller.backends.base import Backend, Message
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.settings import PACKAGE_DIR, SCHEMA_DIR, load_object

logger = logging.getLogger(__name__)


def data_block(name: str, value: Any) -> str:
    """Encode untrusted data so it cannot close its enclosing data block."""
    encoded = json.dumps(value, ensure_ascii=True).replace("<", "\\u003c").replace(
        ">", "\\u003e"
    ).replace("&", "\\u0026")
    return f"<{name}_data>\n{encoded}\n</{name}_data>"


def build_messages(
    request: str, handoff: dict[str, Any] | None = None,
    examples: list[dict[str, Any]] | None = None,
) -> list[Message]:
    """Keep authoritative instructions separate from every input data source."""
    template = (PACKAGE_DIR / "prompts" / "contract.md").read_text(encoding="utf-8")
    return [
        {"role": "system", "content": template},
        {"role": "user", "content": "\n".join((
            data_block("request", request), data_block("handoff", handoff),
            data_block("examples", examples or []),
        ))},
    ]


def mechanical_request_hints(request: str) -> list[str]:
    """Recognize objective anchors in request text without inspecting a workspace.

    These are lexical hints for a quality retry, never asserted workspace facts.
    The original request stays in its escaped data block; feedback is code-owned.
    """
    hints: list[str] = []
    if re.search(
        r"(?<![\w])(?:[\w-]+/)*(?:[\w-]+\.[A-Za-z][\w-]*|\.[A-Za-z][\w-]*)"
        r"|\b(?:README|LICENSE|Dockerfile|Makefile)\b"
        r"|\bfile\s+[`'\"][A-Za-z_][\w/-]*[`'\"]", request,
    ):
        hints.append("named files or modules")
    if re.search(
        r"\b(?:functions?|methods?|def|modules?)\s+[`'\"]?[A-Za-z_]\w*"
        r"|\b[A-Za-z_]\w*\s*\(", request, re.IGNORECASE,
    ):
        hints.append("named functions or modules")
    if re.search(r"\b(?:tests?|testing|pytest|unittest)\b", request, re.IGNORECASE):
        hints.append("tests")
    return hints


def generate_contract(
    request: str, backend: Backend, *, handoff: dict[str, Any] | None = None,
    examples: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate at most three times, then attach only code/provider metadata."""
    if not isinstance(request, str) or not request.strip():
        raise InputError("The request must be a nonempty string")
    if handoff is not None and not Draft202012Validator(
        load_object(SCHEMA_DIR / "handoff.schema.json")
    ).is_valid(handoff):
        raise InputError("Handoff failed schema validation")
    schema = load_object(SCHEMA_DIR / "contract.schema.json")
    validator = Draft202012Validator(schema)
    for example in examples or []:
        if not validator.is_valid(example):
            raise InputError("Example failed contract schema validation")
    model_schema = copy.deepcopy(schema)
    for field in ("reasoning_effort", "cost_estimate"):
        model_schema["properties"].pop(field)
        model_schema["required"].remove(field)
    messages = build_messages(request, handoff, examples)
    hints = mechanical_request_hints(request)
    quality_regenerated = False
    total_input = total_output = 0
    total_cost = Decimal(0)
    for attempt in range(3):
        invalid: InvalidGeneration | None = None
        try:
            generated = backend.generate(model_schema, messages)
        except InvalidGeneration as exc:
            invalid = exc
            generated = {}
        usage = backend.usage()
        if usage.input_tokens is None or usage.output_tokens is None or usage.usd is None:
            raise BackendError("Generation has no reliable usage accounting")
        total_input += usage.input_tokens
        total_output += usage.output_tokens
        total_cost += Decimal(str(usage.usd))
        contract = copy.deepcopy(generated)
        contract["reasoning_effort"] = reasoning_effort(request)
        contract["cost_estimate"] = {
            "input_tokens": total_input, "output_tokens": total_output, "usd": float(total_cost)
        }
        if invalid is None and validator.is_valid(contract):
            mechanical = any(item["check"]["type"] in {"command", "file_exists", "regex"}
                             for item in contract["success_criteria"])
            if not hints or mechanical:
                return contract
            logger.info("contract_quality_gate %s", json.dumps({
                "attempt": attempt + 1,
                "action": ("accept_degraded" if quality_regenerated else
                           "reject" if attempt == 2 else "regenerate"),
            }))
            if quality_regenerated:
                contract["assumptions"].append(
                    "No mechanical check could be derived from the request, so every "
                    "success criterion requires judgment."
                )
                return contract
            if attempt == 2:
                raise InvalidGeneration(
                    "Contract quality gate: no mechanical success criteria for "
                    + ", ".join(hints)
                )
            quality_regenerated = True
            messages.append({"role": "system", "content": (
                "Contract quality gate: the request mentions " + ", ".join(hints) + ". "
                "The preceding contract contained no mechanical success criterion. "
                "Regenerate the complete object with command, file_exists or regex checks "
                "grounded in the request. Use py_compile for named Python files; use the "
                "named test command, or standard discovery when tests are mentioned. "
                "For named functions, check the named definition or specified behavior "
                "where its location is known; otherwise propose test discovery and record "
                "the unknown location. Follow only the allowed command forms in the "
                "original system prompt. List every inferred path/runner/discovery choice "
                "under assumptions for user review. Reserve llm_judge for scope/style or "
                "requirements objective checks cannot express. Include command criteria "
                "in verification. Do not add reasoning_effort or cost_estimate."
            )})
            continue
        if attempt < 2:
            messages.append({"role": "system", "content": (
                "The preceding generation failed JSON or schema validation. Regenerate the "
                "complete JSON object using the original input data and output schema. "
                "Do not add reasoning_effort or cost_estimate."
            )})
    raise InvalidGeneration("Contract failed validation after 3 generations (2 regenerations)")


def read_request(path: Path) -> str:
    """Accept UTF-8 text or the shared JSON-string prompt fixture."""
    try:
        text = path.read_text(encoding="utf-8")
        request = json.loads(text) if path.suffix.lower() == ".json" else text
    except (OSError, ValueError) as exc:
        raise InputError(f"Cannot read prompt: {path}") from exc
    if not isinstance(request, str) or not request.strip():
        raise InputError("Prompt must contain nonempty text or a JSON string")
    return request
