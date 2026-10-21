"""Explicit local JSON-schema decoding through a configurable chat endpoint."""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator

from controller.analyze import Prices, calculate_cost
from controller.backends.base import Message, Usage, configured_prices
from controller.backends.cheap_api import Transport, post_json, structured_schema
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.settings import PACKAGE_DIR, load_object

logger = logging.getLogger(__name__)


class LocalBackend:
    """Never download/start a server or fall back to cloud implicitly."""

    def __init__(self, *, transport: Transport = post_json,
                 config: dict[str, Any] | None = None, prices: Prices | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config if config is not None else load_object(PACKAGE_DIR / "config.yaml")["local"]
        if not self.config.get("enabled", False):
            raise InputError("Local backend is disabled pending host serving verification; no cloud fallback was made")
        try:
            self.model = self.config["model"]
            self.endpoint = self.config["endpoint"]
            self.timeout = float(self.config["timeout_seconds"])
            self.max_output = int(self.config["max_output_tokens"])
            self.prices, self.pricing_ref = configured_prices(self.config, prices)
            if (not self.model or self.timeout <= 0 or self.max_output <= 0
                    or urlparse(self.endpoint).hostname not in ("localhost", "127.0.0.1", "::1")):
                raise ValueError("Invalid local model endpoint or limits")
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise InputError("Invalid local configuration") from exc
        self.transport, self.clock = transport, clock
        self._usage = Usage(None, None, None, 0.0)

    def usage(self) -> Usage:
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        started = self.clock()
        self._usage = Usage(None, None, None, 0.0)
        status = "error"
        try:
            response = self.transport(self.endpoint, {"Content-Type": "application/json"}, {
                "model": self.model, "messages": messages, "max_tokens": self.max_output,
                "stream": False, "response_format": {"type": "json_schema", "json_schema": {
                    "name": "controller_output", "strict": True, "schema": structured_schema(schema),
                }},
            }, self.timeout)
            usage = response.get("usage") or {}
            try:
                inputs, outputs = usage.get("prompt_tokens"), usage.get("completion_tokens")
                cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
                for count in (inputs, outputs, cached):
                    if count is not None and (type(count) is not int or count < 0):
                        raise ValueError("Invalid count")
                if cached is not None and inputs is not None and cached > inputs:
                    raise ValueError("Invalid cache subset")
                cost = (calculate_cost(inputs, outputs, self.prices, cached)
                        if None not in (inputs, outputs, cached, self.prices) else None)
            except (TypeError, AttributeError, ValueError) as exc:
                raise BackendError("Local server returned invalid usage accounting") from exc
            self._usage = Usage(inputs, outputs, cost, 0.0, cached)
            if response.get("model") not in (None, self.model):
                raise BackendError("Local server reported a conflicting model identity")
            try:
                choice = response["choices"][0]
                if choice["finish_reason"] != "stop":
                    raise BackendError("Local generation did not complete")
                value = json.loads(choice["message"]["content"])
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise InvalidGeneration("Local server returned invalid structured content") from exc
            if not isinstance(value, dict) or not Draft202012Validator(schema).is_valid(value):
                raise InvalidGeneration("Local output failed schema validation")
            status = "success"
            return value
        finally:
            self._usage = Usage(self._usage.input_tokens, self._usage.output_tokens, self._usage.usd,
                                max(0.0, self.clock() - started), self._usage.cached_input_tokens)
            logger.info("control_call %s", json.dumps({"backend": "local", "model": self.model,
                "status": status, "pricing_ref": self.pricing_ref, **asdict(self._usage)}, sort_keys=True))
