"""The shared backend interface; no verifier dependency."""

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

from controller.analyze import Prices
from controller.settings import PACKAGE_DIR, load_object

Message = dict[str, str]


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
