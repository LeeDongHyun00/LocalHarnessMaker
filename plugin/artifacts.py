"""Confined, atomic v3 artifacts and nonblocking native-session serialization."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def confined(root: Path, relative: str) -> Path:
    """Reject aliases through symlinks, including aliases still inside the root."""
    path = Path(relative)
    if path.is_absolute() or not path.parts or '..' in path.parts:
        raise ValueError('artifact path must be confined and relative')
    target = root / path
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f'symlink artifact path: {relative}')
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('artifact path escapes root')
    return target


def session_directory(workspace: Path, session_id: str) -> Path:
    if not isinstance(session_id, str) or not session_id:
        raise ValueError('native session ID required')
    path = confined(workspace, f'.localharness/v3/sessions/{digest(session_id.encode())}')
    path.mkdir(parents=True, exist_ok=True)
    confined(path, 'evidence').mkdir(exist_ok=True)
    return path


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('expected JSON object')
    return value


def atomic_bytes(path: Path, data: bytes) -> None:
    confined(path.parent, path.name)
    temporary = path.with_name(f'.{path.name}.{uuid4().hex}.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write(path: Path, value: dict[str, Any]) -> None:
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def snapshot(directory: Path, name: str, data: bytes) -> dict[str, str]:
    path = confined(directory, f'evidence/{name}')
    # A retry/event must never overwrite evidence from an earlier invocation.
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('immutable evidence collision')
    else:
        with path.open('xb') as stream:
            stream.write(data)
    return {'path': str(path.relative_to(directory)), 'sha256': digest(data)}


def validate(value: dict[str, Any], schema: str) -> None:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
    registry = Registry().with_resources(
        (p.name, Resource.from_contents(json.loads(p.read_text())))
        for p in (ROOT / 'schemas').glob('*.schema.json'))
    Draft202012Validator(read(ROOT / 'schemas' / schema), registry=registry,
                         format_checker=FormatChecker()).validate(value)


def verify_reference(directory: Path, reference: dict[str, str]) -> Path:
    path = confined(directory, reference['path'])
    if digest(path.read_bytes()) != reference['sha256']:
        raise ValueError('artifact hash mismatch')
    return path


@contextmanager
def locked(directory: Path) -> Iterator[None]:
    with confined(directory, 'hook.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def workspace_hash(workspace: Path) -> str:
    """Hash pre-edit file contents/paths; ignore only Git and hook-owned state."""
    rows: list[tuple[str, str]] = []
    for base, directories, files in os.walk(workspace, followlinks=False):
        parent = Path(base)
        directories[:] = sorted(d for d in directories if
                                not (parent == workspace and d in {'.git', '.localharness'}))
        for name in sorted([*files, *(d for d in directories if (parent / d).is_symlink())]):
            path = parent / name
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            rows.append((str(path.relative_to(workspace)), digest(data)))
    return digest(json.dumps(rows, separators=(',', ':')).encode())
