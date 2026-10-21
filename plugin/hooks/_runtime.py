"""Thin hook orchestration: state, approval routing, and controller/verifier CLIs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugin/skills/harness/SKILL.md"


def read_json(path: Path) -> dict[str, Any]:
    """Load an object rather than interpreting malformed state as defaults."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    """Write plugin-owned session metadata, never controller/verifier artifacts."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(path: Path, schema: str) -> dict[str, Any]:
    """Validate boundary artifacts without importing controller or verifier code."""
    value = read_json(path)
    Draft202012Validator(read_json(ROOT / "schemas" / schema)).validate(value)
    return value


class Runtime:
    """Keep all work behind the entry-point's exact nested-environment guard."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.workspace = Path(payload["cwd"]).resolve(strict=True)
        if not self.workspace.is_dir() or not isinstance(payload["session_id"], str):
            raise ValueError("invalid workspace or session id")
        self.directory = self.workspace / ".harness"
        self.directory.mkdir(exist_ok=True)
        self.state_path = self.directory / "state.json"
        self.session_path = self.directory / "session.json"
        self.cli_seconds = 0.0

    def initialize(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Reset new sessions; preserve state when the same session resumes/compacts."""
        if self.session_path.exists() and self.state_path.exists():
            session = read_json(self.session_path)
            if session["session_id"] == self.payload["session_id"]:
                return read_json(self.state_path), session
        state = {
            "attempt": 0,
            "contract_path": str(self.directory / "contract.json"),
            "verdict_path": str(self.directory / "verdict.json"),
            "handoff_path": str(self.directory / "handoff.json"),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        session = {"session_id": self.payload["session_id"], "phase": "idle"}
        self.save(state, session)
        return state, session

    def save(self, state: dict[str, Any], session: dict[str, Any]) -> None:
        write_json(self.state_path, state)
        write_json(self.session_path, session)

    def call(self, module: str, operation: str, args: list[str], output: Path) -> None:
        """Use unchanged CLI arguments, a copied child environment, and a deadline."""
        python = os.environ.get("HARNESS_PYTHON", sys.executable)
        if os.environ.get("HARNESS_STUB") == "1":
            command = [python, str(Path(__file__).with_name("_stub.py")), module, operation, *args]
        else:
            command = [python, "-m", module, operation, *args]
        child_env = {**os.environ, "HARNESS_NESTED": "1"}
        started = time.perf_counter()
        try:
            result = subprocess.run(
                command, cwd=ROOT, env=child_env, text=True, capture_output=True,
                shell=False, timeout=30, check=False,
            )
        finally:
            duration = time.perf_counter() - started
            self.cli_seconds += duration
            if module == "controller" and operation == "contract":
                print(f"harness controller contract latency_seconds={duration:.6f}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"{module} {operation} exited {result.returncode}")
        if result.stdout != str(output) + "\n":
            raise ValueError(f"{module} {operation} did not print exactly its output path")

    def context(self, event: str, text: str) -> dict[str, Any]:
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}

    def dispatch(self, event: str) -> dict[str, Any] | None:
        state, session = self.initialize()
        if event == "SessionStart":
            handoff = Path(state["handoff_path"])
            if handoff.is_file():
                self.call("verifier", "validate-handoff", ["--handoff", str(handoff)], handoff)
                validate(handoff, "handoff.schema.json")
                return self.context(event, "HARNESS_HANDOFF\n" + handoff.read_text(encoding="utf-8"))
            return None
        if event == "UserPromptSubmit":
            return self.submit(state, session)
        if event == "Stop":
            return self.stop(state, session)
        raise ValueError("unsupported hook event")

    def submit(self, state: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
        prompt = self.payload["prompt"]
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a nonempty string")
        contract_path = Path(state["contract_path"])
        if session["phase"] == "awaiting_approval" and prompt.strip().lower() == "approve":
            validate(contract_path, "contract.schema.json")
            if hashlib.sha256(contract_path.read_bytes()).hexdigest() != session["contract_sha256"]:
                raise ValueError("contract changed after review; submit edits to regenerate")
            session["phase"] = "approved"
            self.save(state, session)
            return self.context("UserPromptSubmit", "HARNESS_APPROVED: The user approved the displayed contract.\n"
                                + SKILL.read_text(encoding="utf-8"))
        request = self.directory / "request.txt"
        text = prompt
        if session["phase"] == "awaiting_approval" and request.is_file():
            text = request.read_text(encoding="utf-8") + "\n\nUser edits:\n" + prompt
        session["phase"] = "idle"
        state["attempt"] = 0
        self.save(state, session)
        request.write_text(text, encoding="utf-8")
        handoff = Path(state["handoff_path"])
        self.call("controller", "contract", [
            "--prompt", str(request), "--handoff", str(handoff) if handoff.is_file() else "none",
            "--cases", os.environ.get("HARNESS_CASES", str(ROOT / "controller/case_library/seed")),
            "--backend", os.environ.get("HARNESS_BACKEND", "codex_cli"), "--out", str(contract_path),
        ], contract_path)
        validate(contract_path, "contract.schema.json")
        session.update(phase="awaiting_approval", contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest())
        self.save(state, session)
        stub_note = "HARNESS_STUB=1: fixture contract and verdicts are SYNTHETIC; never claim actual validation from them.\n" if os.environ.get("HARNESS_STUB") == "1" else ""
        return self.context("UserPromptSubmit", "HARNESS_CONTRACT\n" + stub_note
                            + SKILL.read_text(encoding="utf-8") + "\n\n"
                            + contract_path.read_text(encoding="utf-8"))

    def stop(self, state: dict[str, Any], session: dict[str, Any]) -> dict[str, Any] | None:
        if session["phase"] != "approved":
            return None
        limit = int(os.environ.get("HARNESS_MAX_ATTEMPTS", "3"))
        if limit < 1:
            raise ValueError("HARNESS_MAX_ATTEMPTS must be at least 1")
        transcript = self.payload.get("transcript_path")
        if not isinstance(transcript, str) or not Path(transcript).is_file():
            raise ValueError("verification requires an available transcript path")
        attempt = state["attempt"] + 1
        verdict_path = Path(state["verdict_path"])
        self.call("verifier", "check", [
            "--contract", state["contract_path"], "--workspace", str(self.workspace),
            "--transcript", transcript, "--attempt", str(attempt), "--out", str(verdict_path),
        ], verdict_path)
        verdict = validate(verdict_path, "verdict.schema.json")
        if verdict["attempt"] != attempt:
            raise ValueError("verifier attempt does not match the requested attempt")
        state["attempt"] = attempt
        if verdict["overall"] == "pass":
            session["phase"] = "complete"
            self.save(state, session)
            return None
        if attempt >= limit or verdict["reinstruct_message"] is None:
            session["phase"] = "exhausted"
            self.save(state, session)
            unmet = "\n".join(f"{item['id']} ({item['status']}): {item['reason']} Evidence: {item['evidence']}"
                              for item in verdict["items"] if item["status"] != "pass")
            return {"systemMessage": f"Harness ended after attempt {attempt}; unmet items:\n{unmet}"}
        self.save(state, session)
        return {"decision": "block", "reason": verdict["reinstruct_message"]}
