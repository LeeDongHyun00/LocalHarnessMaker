"""Private strict output adapters; no executable checks or accounting from Luna."""

from typing import Any


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False,
            "required": list(properties), "properties": properties}


def array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


TEXT = {"type": "string"}
KINDS = ["behavior", "constraint", "protected_file", "named_file", "named_command", "test_command"]
REQUIREMENTS = obj({
    "requirements": array(obj({"text": TEXT, "kind": {"type": "string", "enum": KINDS},
                                "source_excerpt": TEXT})),
    "open_questions": array(obj({"text": TEXT, "requirement_numbers": array({"type": "integer"})})),
})
CLAIMS = obj({"claims": array(obj({
    "requirement_id": {**TEXT, "minLength": 1}, "claim_excerpt": {**TEXT, "minLength": 1},
    "citations": array(obj({"citation_excerpt": {**TEXT, "minLength": 1}})),
    "assessment": {"enum": ["supported", "unsupported", "unverifiable"]},
}))})


def validate_requirements_output(value: dict[str, Any]) -> None:
    """Enforce artifact semantics locally, outside the provider's schema subset."""
    if not value["requirements"]:
        raise ValueError("requirements must be nonempty")
    for row in value["requirements"]:
        if not row["text"] or not row["source_excerpt"]:
            raise ValueError("requirement text and excerpt must be nonempty")
    for question in value["open_questions"]:
        numbers = question["requirement_numbers"]
        if (not question["text"] or len(numbers) != len(set(numbers))
                or any(number < 1 or number > len(value["requirements"]) for number in numbers)):
            raise ValueError("question text or requirement numbers are invalid")
