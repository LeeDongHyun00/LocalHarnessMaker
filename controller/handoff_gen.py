"""Generate handoffs constrained by the contract and trusted verdict."""

from pathlib import Path
from typing import Any

from controller.backends.base import Backend, Message
from controller.contract_gen import data_block
from controller.errors import InputError, InvalidGeneration
from controller.generation import generate_validated, read_text, schema_validator, validate_input
from controller.settings import PACKAGE_DIR, SCHEMA_DIR, load_object


def validate_handoff_inputs(contract: dict[str, Any], verdict: dict[str, Any]) -> dict[str, str]:
    validate_input(contract, "contract.schema.json")
    validate_input(verdict, "verdict.schema.json")
    ids = [item["id"] for item in contract["success_criteria"]]
    statuses = {item["id"]: item["status"] for item in verdict["items"]}
    if (len(set(ids)) != len(ids) or len(statuses) != len(verdict["items"])
            or set(ids) != set(statuses)
            or (verdict["overall"] == "pass") != all(s == "pass" for s in statuses.values())
            or (verdict["overall"] == "pass" and verdict["reinstruct_message"] is not None)):
        raise InputError("Contract/verdict criterion IDs or overall status are inconsistent")
    return statuses


def generate_handoff(transcript: str, contract: dict[str, Any], verdict: dict[str, Any],
                     backend: Backend) -> dict[str, Any]:
    statuses = validate_handoff_inputs(contract, verdict)
    schema = load_object(SCHEMA_DIR / "handoff.schema.json")
    messages: list[Message] = [
        {"role": "system", "content": read_text(PACKAGE_DIR / "prompts/handoff.md")},
        {"role": "user", "content": "\n".join((data_block("transcript", transcript),
            data_block("contract", contract), data_block("verdict", verdict)))},
    ]

    def finish(value: dict[str, Any]) -> dict[str, Any]:
        if not schema_validator("handoff.schema.json").is_valid(value):
            raise InvalidGeneration("Handoff failed schema validation")
        done = [item["criterion_id"] for item in value["done"]]
        remaining = [item["criterion_id"] for item in value["remaining"]]
        if (len(set(done + remaining)) != len(done + remaining)
                or set(done + remaining) != set(statuses)
                or any(statuses[item] != "pass" for item in done)
                or any(statuses[item] == "pass" for item in remaining)):
            raise InvalidGeneration("Handoff contradicts trusted verdict or drops criteria")
        return value

    return generate_validated(backend, schema, messages, finish)
