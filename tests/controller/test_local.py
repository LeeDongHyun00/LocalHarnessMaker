"""Local serving protocol tests use injected HTTP only."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from controller.backends.local import LocalBackend
from controller.backends.routing import RoutedBackend
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.judge import generate_judgment
from controller.settings import load_object
from tests.controller.support import ROOT, RecordingTransport
from tests.controller.test_commands import criterion, judgment


def local_config() -> dict[str, Any]:
    value = load_object(ROOT / "controller/config.yaml")["local"]
    return {**value, "enabled": True}


def envelope(value: Any = None) -> dict[str, Any]:
    return {"model": "gemma-4-12b", "usage": {"prompt_tokens": 10, "completion_tokens": 5,
        "prompt_tokens_details": {"cached_tokens": 0}},
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(
            judgment() if value is None else value)}}]}


def test_local_schema_request_and_null_price(tmp_path: Path) -> None:
    transport = RecordingTransport([envelope()])
    backend = LocalBackend(config=local_config(), transport=transport)
    result = generate_judgment(criterion(), tmp_path, backend)
    assert result["model"] == "gemma-4-12b"
    assert result["usage"]["input_tokens"] == 10
    assert result["usage"]["usd"] is None and result["usage"]["pricing_ref"] is None
    payload = transport.calls[0]["payload"]
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert transport.calls[0]["headers"] == {"Content-Type": "application/json"}


@pytest.mark.parametrize("kind", ["invalid-json", "incomplete", "model", "cache", "unavailable"])
def test_local_failures_no_cloud_fallback(kind: str, tmp_path: Path) -> None:
    value = envelope()
    if kind == "invalid-json":
        value["choices"][0]["message"]["content"] = "broken"
    elif kind == "incomplete":
        value["choices"][0]["finish_reason"] = "length"
    elif kind == "model":
        value["model"] = "wrong"
    elif kind == "cache":
        value["usage"]["prompt_tokens_details"]["cached_tokens"] = 100
    transport = RecordingTransport([copy.deepcopy(value) for _ in range(3)])
    def send(*args: Any) -> dict[str, Any]:
        if kind == "unavailable":
            raise BackendError("Local server unavailable")
        return transport(*args)
    config = load_object(ROOT / "controller/config.yaml")
    config["local"] = local_config()
    backend = RoutedBackend("local", config=config, factories={
        "local": lambda: LocalBackend(config=local_config(), transport=send),
        "cheap_api": lambda: pytest.fail("Local must not fall back"),
    })
    with pytest.raises(BackendError):
        generate_judgment(criterion(), tmp_path, backend)
    assert backend.count == (3 if kind == "invalid-json" else 1)


def test_local_disabled_and_remote_endpoint_rejected() -> None:
    with pytest.raises(InputError, match="disabled"):
        LocalBackend()
    config = {**local_config(), "endpoint": "https://remote.invalid/v1/chat/completions"}
    with pytest.raises(InputError):
        LocalBackend(config=config)
