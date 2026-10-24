"""Mechanically validate executor ledgers without trusting their validation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError

from verifier.python_identity import identifier_found
from verifier.schema import validate
from verifier.v3_io import (
    atomic, confined, digest, encoded, locked, reference, requirements,
    session_root, supplied_file,
)


class InvalidLedger(ValueError):
    """Invalid ledger input; an advisory, never a bookkeeping retry."""


def validate_ledger(ledger_file: Path, workspace: Path, session_id: str, artifacts: Path) -> dict[str, Any]:
    try:
        root = session_root(workspace, artifacts, session_id)
        if supplied_file(root, ledger_file) != root / "ledger.json":
            raise InvalidLedger("ledger must be the session ledger.json")
        with locked(root):
            return _validate(root, workspace.resolve(), session_id)
    except (ValueError, ValidationError, FileNotFoundError) as exc:
        raise InvalidLedger(str(exc)) from exc


def _validate(root: Path, workspace: Path, session_id: str) -> dict[str, Any]:
    path = confined(root, "ledger.json")
    ledger = json.loads(path.read_bytes())
    validate(ledger, "ledger.schema.json")
    table, req_ref = requirements(root, session_id)
    if ledger["session_id"] != session_id or ledger["requirements"] != req_ref:
        raise InvalidLedger("ledger session/requirements identity mismatch")
    reference(root, ledger["requirements"])
    ids = [d["id"] for d in ledger["decisions"]]
    if len(set(ids)) != len(ids):
        raise InvalidLedger("duplicate decision ID")
    requirement_ids = {r["id"] for r in table["requirements"]}
    if any(o["requirement_id"] is not None and o["requirement_id"] not in requirement_ids for o in ledger["open_items"]):
        raise InvalidLedger("unknown open-item requirement ID")
    old = ledger["validation"]
    expected = [(d["id"], f["kind"], f["value"], f["path"]) for d in ledger["decisions"] for f in d["fixes"]]
    if len(set(expected)) != len(expected):
        raise InvalidLedger("duplicate fixed identifier")
    problems: list[str] = []
    old_files: dict[str, str] = {}
    if old is not None:
        if old["status"] != "valid":
            problems.append("previously invalid ledger requires a fresh executor-written ledger, not repeated validation")
        coverage = [(i["decision_id"], i["kind"], i["value"], i["path"]) for i in old["identifiers"]]
        old_files = {f["path"]: f["sha256"] for f in old["files"]}
        if (sorted(coverage) != sorted(expected) or len(old_files) != len(old["files"])
                or set(old_files) != {e[3] for e in expected}):
            problems.append("previous validation does not cover exactly the ledger identifiers/files")
    identifiers: list[dict[str, Any]] = []
    files: dict[str, str] = {}
    for decision_id, kind, value, relative in expected:
        found, sha = False, None
        try:
            target = confined(workspace, relative)
            source = target.read_bytes()
            sha = digest(source)
            files[relative] = sha
            if target.suffix != ".py":
                raise ValueError("only Python identifier extraction is supported")
            found = identifier_found(source, kind, value)
            if old is not None:
                matching = [i for i in old["identifiers"] if (i["decision_id"], i["kind"], i["value"], i["path"]) == (decision_id, kind, value, relative)]
                if old_files.get(relative) != sha or len(matching) != 1 or matching[0]["sha256"] != sha:
                    problems.append(f"stale workspace hash: {relative}")
            if not found:
                problems.append(f"missing or mismatched {kind}: {value} in {relative}")
        except (OSError, ValueError, SyntaxError, UnicodeError, RuntimeError) as exc:
            problems.append(f"unsupported or missing identifier {value}: {exc}")
        identifiers.append({"decision_id": decision_id, "kind": kind, "value": value,
                            "path": relative, "found": found, "sha256": sha})
    # Read again to detect changes during extraction before saving/injection.
    for relative, sha in files.items():
        if digest(confined(workspace, relative).read_bytes()) != sha:
            problems.append(f"workspace changed during ledger validation: {relative}")
    ledger["validation"] = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "invalid" if problems else "valid",
        "reason": "; ".join(problems) if problems else "all listed Python identities found; current file hashes recorded",
        "identifiers": identifiers, "files": [{"path": p, "sha256": h} for p, h in sorted(files.items())],
    }
    validate(ledger, "ledger.schema.json")
    data = encoded(ledger)
    atomic(path, data)
    if not problems:
        latest = confined(workspace, ".localharness/v3/latest-ledger.json")
        with locked(latest.parent):
            atomic(latest, data)
    return ledger
