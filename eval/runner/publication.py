"""Use checkout-relative references in published evaluation evidence."""

from pathlib import Path
import re


def checkout_text(text: str) -> str:
    """Remove this checkout's absolute prefix, including paths inside log strings."""
    from eval.runner.core import REPOSITORY

    root = str(REPOSITORY)
    text = text.replace(root + "/", "")
    return re.sub(re.escape(root) + r"(?=$|[\s\"'])", ".", text)


def evidence_path(value: str) -> Path:
    """Resolve report references independently of the caller's working directory."""
    from eval.runner.core import REPOSITORY

    path = Path(value)
    return path if path.is_absolute() else REPOSITORY / path
