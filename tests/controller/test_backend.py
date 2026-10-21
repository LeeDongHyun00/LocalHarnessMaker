import copy
import io
import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest
from jsonschema import Draft202012Validator

from controller.backends.cheap_api import CheapAPIBackend, post_json, structured_schema
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.settings import load_object
from tests.controller.support import ROOT, RecordingTransport, model_contract, response


@pytest.fixture(autouse=True)
def dummy_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-not-a-real-key")


def test_request_golden_and_provider_usage(caplog: pytest.LogCaptureFixture) -> None:
    transport = RecordingTransport()
    ticks = iter([10.0, 10.25])
    backend = CheapAPIBackend(transport=transport, clock=lambda: next(ticks))
    schema = load_object(ROOT / "schemas/contract.schema.json")
    for field in ("reasoning_effort", "cost_estimate"):
        schema["properties"].pop(field)
        schema["required"].remove(field)
    messages = [{"role": "user", "content": "task data"}]
    with caplog.at_level(logging.INFO):
        assert backend.generate(schema, messages) == model_contract()
    call = transport.calls[0]
    config = load_object(ROOT / "controller/config.yaml")["cheap_api"]
    assert call["endpoint"] == config["endpoint"]
    assert call["timeout"] == config["timeout_seconds"]
    assert call["payload"] == {
        "model": config["model"], "input": messages, "store": False, "service_tier": "default",
        "max_output_tokens": config["max_output_tokens"],
        "text": {"format": {"type": "json_schema", "name": "controller_output",
                            "strict": True, "schema": structured_schema(schema)}},
    }
    usage = backend.usage()
    assert (usage.input_tokens, usage.output_tokens, usage.cached_input_tokens) == (1000, 200, 100)
    assert usage.usd == 0.000191
    assert usage.latency_seconds == 0.25
    log = caplog.records[-1].getMessage()
    assert '"usd": 0.000191' in log and '"latency_seconds": 0.25' in log
    assert "test-placeholder" not in log and "task data" not in log
    assert config["model"] == "gpt-6-luna"


def test_wire_schema_preserves_optional_stdout_and_disjoint_checks() -> None:
    schema = load_object(ROOT / "schemas/contract.schema.json")
    original = copy.deepcopy(schema)
    wire = structured_schema(schema)
    Draft202012Validator.check_schema(wire)
    assert schema == original
    assert '"oneOf":' not in json.dumps(wire)
    assert '"const":' not in json.dumps(wire)
    value = load_object(ROOT / "schemas/examples/contract.json")
    assert Draft202012Validator(wire).is_valid(value)
    for check in ({"type": "file_exists", "path": "READY.txt"},
                  {"type": "regex", "path": "config.ini", "pattern": "timeout=30"},
                  {"type": "llm_judge", "rubric": "Inspect the result"},
                  {"type": "command", "command": "true", "expected": {"exit_code": 0, "stdout": ""}}):
        value["success_criteria"][0]["check"] = check
        assert Draft202012Validator(wire).is_valid(value)
        assert Draft202012Validator(schema).is_valid(value)
    value["success_criteria"][0]["check"]["expected"]["stdout"] = None
    assert not Draft202012Validator(wire).is_valid(value)


@pytest.mark.parametrize("text", ["not JSON", "[]", "{}", '{"task_summary": ""}'])
def test_invalid_generation_is_distinct_and_accounted(text: str) -> None:
    backend = CheapAPIBackend(transport=RecordingTransport([response(text=text)]))
    with pytest.raises(InvalidGeneration):
        backend.generate(load_object(ROOT / "schemas/contract.schema.json"), [])
    assert backend.usage().usd == 0.000191


@pytest.mark.parametrize("kind", ["refusal", "incomplete", "invalid-usage"])
def test_failures_do_not_claim_success(kind: str, caplog: pytest.LogCaptureFixture) -> None:
    envelope = response()
    if kind == "refusal":
        envelope["output"][0]["content"] = [{"type": "refusal", "refusal": "private"}]
    elif kind == "incomplete":
        envelope["status"] = "incomplete"
    elif kind == "missing-usage":
        envelope.pop("usage")
    else:
        envelope["usage"]["input_tokens"] = -1
    backend = CheapAPIBackend(transport=RecordingTransport([envelope]))
    with caplog.at_level(logging.INFO), pytest.raises(BackendError):
        backend.generate({}, [])
    assert '"status": "error"' in caplog.text
    assert "private" not in caplog.text


def test_missing_key_never_calls_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY")
    transport = RecordingTransport()
    with pytest.raises(InputError, match="OPENAI_API_KEY"):
        CheapAPIBackend(transport=transport).generate({}, [])
    assert not transport.calls


def test_transport_error_logs_unknown_cost(caplog: pytest.LogCaptureFixture) -> None:
    def fail(*args: Any) -> dict[str, Any]:
        raise BackendError("Transport failed")
    backend = CheapAPIBackend(transport=fail)
    with caplog.at_level(logging.INFO), pytest.raises(BackendError):
        backend.generate({}, [])
    assert backend.usage().usd is None
    assert '"usd": null' in caplog.text
    assert '"latency_seconds":' in caplog.text


def test_stdlib_transport_encodes_request(monkeypatch: pytest.MonkeyPatch) -> None:
    def opener(request: Request, timeout: float) -> io.BytesIO:
        assert request.method == "POST"
        assert json.loads(request.data or b"") == {"input": "한글"}
        assert timeout == 3
        return io.BytesIO(b'{"status":"completed"}')
    monkeypatch.setattr("controller.backends.cheap_api.urlopen", opener)
    assert post_json("https://example.invalid", {}, {"input": "한글"}, 3) == {"status": "completed"}


@pytest.mark.parametrize("error", [HTTPError("https://example.invalid", 401, "secret", {}, None),
                                  URLError("secret"), TimeoutError("secret")])
def test_transport_sanitizes_errors(error: Exception, monkeypatch: pytest.MonkeyPatch) -> None:
    def opener(*args: Any, **kwargs: Any) -> Any:
        raise error
    monkeypatch.setattr("controller.backends.cheap_api.urlopen", opener)
    with pytest.raises(BackendError) as caught:
        post_json("https://example.invalid", {}, {}, 3)
    assert "secret" not in str(caught.value)


def test_missing_usage_remains_unknown() -> None:
    envelope = response()
    envelope.pop("usage")
    backend = CheapAPIBackend(transport=RecordingTransport([envelope]))
    backend.generate({}, [])
    assert backend.usage().input_tokens is None
    assert backend.usage().usd is None
