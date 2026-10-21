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
from controller.backends.base import Message, Usage
from controller.backends.cheap_api import structured_schema
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.settings import PACKAGE_DIR, load_object

logger = logging.getLogger(__name__)
Runner = Callable[..., subprocess.CompletedProcess[str]]


def _read_usage(events: str, prices: Prices) -> Usage:
    """Sum completed-turn JSONL usage and price it at configured API rates."""
    input_tokens = output_tokens = cached_tokens = 0
    found = False
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict) or event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
        inputs = usage.get("input_tokens")
        outputs = usage.get("output_tokens")
        cached = usage.get("cached_input_tokens", usage.get("cached_tokens", 0))
        if any(type(value) is not int or value < 0 for value in (inputs, outputs, cached)):
            continue
        input_tokens += inputs
        output_tokens += outputs
        cached_tokens += cached
        found = True
    if not found:
        return Usage(None, None, None, 0.0)
    if cached_tokens > input_tokens:
        return Usage(None, None, None, 0.0)
    return Usage(input_tokens, output_tokens,
                 calculate_cost(input_tokens, output_tokens, prices, cached_tokens), 0.0,
                 cached_tokens)


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
    ) -> None:
        root = load_object(PACKAGE_DIR / "config.yaml")
        self.config = config if config is not None else root["codex_cli"]
        try:
            price_book = load_object(PACKAGE_DIR / "prices.yaml")
            self.prices = prices if prices is not None else Prices.from_dict(
                price_book["models"][self.config["price_key"]]
            )
            self.model = str(self.config["model"])
            self.reasoning_effort = str(self.config["reasoning_effort"])
            self.sandbox = str(self.config["sandbox"])
            self.timeout = float(self.config["timeout_seconds"])
            cli = executable or str(self.config["executable"])
            if not self.model or self.reasoning_effort != "low" or self.sandbox != "read-only":
                raise ValueError("Unexpected Codex model execution policy")
            if self.timeout <= 0:
                raise ValueError("Timeout must be positive")
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            raise InputError("Invalid Codex CLI configuration or prices") from exc
        self.executable = shutil.which(cli) if os.path.sep not in cli else cli
        if not self.executable:
            raise InputError("Codex CLI executable was not found on PATH")
        self.runner = runner
        self.clock = clock
        self._usage = Usage(None, None, None, 0.0)

    def usage(self) -> Usage:
        """Return token use and API-equivalent cost from the last CLI call."""
        return self._usage

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        prompt = _render_prompt(messages)
        self._usage = Usage(None, None, None, 0.0)
        started = self.clock()
        status = "error"
        with tempfile.TemporaryDirectory(prefix="localharness-codex-") as temporary:
            workdir = Path(temporary)
            if any(workdir.iterdir()):
                raise BackendError("Codex temporary working directory is not empty")
            schema_path = workdir / "wire-schema.json"
            output_path = workdir / "last-message.json"
            schema_path.write_text(json.dumps(structured_schema(schema)), encoding="utf-8")
            argv = [
                self.executable, "exec", "--model", self.model,
                "--sandbox", self.sandbox, "--ephemeral", "--skip-git-repo-check",
                "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                "--output-schema", str(schema_path), "-o", str(output_path), "--json", "-",
            ]
            child_env = os.environ.copy()
            child_env["HARNESS_NESTED"] = "1"
            try:
                try:
                    result = self.runner(
                        argv, input=prompt, cwd=workdir, env=child_env, text=True,
                        capture_output=True, timeout=self.timeout, check=False, shell=False,
                    )
                    events = result.stdout or ""
                except subprocess.TimeoutExpired as exc:
                    raw = exc.stdout or ""
                    events = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                    self._usage = _read_usage(events, self.prices)
                    raise BackendError("Codex CLI timed out; consult its JSONL usage log") from exc
                self._usage = _read_usage(events, self.prices)
                if result.returncode != 0:
                    raise BackendError(f"Codex CLI exited with status {result.returncode}")
                if not output_path.is_file():
                    raise BackendError("Codex CLI did not write its final-message file")
                try:
                    value = json.loads(output_path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise InvalidGeneration("Codex CLI final message was not valid JSON") from exc
                if not isinstance(value, dict) or not Draft202012Validator(schema).is_valid(value):
                    raise InvalidGeneration("Codex CLI output failed contract schema validation")
                if self._usage.usd is None:
                    raise BackendError("Codex CLI events contained no completed-turn token usage")
                status = "success"
                return value
            except FileNotFoundError as exc:
                raise InputError("Codex CLI executable could not be started") from exc
            finally:
                self._usage = Usage(
                    self._usage.input_tokens, self._usage.output_tokens, self._usage.usd,
                    max(0.0, self.clock() - started), self._usage.cached_input_tokens,
                )
                logger.info("control_call %s", json.dumps({
                    "backend": "codex_cli", "model": self.model,
                    "reasoning_effort": self.reasoning_effort, "status": status,
                    **asdict(self._usage),
                }, sort_keys=True))
