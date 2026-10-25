"""Version selection for hook prompts and independent calibration."""

import os

from controller.errors import InputError
from controller.generation import read_text
from controller.settings import PACKAGE_DIR

PROMPT_VERSION_ENV = "HARNESS_LUNA_PROMPT_VERSION"
DEFAULT_PROMPT_VERSION = "v2"
PROMPT_VERSIONS = ("v1", "v2")


def select_prompt(phase: str, version: str | None = None) -> tuple[str, str]:
    """Resolve an explicit version, then the environment, then the v2 default."""
    selected = version if version is not None else os.environ.get(PROMPT_VERSION_ENV, DEFAULT_PROMPT_VERSION)
    if selected not in PROMPT_VERSIONS:
        raise InputError(f"{PROMPT_VERSION_ENV} must be v1 or v2")
    if phase not in {"requirements", "claim_audit"}:
        raise InputError("unknown controller hook prompt phase")
    path = PACKAGE_DIR / "prompts" / f"{phase.replace('_', '-')}-{selected}.md"
    return selected, read_text(path)
