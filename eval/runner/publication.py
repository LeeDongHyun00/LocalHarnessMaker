"""Use checkout-relative references in published evaluation evidence."""

from pathlib import Path
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eval.runner.audit import PrivateGraders


def review_bytes(data: bytes, private: "PrivateGraders") -> bytes:
    """Apply the same text decoding, newline conversion and redaction everywhere."""
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    return checkout_text(private.redact(text)).encode("utf-8")


def safe_source(path: Path, root: Path) -> bool:
    """Reject traversal and symlinks at/below root, allowing system aliases above it."""
    return (path.is_relative_to(root) and ".." not in path.relative_to(root).parts and
            not any(p.is_symlink() for p in (path, *path.parents)
                    if p == root or p.is_relative_to(root)))


def control_target(source: Path, runtime: Path, out: Path) -> Path | None:
    """Apply the runner's control-evidence allowlist and destination layout."""
    if not safe_source(source, runtime) or "workspace" in source.relative_to(runtime).parts:
        return None
    name = source.name
    if not (name in {"contract.json", "handoff.json", "recovery.json"} or
            re.fullmatch(r"verdict-[0-9]+\.json", name) or name.endswith(".control.json") or
            re.fullmatch(r"(?:contract|verdict-[0-9]+|handoff|handoff-validation)\.std(?:out|err)", name)):
        return None
    if source.is_relative_to(runtime / "control-interruptions"):
        return out / source.relative_to(runtime)
    return out / (source.parent.name + "-" + name if source.parent != runtime else name)


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
