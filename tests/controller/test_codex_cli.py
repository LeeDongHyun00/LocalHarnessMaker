import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from controller.backends.codex_cli import CodexCLIBackend, _read_usage
from controller.backends.cheap_api import structured_schema
from controller.contract_gen import build_messages
from controller.errors import BackendError, InputError, InvalidGeneration
from controller.settings import load_object
from tests.controller.support import ROOT, model_contract


def contract_schema() -> dict[str, Any]:
    schema = load_object(ROOT / "schemas/contract.schema.json")
    for field in ("reasoning_effort", "cost_estimate"):
        schema["properties"].pop(field)
        schema["required"].remove(field)
    return schema


def events(
    inputs: int = 1200, cached: int = 300, outputs: int = 250
) -> str:
    return json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": inputs, "cached_input_tokens": cached,
        "output_tokens": outputs, "reasoning_output_tokens": 40,
    }}) + "\n"


class MockRunner:
    def __init__(self, *, returncode: int = 0, output: Any = None,
                 stdout: str | None = None) -> None:
        self.returncode = returncode
        self.output = model_contract() if output is None else output
        self.stdout = events() if stdout is None else stdout
        self.calls: list[dict[str, Any]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cwd = Path(kwargs["cwd"])
        schema_path = Path(argv[argv.index("--output-schema") + 1])
        self.calls.append({"argv": argv.copy(), "cwd": cwd, "kwargs": kwargs.copy(),
                           "initial_files": sorted(path.name for path in cwd.iterdir()),
                           "schema": json.loads(schema_path.read_text(encoding="utf-8"))})
        if self.returncode == 0:
            output_path = Path(argv[argv.index("-o") + 1])
            output_path.write_text(json.dumps(self.output), encoding="utf-8")
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, "mock stderr")


def test_codex_cli_uses_read_only_empty_temp_and_low_effort(
    caplog: pytest.LogCaptureFixture
) -> None:
    parent_guard = os.environ.get("HARNESS_NESTED")
    runner = MockRunner()
    ticks = iter([5.0, 6.75])
    backend = CodexCLIBackend(runner=runner, clock=lambda: next(ticks), executable="/usr/bin/codex")
    messages = build_messages('Prompt says "hello".', examples=[])
    with caplog.at_level(logging.INFO):
        assert backend.generate(contract_schema(), messages) == model_contract()
    call = runner.calls[0]
    argv = call["argv"]
    assert argv[1:7] == ["exec", "--model", "gpt-6-luna", "--sandbox", "read-only", "--ephemeral"]
    assert "--skip-git-repo-check" in argv and "--json" in argv and "-" == argv[-1]
    assert argv[argv.index("--config") + 1] == 'model_reasoning_effort="low"'
    assert call["kwargs"]["shell"] is False and call["kwargs"]["check"] is False
    assert call["kwargs"]["text"] is True and call["kwargs"]["capture_output"] is True
    assert call["kwargs"]["timeout"] == 180
    assert call["kwargs"]["input"] == "\n\n".join(
        f"## {('Controller instructions' if msg['role'] == 'system' else 'Controller input data')}\n\n{msg['content']}"
        for msg in messages
    ) + "\n"
    assert call["kwargs"]["env"]["HARNESS_NESTED"] == "1"
    assert os.environ.get("HARNESS_NESTED") == parent_guard
    assert call["initial_files"] == ["wire-schema.json"]
    assert call["cwd"].is_absolute() and not call["cwd"].exists()
    wire = structured_schema(contract_schema())
    assert call["schema"] == wire
    assert wire["type"] == "object" and "reasoning_effort" not in wire["required"]
    usage = backend.usage()
    assert (usage.input_tokens, usage.cached_input_tokens, usage.output_tokens) == (1200, 300, 250)
    assert usage.usd == pytest.approx((900 * .10 + 300 * .01 + 250 * .50) / 1_000_000)
    assert usage.latency_seconds == 1.75
    assert '"backend": "codex_cli"' in caplog.text
    assert '"reasoning_effort": "low"' in caplog.text
    assert "mock stderr" not in caplog.text


