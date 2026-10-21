"""The shared backend interface; no verifier dependency."""

from dataclasses import dataclass
from typing import Any, Protocol

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
