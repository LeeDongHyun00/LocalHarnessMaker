"""Command-scoped backend selection, call budget and audited fallback."""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from controller.backends.base import Backend, Message, Usage
from controller.backends.cheap_api import CheapAPIBackend
from controller.backends.codex_cli import CodexCLIBackend
from controller.backends.local import LocalBackend
from controller.errors import BackendError, InputError, TransportError
from controller.settings import PACKAGE_DIR, load_object

logger = logging.getLogger(__name__)


def sum_usage(usages: list[Usage]) -> Usage:
    """Propagate unknown accounting instead of fabricating zero for failed calls."""
    def total(field: str) -> Any:
        values = [getattr(usage, field) for usage in usages]
        return None if any(value is None for value in values) else sum(values)
    return Usage(total("input_tokens"), total("output_tokens"), total("usd"),
                 sum(u.latency_seconds for u in usages), total("cached_input_tokens"))


class RoutedBackend:
    """One budget shared by regeneration and at most one CLI-to-HTTP transition."""

    def __init__(self, selected: str, *, config: dict[str, Any] | None = None,
                 factories: dict[str, Callable[[], Backend]] | None = None) -> None:
        self.config = config if config is not None else load_object(PACKAGE_DIR / "config.yaml")
        if selected == "local" and not self.config["local"]["enabled"]:
            raise InputError("Local backend is disabled pending host serving verification; no cloud fallback was made")
        if selected not in ("codex_cli", "cheap_api", "local"):
            raise InputError("Unknown controller backend")
        policy = self.config.get("fallback", {})
        if policy.get("enabled") and policy.get("target") != "cheap_api":
            raise InputError("Only the approved CLI-to-cheap_api fallback is supported")
        self.selected = selected
        self.model = self.config[selected]["model"]
        self.factories = factories or {
            "codex_cli": lambda: CodexCLIBackend(config=self.config["codex_cli"]),
            "cheap_api": lambda: CheapAPIBackend(config=self.config["cheap_api"]),
            "local": lambda: LocalBackend(config=self.config["local"]),
        }
        self.instances: dict[str, Backend] = {}
        self.calls: list[dict[str, Any]] = []
        self._usage = Usage(None, None, None, 0.0)
        self.count = 0
        self.pricing_ref: str | None = None

    def usage(self) -> Usage:
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        usages: list[Usage] = []
        while self.count < 3:
            self.count += 1
            backend = None
            fallback_reason = None
            try:
                backend = self.instances.get(self.selected)
                if backend is None:
                    backend = self.factories[self.selected]()
                    self.instances[self.selected] = backend
                self.model = getattr(backend, "model", self.config[self.selected]["model"])
                self.pricing_ref = getattr(backend, "pricing_ref", None)
                return backend.generate(schema, messages)
            except TransportError as exc:
                policy = self.config.get("fallback", {})
                if (self.selected != "codex_cli" or not policy.get("enabled", False)
                        or self.count >= 3):
                    raise BackendError("CLI transport failed without an available fallback slot") from exc
                api = self.config["cheap_api"]
                if api["model"] != self.model or not os.environ.get(api["api_key_env"]):
                    raise BackendError("CLI fallback requires the same model and an environment API key") from exc
                fallback_reason = str(exc)
            finally:
                usage = backend.usage() if backend is not None else Usage(None, None, None, 0.0)
                usages.append(usage)
                self._usage = sum_usage(usages)
                record = {"backend": self.selected, "model": self.model,
                          "pricing_ref": self.pricing_ref, "fallback_reason": fallback_reason,
                          **asdict(usage)}
                self.calls.append(record)
                logger.info("control_route %s", json.dumps(record, sort_keys=True))
            self.selected = "cheap_api"
        raise BackendError("Controller exhausted its shared three-generation budget")
