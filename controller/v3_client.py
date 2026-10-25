"""One-shot pinned Luna transport, isolated from historical routing and retries."""

import json
import logging
import os
import subprocess
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from controller.analyze import Prices
from controller.backends.base import Message, Usage
from controller.backends.codex_cli import CodexCLIBackend, Runner, _read_usage
from controller.errors import BackendError
from controller.settings import PACKAGE_DIR, load_object
from controller.v3_native import native_models, records, rollout, usage_event

MODEL = "gpt-6-luna"
logger = logging.getLogger(__name__)


class PinMismatch(BackendError):
    """A native record explicitly names a model different from the pin."""


class IdentityUnobserved(BackendError):
    """No usable native record names the served model."""


def call_error(exc: Exception, diagnostic: str | None = None) -> str:
    """Bound diagnostics for public accounting without losing identity classification."""
    if isinstance(exc, IdentityUnobserved):
        return (f"identity_unobserved\n{diagnostic}" if diagnostic else "identity_unobserved")[:2000]
    return (diagnostic or str(exc))[:2000]


class PinnedLunaClient:
    """One provider invocation per instance, including failure; no automatic fallback."""

    def __init__(self, prices: Prices, pricing_ref: str, *, runner: Runner = subprocess.run,
                 config: dict[str, Any] | None = None,
                 clock: Callable[[], float] | None = None) -> None:
        settings = dict(config or load_object(PACKAGE_DIR / "config.yaml")["codex_cli"])
        if settings.get("model") != MODEL or settings.get("reasoning_effort") != "low":
            raise PinMismatch("requested model/effort violates the pin")
        self.events = ""
        self.native_events = ""
        self.model: str | None = None
        self.error: str | None = None
        self.invoked = False
        self.timeout = False
        self.codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        self._usage = Usage(None, None, None, 0.0)

        def capture(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            self.codex_home = Path(kwargs["env"].get("CODEX_HOME") or Path.home() / ".codex")
            try:
                result = runner(argv, **kwargs)
                self.events = result.stdout or ""
                return result
            except subprocess.TimeoutExpired as exc:
                self.timeout = True
                raw = exc.stdout or ""
                self.events = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                raise
        options: dict[str, Any] = {"runner": capture, "config": settings, "prices": prices,
                                   "persist_session": True, "log_calls": False}
        if clock is not None:
            options["clock"] = clock
        self.backend = CodexCLIBackend(**options)
        self.backend.pricing_ref = pricing_ref

    def usage(self) -> Usage:
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        if self.invoked:
            raise BackendError("second provider invocation refused")
        self.invoked = True
        value: dict[str, Any] = {}
        failure: Exception | None = None
        try:
            value = self.backend.generate(schema, messages)
        except Exception as exc:
            failure = exc
        self._usage = self.backend.usage()
        try:
            self.native_events = rollout(self.events, self.codex_home)
            models = native_models(self.events) + native_models(self.native_events)
            # A new exec has no earlier process totals. Prefer completed-turn
            # counters; recover native totals only when that transport record is absent.
            if not any(e.get("type") == "turn.completed" for e in records(self.events)):
                recovered = _read_usage(usage_event(self.native_events), self.backend.prices)
                self._usage = Usage(recovered.input_tokens, recovered.output_tokens, recovered.usd,
                                    self._usage.latency_seconds, recovered.cached_input_tokens)
        except (OSError, ValueError, TypeError):
            models = []
        self.model = next((model for model in models if model != MODEL), MODEL if models else None)
        if self.model is not None and self.model != MODEL:
            failure = PinMismatch("native model pin mismatch")
        elif self.model is None:
            failure = IdentityUnobserved("identity_unobserved")
        status = ("success" if failure is None else "pin_mismatch" if isinstance(failure, PinMismatch)
                  else "error" if isinstance(failure, IdentityUnobserved)
                  else "timeout" if self.timeout else "error")
        self.error = call_error(failure, self.backend.error) if failure else None
        logger.info("control_call %s", json.dumps({
            "backend": "codex_cli", "requested_model": MODEL, "model": self.model,
            "executable": self.backend.executable,
            "timeout_seconds": self.backend.timeout, "reasoning_effort": "low", "status": status,
            "error": self.error, "pricing_ref": self.backend.pricing_ref, **asdict(self._usage),
        }, sort_keys=True))
        if failure is not None:
            raise failure
        return value
