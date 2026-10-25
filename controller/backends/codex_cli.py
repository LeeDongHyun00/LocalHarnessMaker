"""Logged-in Codex CLI backend with isolated, read-only child executions."""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from controller.analyze import Prices, calculate_cost
from controller.backends.base import Message, Usage, configured_prices, control_timeout, log_control_timeout
from controller.backends.cheap_api import structured_schema
from controller.errors import BackendError, InputError, InvalidGeneration, TransportError
from controller.settings import PACKAGE_DIR, load_object
from controller.diagnostics import byte_count, private_paths, trace, trace_failure

logger = logging.getLogger(__name__)
Runner = Callable[..., subprocess.CompletedProcess[str]]
APP_BUNDLE_CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"


def resolve_executable(cli: str) -> str:
    """Prefer the host override, then configured CLI/PATH, then the Mac bundle."""
    override = os.environ.get("HARNESS_CODEX")
    if override:
        if not Path(override).is_absolute():
            raise TransportError("HARNESS_CODEX must be an absolute executable path")
        resolved = shutil.which(override)
        if not resolved:
            raise TransportError(f"codex executable not found or not executable: {override}")
        return resolved
    # Preserve explicit configured/injected paths used by historical callers.
    if os.path.sep in cli:
        return str(Path(cli).absolute())
    resolved = shutil.which(cli) or shutil.which(APP_BUNDLE_CODEX)
    if not resolved:
        raise TransportError("codex executable not found (HARNESS_CODEX, PATH, application bundle)")
    return str(Path(resolved).absolute())


def provider_error(events: str, stderr: str) -> str | None:
    """Keep provider diagnostics independent of truncated event-log presentation."""
    messages: list[str] = []
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") not in {"error", "turn.failed"}:
            continue
        value = event.get("error", event.get("message"))
        # CLI versions may wrap a provider error as a JSON-encoded message.
        for _ in range(4):
            if isinstance(value, dict):
                value = value.get("error", value.get("message"))
            elif isinstance(value, str):
                try:
                    value = json.loads(value)
                except ValueError:
                    break
            else:
                break
        if isinstance(value, str) and value:
            messages.append(value)
    return ("\n".join(dict.fromkeys(messages)) or stderr.strip() or None)


def _read_usage(events: str, prices: Prices | None) -> Usage:
    """Sum completed-turn JSONL usage and price it at configured API rates."""
    totals: list[int | None] = [0, 0, 0]
    found = False
    for line in events.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            return Usage(None, None, None, 0.0)
        if not isinstance(event, dict):
            return Usage(None, None, None, 0.0)
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            return Usage(None, None, None, 0.0)
        counts = [usage.get("input_tokens"), usage.get("output_tokens"),
                  usage.get("cached_input_tokens", usage.get("cached_tokens"))]
        if any(value is not None and (type(value) is not int or value < 0) for value in counts):
            return Usage(None, None, None, 0.0)
        if counts[0] is not None and counts[2] is not None and counts[2] > counts[0]:
            return Usage(None, None, None, 0.0)
        totals = [None if old is None or new is None else old + new
                  for old, new in zip(totals, counts)]
        found = True
    if not found:
        return Usage(None, None, None, 0.0)
    inputs, outputs, cached = totals
    cost = (calculate_cost(inputs, outputs, prices, cached)
            if None not in (inputs, outputs, cached, prices) else None)
    return Usage(inputs, outputs, cost, 0.0, cached)


def _render_prompt(messages: list[Message]) -> str:
    """Render controller instructions and request data as a single stdin prompt."""
    parts: list[str] = []
    for message in messages:
        role, content = message.get("role"), message.get("content")
        if role not in ("system", "user") or not isinstance(content, str):
            raise InputError("Codex CLI messages must have system/user roles and text content")
        header = "Controller instructions" if role == "system" else "Controller input data"
        parts.append(f"## {header}\n\n{content}")
    prompt = "\n\n".join(parts).strip()
    if not prompt:
        raise InputError("Codex CLI requires a nonempty prompt")
    return prompt + "\n"