def test_wire_schema_is_written_to_the_temp_path() -> None:
    runner = MockRunner()
    backend = CodexCLIBackend(runner=runner, executable="/usr/bin/codex")
    backend.generate(contract_schema(), build_messages("test"))
    call = runner.calls[0]
    schema_path = Path(call["argv"][call["argv"].index("--output-schema") + 1])
    assert schema_path == call["cwd"] / "wire-schema.json"
    assert call["schema"] == structured_schema(contract_schema())


def test_token_events_sum_completed_turns_and_price_cache() -> None:
    price_dict = load_object(ROOT / "controller/prices.yaml")["models"]["gpt-6-luna"]
    from controller.analyze import Prices
    prices = Prices.from_dict(price_dict)
    usage = _read_usage("\n".join([
        json.dumps({"type": "turn.started"}), events(1000, 200, 100).strip(),
        events(200, 0, 50).strip(), "not json",
    ]), prices)
    assert (usage.input_tokens, usage.cached_input_tokens, usage.output_tokens) == (1200, 200, 150)
    assert usage.usd == pytest.approx((1000 * .10 + 200 * .01 + 150 * .50) / 1_000_000)


def test_missing_or_invalid_usage_remains_unknown() -> None:
    from controller.analyze import Prices
    rates = Prices.from_dict(load_object(ROOT / "controller/prices.yaml")["models"]["gpt-6-luna"])
    assert _read_usage('{"type":"turn.completed"}', rates).usd is None
    assert _read_usage(json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": -1, "output_tokens": 1,
    }}), rates).usd is None
    assert _read_usage(json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 10, "cached_input_tokens": 20, "output_tokens": 1,
    }}), rates).usd is None


@pytest.mark.parametrize("output", [{}, {"task_summary": "bad"}, []])
def test_cli_output_still_gets_local_schema_validation(output: Any) -> None:
    backend = CodexCLIBackend(runner=MockRunner(output=output), executable="/usr/bin/codex")
    with pytest.raises(InvalidGeneration):
        backend.generate(contract_schema(), build_messages("test"))


def test_nonzero_exit_logs_available_usage(caplog: pytest.LogCaptureFixture) -> None:
    backend = CodexCLIBackend(runner=MockRunner(returncode=17), executable="/usr/bin/codex")
    with caplog.at_level(logging.INFO), pytest.raises(BackendError, match="status 17"):
        backend.generate(contract_schema(), build_messages("test"))
    assert backend.usage().input_tokens == 1200
    assert backend.usage().usd is not None
    assert '"status": "error"' in caplog.text


def test_timeout_preserves_partial_event_usage() -> None:
    def timeout(argv: list[str], **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"], output=events().encode())
    backend = CodexCLIBackend(runner=timeout, executable="/usr/bin/codex")
    with pytest.raises(BackendError, match="timed out"):
        backend.generate(contract_schema(), build_messages("test"))
    assert backend.usage().input_tokens == 1200
    assert backend.usage().usd is not None


def test_unknown_usage_after_success_is_an_error() -> None:
    backend = CodexCLIBackend(runner=MockRunner(stdout="not JSONL\n"), executable="/usr/bin/codex")
    with pytest.raises(BackendError, match="no completed-turn token usage"):
        backend.generate(contract_schema(), build_messages("test"))
    assert backend.usage().usd is None


def test_invalid_messages_and_missing_cli_are_input_errors() -> None:
    with pytest.raises(InputError):
        CodexCLIBackend(executable="/no/such/codex").generate(contract_schema(), [{"role": "tool", "content": "bad"}])


def test_api_fallback_model_and_rates_match_cli_estimate() -> None:
    config = load_object(ROOT / "controller/config.yaml")
    price = load_object(ROOT / "controller/prices.yaml")["models"]["gpt-6-luna"]
    assert config["cheap_api"]["model"] == config["codex_cli"]["model"] == "gpt-6-luna"
    assert price == {"input_per_million": "0.10", "cached_input_per_million": "0.01",
                     "output_per_million": "0.50"}
