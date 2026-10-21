import io
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from controller.__main__ import main
from controller.settings import load_object
from tests.controller.mock_contract_cli import mock_urlopen
from tests.controller.support import ROOT


def arguments(out: Path) -> list[str]:
    return ["contract", "--prompt", str(ROOT / "schemas/examples/prompt.json"),
            "--handoff", "none", "--cases", str(ROOT / "controller/case_library/seed"),
            "--backend", "cheap_api", "--out", str(out)]


def test_cli_writes_valid_output_and_exactly_one_stdout_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-placeholder")
    monkeypatch.setattr("controller.backends.cheap_api.urlopen", mock_urlopen)
    output = tmp_path / "contract.json"
    assert main(arguments(output)) == 0
    captured = capsys.readouterr()
    assert captured.out == f"{output}\n"
    Draft202012Validator(load_object(ROOT / "schemas/contract.schema.json")).validate(load_object(output))


@pytest.mark.parametrize("kind", ["arguments", "prompt", "handoff", "cases", "local", "out", "jsonl"])
def test_input_errors_exit_one_without_writing_output(
    kind: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "contract.json"
    args = arguments(output)
    if kind == "arguments":
        args = ["contract"]
    elif kind == "jsonl":
        (tmp_path / "case.jsonl").write_text("{}\n", encoding="utf-8")
        args[args.index("--cases") + 1] = str(tmp_path)
    else:
        option = {"prompt": "--prompt", "handoff": "--handoff", "cases": "--cases",
                  "local": "--backend", "out": "--out"}[kind]
        args[args.index(option) + 1] = "local" if kind == "local" else str(tmp_path / "missing" / "file")
    assert main(args) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("controller:")
    assert not output.exists()


def test_missing_credentials_is_input_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(arguments(tmp_path / "out.json")) == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_invalid_generations_exit_two_and_preserve_existing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from tests.controller.support import response
    import json
    calls = 0

    def opener(*args: Any, **kwargs: Any) -> io.BytesIO:
        nonlocal calls
        calls += 1
        return io.BytesIO(json.dumps(response({})).encode("utf-8"))

    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-placeholder")
    monkeypatch.setattr("controller.backends.cheap_api.urlopen", opener)
    output = tmp_path / "contract.json"
    output.write_text("existing", encoding="utf-8")
    assert main(arguments(output)) == 2
    assert capsys.readouterr().out == ""
    assert output.read_text(encoding="utf-8") == "existing"
    assert calls == 3
