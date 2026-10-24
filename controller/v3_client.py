"""One-shot pinned Luna transport, isolated from historical routing and retries."""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from controller.analyze import Prices
from controller.backends.base import Message, Usage
from controller.backends.codex_cli import CodexCLIBackend, Runner
from controller.errors import BackendError
from controller.settings import PACKAGE_DIR, load_object

MODEL = "gpt-6-luna"


class PinMismatch(BackendError):
    """Native identity was missing, malformed or different from the pinned model."""


def native_models(events: str) -> list[str]:
    """Read native metadata fields, never parse assistant text as identity evidence."""
    models: list[str] = []
    for line in events.splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("native event is not an object")
        containers = [event]
        if event.get("type") in {"session_meta", "turn_context", "session.started", "turn.started"}:
            if isinstance(event.get("payload"), dict):
                containers.append(event["payload"])
        for container in containers:
            if "model" in container:
                model = container["model"]
                if not isinstance(model, str) or not model:
                    raise ValueError("native model identity is invalid")
                models.append(model)
    return models


class PinnedLunaClient:
    """One provider invocation per instance, including failure; no automatic fallback."""

    def __init__(self, prices: Prices, pricing_ref: str, *, runner: Runner = subprocess.run,
                 config: dict[str, Any] | None = None,
                 clock: Callable[[], float] | None = None) -> None:
        settings = dict(config or load_object(PACKAGE_DIR / "config.yaml")["codex_cli"])
        if settings.get("model") != MODEL or settings.get("reasoning_effort") != "low":
            raise PinMismatch("requested model/effort violates the pin")
        self.events = ""
        self.model: str | None = None
        self.invoked = False
        self.timeout = False

        def capture(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            try:
                result = runner(argv, **kwargs)
                self.events = result.stdout or ""
                return result
            except subprocess.TimeoutExpired as exc:
                self.timeout = True
                raw = exc.stdout or ""
                self.events = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                raise
        options: dict[str, Any] = {"runner": capture, "config": settings, "prices": prices}
        if clock is not None:
            options["clock"] = clock
        self.backend = CodexCLIBackend(**options)
        self.backend.pricing_ref = pricing_ref

    def usage(self) -> Usage:
        return self.backend.usage()

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        if self.invoked:
            raise BackendError("second provider invocation refused")
        self.invoked = True
        try:
            return self.backend.generate(schema, messages)
        finally:
            try:
                models = native_models(self.events)
            except (ValueError, TypeError):
                models = []
            self.model = next((model for model in models if model != MODEL),
                              MODEL if models else None)
            if self.model != MODEL:
                # A deadline without identity is a timeout, not evidence of substitution.
                if not self.timeout or self.model is not None:
                    raise PinMismatch("native model identity missing, malformed or mismatched")
