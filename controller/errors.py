"""Controller errors shared by the library and CLI."""


class InputError(ValueError):
    """The caller supplied invalid input or configuration."""


class BackendError(RuntimeError):
    """The remote service could not complete a generation."""


class InvalidGeneration(BackendError):
    """A completed generation was not valid JSON matching the schema."""


class TransportError(BackendError):
    """CLI transport unavailable; the approved HTTP fallback may be used."""
