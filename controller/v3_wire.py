"""Private strict output adapters; no executable checks or accounting from Luna."""

from typing import Any


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False,
            "required": list(properties), "properties": properties}


def array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


TEXT = {"type": "string", "minLength": 1}
KINDS = ["behavior", "constraint", "protected_file", "named_file", "named_command", "test_command"]
REQUIREMENTS = obj({
    "requirements": {**array(obj({"text": TEXT, "kind": {"enum": KINDS},
                                  "source_excerpt": TEXT})), "minItems": 1},
    "open_questions": array(obj({"text": TEXT, "requirement_numbers": {
        **array({"type": "integer", "minimum": 1}), "uniqueItems": True}})),
})
CLAIMS = obj({"claims": array(obj({
    "requirement_id": TEXT, "claim_excerpt": TEXT,
    "citations": array(obj({"citation_excerpt": TEXT})),
    "assessment": {"enum": ["supported", "unsupported", "unverifiable"]},
}))})
