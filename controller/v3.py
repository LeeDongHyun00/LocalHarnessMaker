"""Hook-facing v3 artifacts, pin gate, one-shot calls and atomic publication."""

import fcntl
import json
import logging
import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from controller.analyze import Prices, calculate_cost
from controller.backends.base import Message, Usage
from controller.errors import BackendError, InputError
from controller.generation import read_text, schema_validator, validate_input
from controller.settings import PACKAGE_DIR, load_object
from controller.v3_checks import confined, derive_check, digest, source_clause
from controller.v3_client import MODEL, IdentityUnobserved, PinMismatch, PinnedLunaClient, call_error
from controller.v3_wire import CLAIMS, REQUIREMENTS, validate_requirements_output

logger = logging.getLogger(__name__)
ClientFactory = Callable[[Prices, str], Any]


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    """Flush complete JSON before replacing the destination in the same directory."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=".controller-", delete=False) as output:
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
        temporary = Path(output.name)
    temporary.replace(path)


def retain(root: Path, name: str, data: bytes) -> dict[str, str]:
    path = confined(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError:
        if path.read_bytes() != data:
            raise InputError("immutable evidence already exists with different bytes")
    return {"path": name, "sha256": digest(data)}


def artifact_root(directory: Path, session_id: str) -> tuple[Path, Path]:
    if not session_id:
        raise InputError("session ID must be nonempty")
    directory = directory.absolute()
    key = digest(session_id.encode("utf-8"))
    if (directory.name != key or directory.parent.name != "sessions"
            or directory.parent.parent.name != "v3"
            or directory.parent.parent.parent.name != ".localharness"):
        raise InputError("--artifacts must be .localharness/v3/sessions/<sha256(session-id)>")
    workspace = directory.parents[3]
    try:
        confined(workspace, directory.relative_to(workspace).as_posix(), directory=True)
    except ValueError as exc:
        raise InputError("artifact directory escapes workspace") from exc
    directory.mkdir(parents=True, exist_ok=True)
    return directory, workspace


def _pin(directory: Path, session_id: str) -> tuple[dict[str, Any], Prices, str]:
    pin = load_object(confined(directory, "pin-check.json"))
    validate_input(pin, "pin-check.schema.json")
    if pin["session_id"] != session_id or pin["status"] != "enabled":
        raise BackendError("Luna pin is disabled or belongs to another session")
    retained: dict[str, bytes] = {}
    for field in ("model_list", "pricing_snapshot"):
        reference = pin[field]
        data = confined(directory, reference["path"]).read_bytes()
        if digest(data) != reference["sha256"]:
            raise BackendError("pin evidence hash mismatch")
        retained[field] = data
    if not re.search(rb'(?<![a-zA-Z0-9_.-])gpt-6-luna(?![a-zA-Z0-9_.-])', retained["model_list"]):
        raise BackendError("exact pinned model absent from model-list evidence")
    book = json.loads(retained["pricing_snapshot"])
    if book != load_object(PACKAGE_DIR / "prices.yaml"):
        raise BackendError("pin pricing snapshot differs from controller's pinned snapshot")
    return pin, Prices.from_dict(book["models"][MODEL]), pin["pricing_ref"]


def _disable_pin(directory: Path, *, unobserved: bool = False) -> None:
    pin = load_object(directory / "pin-check.json")
    pin["status"] = "disabled"
    reason = "model_list_unavailable" if unobserved else "model_identity_mismatch"
    if reason not in pin["reason_codes"]:
        pin["reason_codes"].append(reason)
    pin["advisory"] = "Luna hooks disabled: native provider model identity could not be verified against gpt-6-luna."
    validate_input(pin, "pin-check.schema.json")
    atomic_json(directory / "pin-check.json", pin)


def _audit_validator() -> Draft202012Validator:
    validator = schema_validator("completion-report.schema.json")
    return validator.evolve(schema=validator.schema["properties"]["claim_audit"])


def _call_ref(call_id: str) -> dict[str, str]:
    return {"path": "luna-calls.jsonl", "call_id": call_id}


def _record(directory: Path, record: dict[str, Any]) -> None:
    validate_input(record, "luna-call.schema.json")
    path = confined(directory, "luna-calls.jsonl")
    data = (json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    # The session lock covers both phases and each complete JSONL append.
    with path.open("ab") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def _requirements(value: dict[str, Any], prompt: str, workspace: Path,
                  config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validate_requirements_output(value)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for number, row in enumerate(value["requirements"], 1):
        if row["source_excerpt"] not in prompt:
            raise BackendError("Luna source excerpt is not verbatim request text")
        key = (row["kind"], row["source_excerpt"], row["text"])
        if key in seen:
            raise BackendError("duplicate requirements row")
        seen.add(key)
        rows.append({"id": f"R-{number}", "number": number, **row,
                     "check": derive_check(row["kind"], row["source_excerpt"], prompt, workspace, config)})
    questions: list[dict[str, Any]] = []
    for number, question in enumerate(value["open_questions"], 1):
        if any(index > len(rows) for index in question["requirement_numbers"]):
            raise BackendError("question references nonexistent requirement")
        if question["text"] in {q["text"] for q in questions}:
            raise BackendError("duplicate open question")
        questions.append({"id": f"Q-{number}", "text": question["text"],
                          "requirement_ids": [f"R-{i}" for i in question["requirement_numbers"]],
                          "answer": None})
    return rows, questions


def _citation(citation: str, final: str, directory: Path) -> dict[str, str] | None:
    """Only final-message-named session evidence; compute hashes from retained bytes."""
    if citation not in final:
        raise BackendError("citation excerpt is not verbatim final-message text")
    try:
        citation = source_clause(final, citation)
    except ValueError:
        return None
    paths = re.findall(r'`([^`\n]+)`|\]\(([^)\n]+)\)', citation)
    names = [first or second for first, second in paths]
    if not names:
        names = re.findall(r'(?<![\w/])evidence/[^\s`<>()[\],;]+', citation)
    names = list(dict.fromkeys(names))
    if len(names) != 1:
        return None
    try:
        name = names[0].rstrip(".")
        path = confined(directory, name)
        if not name.startswith("evidence/"):
            return None
        data = path.read_bytes()
        actual = digest(data)
        cited_hashes = re.findall(r'\b[a-fA-F0-9]{64}\b', citation)
        if any(value.lower() != actual for value in cited_hashes):
            return None
        text = data.decode("utf-8")
        if not text.strip():
            return None
        return {"kind": "file", "path": name, "sha256": actual, "excerpt": text[:2000]}
    except (ValueError, OSError, UnicodeError):
        return None


def _claims(value: dict[str, Any], requirements: dict[str, Any], final: str,
            directory: Path) -> list[dict[str, Any]]:
    ids = {row["id"] for row in requirements["requirements"]}
    result: list[dict[str, Any]] = []
    for claim in value["claims"]:
        if claim["requirement_id"] not in ids or claim["claim_excerpt"] not in final:
            raise BackendError("claim ID or final-message excerpt is invalid")
        evidence: list[dict[str, str]] = []
        invalid = False
        for citation in claim["citations"]:
            verified = _citation(citation["citation_excerpt"], final, directory)
            if verified is None:
                invalid = True
            else:
                evidence.append(verified)
        assessment = claim["assessment"]
        if invalid:
            assessment = "unsupported"
        elif not evidence and assessment == "supported":
            assessment = "unverifiable"
        result.append({"requirement_id": claim["requirement_id"],
                       "claim_excerpt": claim["claim_excerpt"],
                       "cited_evidence": evidence, "assessment": assessment})
    return result


def validate_requirements(value: dict[str, Any], directory: Path, session_id: str) -> None:
    validate_input(value, "requirements.schema.json")
    if value["session_id"] != session_id:
        raise InputError("requirements session ID mismatch")
    prompt = confined(directory, value["prompt"]["path"]).read_bytes()
    if digest(prompt) != value["prompt"]["sha256"]:
        raise InputError("requirements prompt hash mismatch")
    text = prompt.decode("utf-8")
    for number, row in enumerate(value["requirements"], 1):
        if row["number"] != number or row["id"] != f"R-{number}" or row["source_excerpt"] not in text:
            raise InputError("requirements IDs or source correspondence invalid")
    ids = {row["id"] for row in value["requirements"]}
    if (len({q["id"] for q in value["open_questions"]}) != len(value["open_questions"])
            or any(set(q["requirement_ids"]) - ids for q in value["open_questions"])):
        raise InputError("invalid requirements questions")
    if value["state"] in {"ready", "pending_questions"}:
        reference = value["luna_call"]
        calls = [json.loads(line) for line in read_text(directory / "luna-calls.jsonl").splitlines()]
        for call in calls:
            validate_input(call, "luna-call.schema.json")
        matches = [call for call in calls if call["call_id"] == reference["call_id"]]
        if (len(matches) != 1 or matches[0]["status"] != "success"
                or matches[0]["phase"] != "requirements" or matches[0]["session_id"] != session_id):
            raise InputError("requirements accounting reference invalid")


def run_operation(phase: str, *, session_id: str, artifacts: Path,
                  prompt_path: Path | None = None, config_path: Path | None = None,
                  requirements_path: Path | None = None, final_path: Path | None = None,
                  client_factory: ClientFactory | None = None) -> tuple[Path, int]:
    """Publish one artifact; pin/call failure is exit 2 with an unavailable artifact."""
    directory, workspace = artifact_root(artifacts, session_id)
    if phase not in {"requirements", "claim_audit"}:
        raise InputError("unknown controller hook phase")
    output = confined(directory, "requirements.json" if phase == "requirements" else "claim-audit.json")
    lock_path = confined(directory, ".controller.lock")
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _run_locked(phase, session_id, directory, workspace, output, prompt_path,
                           config_path, requirements_path, final_path, client_factory or PinnedLunaClient)


def _run_locked(phase: str, session_id: str, directory: Path, workspace: Path, output: Path,
                prompt_path: Path | None, config_path: Path | None,
                requirements_path: Path | None, final_path: Path | None,
                client_factory: ClientFactory) -> tuple[Path, int]:
    config = load_object(config_path) if config_path is not None else {}
    if phase == "requirements":
        if prompt_path is None:
            raise InputError("prompt is required")
        data = prompt_path.read_bytes()
        text = data.decode("utf-8")
        if not text.strip():
            raise InputError("prompt must be nonempty UTF-8 text")
        snapshot = retain(directory, "evidence/request.txt", data)
        artifact: dict[str, Any] = {"schema_version": 3, "session_id": session_id,
                                    "prompt": snapshot, "state": "unavailable",
                                    "requirements": [], "open_questions": [], "luna_call": None}
        wire = REQUIREMENTS
        inputs: dict[str, Any] = {"request": text}
    else:
        if requirements_path is None or requirements_path.resolve() != (directory / "requirements.json").resolve():
            raise InputError("requirements must be this session's requirements.json")
        requirements = load_object(requirements_path)
        validate_requirements(requirements, directory, session_id)
        try:
            text = read_text(final_path) if final_path is not None else ""
        except InputError:
            text = ""
        if output.exists():
            previous = load_object(output)
            if not _audit_validator().is_valid(previous):
                raise InputError("existing claim audit is invalid")
            original = previous["audited_final_message"]
            if original is not None and original["sha256"] != digest(text.encode("utf-8")):
                previous.update(status="stale", reason="final message changed after the original audit; no second call")
                atomic_json(output, previous)
            return output, 2 if previous["status"] == "unavailable" else 0
        snapshot = retain(directory, "evidence/audited-final.txt", text.encode("utf-8")) if text.strip() else None
        artifact = {"status": "unavailable", "audited_final_message": snapshot,
                    "claims": [], "reason": ("final message unavailable; audit not invoked" if not text.strip()
                                             else "claim audit not available"), "luna_call": None}
        wire = CLAIMS
        inputs = {"requirements": requirements["requirements"], "final_message": text}
    if output.exists():
        previous = load_object(output)
        if phase == "requirements":
            validate_requirements(previous, directory, session_id)
            return output, 2 if previous["state"] == "unavailable" else 0
        if not _audit_validator().is_valid(previous):
            raise InputError("existing claim audit is invalid")
        return output, 2 if previous["status"] == "unavailable" else 0
    call_id = f"{phase}-1"
    try:
        _, prices, pricing_ref = _pin(directory, session_id)
        if phase == "claim_audit" and (not text.strip() or requirements["state"] == "unavailable"):
            raise BackendError("final message or requirements unavailable")
        allocation = confined(directory, f"evidence/{phase}-allocation.json")
        allocation.parent.mkdir(parents=True, exist_ok=True)
        if (directory / "luna-calls.jsonl").exists():
            for line in read_text(directory / "luna-calls.jsonl").splitlines():
                record = json.loads(line)
                validate_input(record, "luna-call.schema.json")
                if (record["session_id"] != session_id or record["phase"] == phase
                        or record["status"] == "pin_mismatch"
                        or (record["error"] or "").startswith("identity_unobserved")):
                    raise BackendError("phase already invoked, pin mismatched or accounting identity invalid")
        # Reserve before construction/provider invocation; never retry after interruption.
        try:
            with allocation.open("x", encoding="utf-8") as marker:
                json.dump({"call_id": call_id, "session_id": session_id}, marker)
        except FileExistsError as exc:
            raise BackendError("phase allocation already consumed; refusing another provider invocation") from exc
        client = client_factory(prices, pricing_ref)
        record = {"schema_version": 3, "session_id": session_id, "call_id": call_id,
                  "phase": phase, "backend": "codex_cli", "requested_model": MODEL,
                  "model": None, "reasoning_effort": "low", "status": "error",
                  "error": "call did not complete", "input_tokens": None,
                  "cached_input_tokens": None, "output_tokens": None, "latency_seconds": 0.0,
                  "usd": None, "pricing_ref": pricing_ref, "cost_basis": "api_equivalent_usd"}
        try:
            messages: list[Message] = [
                {"role": "system", "content": read_text(PACKAGE_DIR / "prompts" / (
                    "requirements-v1.md" if phase == "requirements" else "claim-audit-v1.md"))},
                {"role": "user", "content": json.dumps(inputs, ensure_ascii=False)},
            ]
            value = client.generate(wire, messages)
            if client.model is None:
                raise IdentityUnobserved("identity_unobserved")
            if client.model != MODEL:
                raise PinMismatch("native provider identity does not match requested model")
            if not Draft202012Validator(wire).is_valid(value):
                raise BackendError("Luna output failed private schema validation")
            if phase == "requirements":
                rows, questions = _requirements(value, text, workspace, config)
                artifact.update(requirements=rows, open_questions=questions,
                                state="pending_questions" if questions else "ready")
            else:
                artifact.update(status="complete", claims=_claims(value, requirements, text, directory), reason=None)
            artifact["luna_call"] = _call_ref(call_id)
            if phase == "requirements":
                validate_input(artifact, "requirements.schema.json")
            elif not _audit_validator().is_valid(artifact):
                raise BackendError("claim audit failed published schema validation")
            record.update(status="success", error=None)
        except Exception as exc:
            mismatch = isinstance(exc, PinMismatch)
            record.update(status="pin_mismatch" if mismatch else "error" if isinstance(exc, IdentityUnobserved)
                          else "timeout" if getattr(client, "timeout", False) else "error",
                          error=getattr(client, "error", None) or call_error(exc))
            if phase == "requirements":
                artifact.update(state="unavailable", requirements=[], open_questions=[])
            else:
                artifact.update(status="unavailable", claims=[], reason=record["error"])
        finally:
            usage: Usage = client.usage()
            record.update(model=client.model, input_tokens=usage.input_tokens,
                          cached_input_tokens=usage.cached_input_tokens, output_tokens=usage.output_tokens,
                          latency_seconds=usage.latency_seconds)
            if None not in (usage.input_tokens, usage.cached_input_tokens, usage.output_tokens):
                record["usd"] = calculate_cost(usage.input_tokens, usage.output_tokens, prices, usage.cached_input_tokens)
            events = getattr(client, "events", "")
            _record(directory, record)
            if record["status"] == "pin_mismatch":
                _disable_pin(directory)
            elif record["error"] and record["error"].startswith("identity_unobserved"):
                _disable_pin(directory, unobserved=True)
            if events:
                retain(directory, f"evidence/{phase}-native.jsonl", events.encode("utf-8"))
            native = getattr(client, "native_events", "")
            if native:
                retain(directory, f"evidence/{phase}-rollout.jsonl", native.encode("utf-8"))
        artifact["luna_call"] = _call_ref(call_id)
        if record["status"] != "success":
            logger.error("controller_hook_unavailable %s", record["error"])
    except (BackendError, InputError, OSError, ValueError, KeyError) as exc:
        logger.error("controller_hook_unavailable Luna pin/call unavailable; inspect pin-check.json and accounting (%s)", type(exc).__name__)
        if phase == "requirements":
            artifact.update(state="unavailable", requirements=[], open_questions=[])
        else:
            reason = artifact["reason"]
            artifact.update(status="unavailable", claims=[], reason=(reason if reason != "claim audit not available"
                else "Luna pin/call unavailable; inspect pin-check.json and accounting"))
    if phase == "requirements":
        validate_input(artifact, "requirements.schema.json")
    elif not _audit_validator().is_valid(artifact):
        raise BackendError("claim audit failed published schema validation")
    atomic_json(output, artifact)
    return output, 2 if artifact.get("state", artifact.get("status")) == "unavailable" else 0


def record_answers(*, artifacts: Path, session_id: str, answers: dict[str, str]) -> Path:
    """Record supplied visible answers without inference or another model call.

    The hook must obtain these strings from actual user answers, not executor
    guesses. This helper cannot attest to the origin of an arbitrary caller.
    """
    directory, _ = artifact_root(artifacts, session_id)
    with confined(directory, ".controller.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = directory / "requirements.json"
        value = load_object(path)
        validate_requirements(value, directory, session_id)
        ids = {question["id"] for question in value["open_questions"]}
        if (value["state"] == "unavailable" or set(answers) - ids
                or any(not isinstance(answer, str) or not answer.strip() for answer in answers.values())):
            raise InputError("answers must be visible nonempty user responses for existing question IDs")
        for question in value["open_questions"]:
            if question["id"] in answers:
                question["answer"] = answers[question["id"]]
        value["state"] = "pending_questions" if any(q["answer"] is None for q in value["open_questions"]) else "ready"
        validate_input(value, "requirements.schema.json")
        atomic_json(path, value)
        return path
