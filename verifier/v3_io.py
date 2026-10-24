"""Confined v3 artifacts, immutable snapshots and offline provenance checks."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import tempfile
import time
from typing import Any, Iterator

from verifier.schema import validate


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def confined(root: Path, relative: str) -> Path:
    path, windows = Path(relative), PureWindowsPath(relative)
    if (not relative or "\x00" in relative or path.is_absolute() or windows.drive
            or windows.root or ".." in path.parts or ".." in windows.parts):
        raise ValueError(f"unconfined path: {relative!r}")
    candidate = root / path
    # Reject symlinks even when they currently point inside: artifacts must not
    # be redirectable aliases and workspace targets must have stable identity.
    cursor = root
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symlink path rejected: {relative!r}")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {relative!r}")
    return candidate


def session_root(workspace: Path, artifacts: Path, session_id: str) -> Path:
    if not session_id or not workspace.is_dir():
        raise ValueError("native session ID and existing workspace required")
    workspace = workspace.resolve()
    expected = confined(workspace, f".localharness/v3/sessions/{digest(session_id.encode())}")
    # Inspect the supplied spelling too, before resolving away aliases.
    supplied = artifacts.absolute()
    if not supplied.is_relative_to(workspace):
        raise ValueError("artifacts must be inside the workspace")
    confined(workspace, str(supplied.relative_to(workspace)))
    if supplied != expected:
        raise ValueError("artifacts directory does not match native session ID")
    expected.mkdir(parents=True, exist_ok=True)
    return expected


def supplied_file(root: Path, path: Path) -> Path:
    absolute = path.absolute()
    if not absolute.is_relative_to(root):
        raise ValueError("input artifact is outside session directory")
    return confined(root, str(absolute.relative_to(root)))


def atomic(path: Path, data: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".verifier-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(root: Path) -> Iterator[None]:
    # Lock the directory itself, leaving no extra mutable protocol artifact.
    descriptor = os.open(root, os.O_RDONLY)
    try:
        deadline = time.monotonic() + 5.0
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("verifier artifact lock unavailable after five seconds")
                time.sleep(0.01)
        yield
    finally:
        os.close(descriptor)


def snapshot(root: Path, label: str, data: bytes, kind: str = "file") -> dict[str, str]:
    relative = f"evidence/{label}-{digest(data)}.bin"
    path = confined(root, relative)
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("immutable evidence was changed")
    else:
        with path.open("xb") as stream:
            stream.write(data)
    return {"kind": kind, "path": relative, "sha256": digest(data),
            "excerpt": data.decode("utf-8", errors="replace")[:2000] or "(empty)"}


def reference(root: Path, value: dict[str, Any]) -> bytes:
    data = confined(root, value["path"]).read_bytes()
    if digest(data) != value["sha256"]:
        raise ValueError(f"artifact hash mismatch: {value['path']}")
    return data


def call_records(root: Path, session_id: str) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in confined(root, "luna-calls.jsonl").read_text().splitlines()]
    ids: set[str] = set()
    phases: set[str] = set()
    if len(records) > 2:
        raise ValueError("more than two Luna calls")
    for call in records:
        validate(call, "luna-call.schema.json")
        if call["session_id"] != session_id or call["call_id"] in ids or call["phase"] in phases:
            raise ValueError("duplicate or foreign Luna accounting")
        if call["model"] not in {None, "gpt-6-luna"} and call["status"] != "pin_mismatch":
            raise ValueError("provider identity mismatch")
        cached, total = call["cached_input_tokens"], call["input_tokens"]
        if cached is not None and total is not None and cached > total:
            raise ValueError("cached tokens exceed input tokens")
        ids.add(call["call_id"])
        phases.add(call["phase"])
    return records


def check_call(root: Path, session_id: str, ref: dict[str, Any], phase: str) -> None:
    if ref["path"] != "luna-calls.jsonl":
        raise ValueError("unexpected call accounting path")
    matches = [c for c in call_records(root, session_id) if c["call_id"] == ref["call_id"]]
    if len(matches) != 1 or matches[0]["phase"] != phase or matches[0]["status"] != "success":
        raise ValueError("missing successful phase accounting reference")


def requirements(root: Path, session_id: str) -> tuple[dict[str, Any], dict[str, str]]:
    data = confined(root, "requirements.json").read_bytes()
    table = json.loads(data)
    validate(table, "requirements.schema.json")
    if table["session_id"] != session_id:
        raise ValueError("requirements session ID mismatch")
    prompt_bytes = reference(root, table["prompt"])
    prompt = prompt_bytes.decode("utf-8")
    # Controllers may retain the original JSON string or the plain prompt.
    try:
        decoded = json.loads(prompt)
        if isinstance(decoded, str):
            prompt = decoded
    except ValueError:
        pass
    ids: set[str] = set()
    for number, row in enumerate(table["requirements"], 1):
        if row["number"] != number or row["id"] != f"R-{number}" or row["source_excerpt"] not in prompt:
            raise ValueError("requirement numbering or prompt source mismatch")
        ids.add(row["id"])
    questions = table["open_questions"]
    if len({q["id"] for q in questions}) != len(questions):
        raise ValueError("duplicate question ID")
    if any(set(q["requirement_ids"]) - ids for q in questions):
        raise ValueError("unknown question requirement ID")
    if table["state"] != "unavailable":
        check_call(root, session_id, table["luna_call"], "requirements")
    return table, {"path": "requirements.json", "sha256": digest(data)}