class CodexCLIBackend:
    """Run one schema-constrained invocation through the user's CLI login."""

    def __init__(
        self, *, runner: Runner = subprocess.run, config: dict[str, Any] | None = None,
        prices: Prices | None = None, executable: str | None = None,
        clock: Callable[[], float] = time.monotonic,
        persist_session: bool = False, log_calls: bool = True,
    ) -> None:
        root = load_object(PACKAGE_DIR / "config.yaml")
        self.config = config if config is not None else root["codex_cli"]
        self.timeout = control_timeout(self.config)
        try:
            self.prices, self.pricing_ref = configured_prices(self.config, prices)
            self.model = str(self.config["model"])
            self.reasoning_effort = str(self.config["reasoning_effort"])
            self.sandbox = str(self.config["sandbox"])
            cli = executable or str(self.config["executable"])
            if not self.model or self.reasoning_effort != "low" or self.sandbox != "read-only":
                raise ValueError("Unexpected Codex model execution policy")
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise InputError("Invalid Codex CLI configuration or prices") from exc
        try:
            self.executable = resolve_executable(cli)
        except TransportError as exc:
            trace_failure(exc, message=str(exc))
            raise
        trace("executable_resolved", path=self.executable)
        self.runner = runner
        self.clock = clock
        self.persist_session = persist_session
        self.log_calls = log_calls
        self.error: str | None = None
        self._usage = Usage(None, None, None, 0.0)

    def usage(self) -> Usage:
        """Return token use and API-equivalent cost from the last CLI call."""
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        prompt = _render_prompt(messages)
        self._usage = Usage(None, None, None, 0.0)
        started = self.clock()
        status = "error"
        events = ""
        stderr = ""
        self.error = None
        with tempfile.TemporaryDirectory(prefix="localharness-codex-") as temporary:
            workdir = Path(temporary)
            if any(workdir.iterdir()):
                raise BackendError("Codex temporary working directory is not empty")
            schema_path = workdir / "wire-schema.json"
            output_path = workdir / "last-message.json"
            schema_path.write_text(json.dumps(structured_schema(schema)), encoding="utf-8")
            argv = [
                self.executable, "exec", "--model", self.model,
                "--sandbox", self.sandbox,
                *([] if self.persist_session else ["--ephemeral"]), "--skip-git-repo-check",
                "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                "--output-schema", str(schema_path), "-o", str(output_path), "--json", "-",
            ]
            child_env = os.environ.copy()
            child_env["HARNESS_NESTED"] = "1"
            try:
                try:
                    trace("child_start", argv=[argv[0], *[private_paths(arg) for arg in argv[1:]]],
                          environment_keys_set=["HARNESS_NESTED"])
                    child_started = time.monotonic()
                    try:
                        result = self.runner(
                            argv, input=prompt, cwd=workdir, env=child_env, text=True,
                            capture_output=True, timeout=self.timeout, check=False, shell=False,
                        )
                    except (Exception, KeyboardInterrupt, SystemExit) as exc:
                        trace_failure(exc, message="child execution failed; message redacted")
                        trace("child_exit", exit_code=None, elapsed_seconds=time.monotonic() - child_started,
                              stdout_bytes=byte_count(getattr(exc, "stdout", None)),
                              stderr_bytes=byte_count(getattr(exc, "stderr", None)))
                        raise
                    trace("child_exit", exit_code=result.returncode,
                          elapsed_seconds=time.monotonic() - child_started,
                          stdout_bytes=byte_count(result.stdout),
                          stderr_bytes=byte_count(result.stderr))
                    events = result.stdout or ""
                    stderr = result.stderr or ""
                except subprocess.TimeoutExpired as exc:
                    raw = exc.stdout or ""
                    events = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                    raw_error = exc.stderr or ""
                    stderr = raw_error.decode("utf-8", errors="replace") if isinstance(raw_error, bytes) else raw_error
                    self._usage = _read_usage(events, self.prices)
                    log_control_timeout(logger, "codex_cli", self.model, self.timeout)
                    raise TransportError("Codex CLI timed out; consult its JSONL usage log") from exc
                except OSError as exc:
                    # Spawn failed before a process existed; no inference was run.
                    self._usage = Usage(0, 0, 0.0, 0.0, 0)
                    raise TransportError("Codex CLI executable could not be started") from exc
                self._usage = _read_usage(events, self.prices)
                for line in events.splitlines():
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(event, dict) and event.get("model") not in (None, self.model):
                        raise BackendError("Codex CLI reported a conflicting model identity")
                if result.returncode != 0:
                    raise TransportError(f"Codex CLI exited with status {result.returncode}")
                if not output_path.is_file():
                    raise TransportError("Codex CLI did not write its final-message file")
                try:
                    value = json.loads(output_path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise InvalidGeneration("Codex CLI final message was not valid JSON") from exc
                if not isinstance(value, dict) or not Draft202012Validator(schema).is_valid(value):
                    raise InvalidGeneration("Codex CLI output failed contract schema validation")
                status = "success"
                return value
            except OSError as exc:
                raise TransportError("Codex CLI output could not be read") from exc
            finally:
                if status != "success":
                    diagnostic = provider_error(events, stderr)
                    self.error = diagnostic[:2000] if diagnostic else None
                logger.info("control_cli_events %s", json.dumps({"model": self.model, "events": events}))
                self._usage = Usage(
                    self._usage.input_tokens, self._usage.output_tokens, self._usage.usd,
                    max(0.0, self.clock() - started), self._usage.cached_input_tokens,
                )
                if self.log_calls:
                    logger.info("control_call %s", json.dumps({
                        "backend": "codex_cli", "model": self.model,
                        "executable": self.executable,
                        "timeout_seconds": self.timeout,
                        "reasoning_effort": self.reasoning_effort, "status": status,
                        "error": self.error, "pricing_ref": self.pricing_ref,
                        **asdict(self._usage),
                    }, sort_keys=True))
