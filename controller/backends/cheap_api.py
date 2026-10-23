"""OpenAI Responses API structured output through an injectable HTTP transport."""

import json
import logging
import os
import time
from collections.abc import Callable
from dataclasses import asdict
from itertools import combinations
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator

from controller.analyze import Prices, calculate_cost
from controller.backends.base import Message, Usage, configured_prices, control_timeout, log_control_timeout
from controller.errors import BackendError, ControlTimeoutError, InputError, InvalidGeneration
from controller.settings import PACKAGE_DIR, load_object

logger = logging.getLogger(__name__)
Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


def post_json(
    endpoint: str, headers: dict[str, str], payload: dict[str, Any], timeout: float
) -> dict[str, Any]:
    """Send one request with no implicit paid retries or response-body logging."""
    request = Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers,
                      method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            value = json.load(response)
    except HTTPError as exc:
        raise BackendError(f"Control API returned HTTP {exc.code}") from exc
    except (URLError, OSError, ValueError) as exc:
        if isinstance(exc, TimeoutError) or (
            isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError)
        ):
            raise ControlTimeoutError("Control API timed out") from exc
        raise BackendError("Control API transport failed") from exc
    if not isinstance(value, dict):
        raise BackendError("Control API returned a non-object response")
    return value


def structured_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Adapt contract unions and optional keys to the strict API subset.

    Contract check alternatives have disjoint type constants, so replacing
    oneOf with anyOf preserves their meaning. Optional object keys become
    unions of complete objects, retaining absent versus exact-empty stdout.
    The original schema remains authoritative for local validation.
    """
    def visit(value: Any) -> Any:
        if isinstance(value, list):
            return [visit(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {("anyOf" if key == "oneOf" else key): visit(item)
                  for key, item in value.items() if key != "$schema"}
        if "const" in result:
            result["enum"] = [result.pop("const")]
        if result.get("type") == "object":
            properties = result.get("properties", {})
            required = result.get("required", [])
            optional = [key for key in properties if key not in required]
            if optional:
                variants = []
                for size in range(len(optional) + 1):
                    for subset in combinations(optional, size):
                        names = [key for key in properties if key in required or key in subset]
                        variants.append({**result, "properties": {key: properties[key] for key in names},
                                         "required": names, "additionalProperties": False})
                return {"anyOf": variants}
            result["required"] = list(properties)
            result["additionalProperties"] = False
        return result

    return visit(schema)


class CheapAPIBackend:
    """A single standard-tier request with provider usage and local validation."""

    def __init__(
        self, *, transport: Transport = post_json, config: dict[str, Any] | None = None,
        prices: Prices | None = None, clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config if config is not None else load_object(PACKAGE_DIR / "config.yaml")["cheap_api"]
        self.timeout = control_timeout(self.config)
        try:
            self.prices, self.pricing_ref = configured_prices(self.config, prices)
            self.model = str(self.config["model"])
            self.endpoint = str(self.config["endpoint"])
            self.max_output = int(self.config["max_output_tokens"])
            self.api_key_env = str(self.config["api_key_env"])
            if self.max_output <= 0 or not self.model:
                raise ValueError("Invalid API settings")
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise InputError("Invalid controller configuration or prices") from exc
        self.transport = transport
        self.clock = clock
        self._usage = Usage(None, None, None, 0.0)

    def usage(self) -> Usage:
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise InputError(f"Set {self.api_key_env} to use cheap_api")
        payload = {
            "model": self.model, "input": messages, "store": False,
            "service_tier": "default", "max_output_tokens": self.max_output,
            "text": {"format": {"type": "json_schema", "name": "controller_output",
                                "strict": True, "schema": structured_schema(schema)}},
        }
        started = self.clock()
        self._usage = Usage(None, None, None, 0.0)
        status = "error"
        try:
            response = self.transport(self.endpoint, {
                "Authorization": f"Bearer {key}", "Content-Type": "application/json"
            }, payload, self.timeout)
            usage = response.get("usage")
            if usage is None:
                usage = {}
            if not isinstance(usage, dict):
                raise BackendError("Control API returned invalid usage accounting")
            try:
                inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
                cached = (usage.get("input_tokens_details") or {}).get("cached_tokens")
                cost = (calculate_cost(inputs, outputs, self.prices, cached)
                        if inputs is not None and outputs is not None and cached is not None
                        and self.prices is not None else None)
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise BackendError("Control API returned invalid usage accounting") from exc
            for count in (inputs, outputs, cached):
                if count is not None and (type(count) is not int or count < 0):
                    raise BackendError("Control API returned invalid usage accounting")
            if cached is not None and inputs is not None and cached > inputs:
                raise BackendError("Control API cache exceeds total input")
            self._usage = Usage(inputs, outputs, cost, 0.0, cached)
            if response.get("model") not in (None, self.model):
                raise BackendError("Control API reported a conflicting model identity")
            if response.get("status") != "completed":
                raise BackendError("Control API generation did not complete")
            text_parts: list[str] = []
            try:
                for item in response.get("output", []):
                    if item.get("type") != "message":
                        continue
                    for part in item.get("content", []):
                        if part.get("type") == "refusal":
                            raise BackendError("Control API refused generation")
                        if part.get("type") == "output_text":
                            text_parts.append(part["text"])
                result = json.loads("".join(text_parts))
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InvalidGeneration("Control API returned malformed JSON output") from exc
            if not isinstance(result, dict) or not Draft202012Validator(schema).is_valid(result):
                raise InvalidGeneration("Control API output failed schema validation")
            status = "success"
            return result
        except (ControlTimeoutError, TimeoutError) as exc:
            log_control_timeout(logger, "cheap_api", self.model, self.timeout)
            raise ControlTimeoutError("Control API timed out") from exc
        finally:
            self._usage = Usage(
                self._usage.input_tokens, self._usage.output_tokens, self._usage.usd,
                max(0.0, self.clock() - started), self._usage.cached_input_tokens,
            )
            logger.info("control_call %s", json.dumps({
                "backend": "cheap_api", "model": self.model, "status": status,
                "timeout_seconds": self.timeout,
                "pricing_ref": self.pricing_ref,
                **asdict(self._usage),
            }, sort_keys=True))
