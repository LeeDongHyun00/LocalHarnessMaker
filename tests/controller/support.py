"""Hand-written golden objects; never collected from paid model output."""

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def model_contract() -> dict[str, Any]:
    """Reuse the shared hand-written FastAPI fixture without code-only metadata."""
    value = json.loads((ROOT / "schemas/examples/contract.json").read_text(encoding="utf-8"))
    value.pop("reasoning_effort")
    value.pop("cost_estimate")
    value["assumptions"] = value["assumptions"][:-1]
    return value


def response(value: Any = None, *, text: str | None = None) -> dict[str, Any]:
    """Return a fixed Responses API envelope with explicit synthetic usage."""
    return {
        "status": "completed",
        "usage": {"input_tokens": 1000, "output_tokens": 200,
                  "input_tokens_details": {"cached_tokens": 100}},
        "output": [{"type": "message", "content": [{"type": "output_text",
                    "text": text if text is not None else json.dumps(
                        model_contract() if value is None else value
                    )}]}],
    }


class RecordingTransport:
    """One supplied response per call; never performs HTTP."""

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.responses = copy.deepcopy(responses if responses is not None else [response()])
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self, endpoint: str, headers: dict[str, str], payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        self.calls.append({"endpoint": endpoint, "headers": headers,
                           "payload": copy.deepcopy(payload), "timeout": timeout})
        return self.responses.pop(0)
