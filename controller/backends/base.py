"""The shared backend interface; no verifier dependency."""

import hashlib
import json
import logging
import math
import os
from dataclasses import dataclass
from typing import Any, Protocol

from controller.analyze import Prices
from controller.errors import InputError
from controller.settings import PACKAGE_DIR, load_object

Message = dict[str, str]


def control_timeout(config: dict[str, Any]) -> float:
    """Snapshot the cloud deadline at construction without changing configuration."""
    override = os.environ.get("HARNESS_CONTROL_TIMEOUT_SECONDS")
    try:
        timeout = float(override if override is not None else config["timeout_seconds"])
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Deadline must be finite and positive")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise InputError(
            "HARNESS_CONTROL_TIMEOUT_SECONDS or timeout_seconds must be a finite positive number"
        ) from exc
    return timeout


def log_control_timeout(logger: logging.Logger, backend: str, model: str, seconds: float) -> None:
    """Retain a timeout diagnosis even if routing later reports a fallback error."""
    logger.error("control_failure %s", json.dumps({
        "backend": backend, "model": model, "reason": "deadline",
        "timeout_seconds": seconds,
    }, sort_keys=True))


@dataclass(frozen=True)
class Usage:
    """Usage of the last call; None means the service supplied no accounting."""

    input_tokens: int | None
    output_tokens: int | None
    usd: float | None
    latency_seconds: float
    cached_input_tokens: int | None = None


class Backend(Protocol):
    """Backends perform one call; generators own bounded regeneration."""

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        """Return a validated object or raise a controller backend error."""
        ...

    def usage(self) -> Usage:
        """Return accounting for the most recent call."""
        ...


def configured_prices(config: dict[str, Any], override: Prices | None = None) -> tuple[Prices | None, str | None]:
    """Pin a price snapshot; custom or unavailable prices have no false reference."""
    if override is not None:
        return override, None
    snapshot = PACKAGE_DIR / "prices.yaml"
    book = load_object(snapshot)
    key = config.get("price_key")
    if key not in book["models"]:
        return None, None
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    return Prices.from_dict(book["models"][key]), (
        f"controller/prices.yaml@{book['checked_on']}#{key}:sha256:{digest}"
    )
