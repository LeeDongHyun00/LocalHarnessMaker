"""Package resources remain anchored when invoked by an installed hook adapter."""

import hashlib
from pathlib import Path

import pytest

from controller.backends.base import configured_prices
from controller.backends.codex_cli import CodexCLIBackend
from controller.contract_gen import generate_contract, read_request
from controller.generation import schema_validator
from controller.handoff_gen import generate_handoff
from controller.judge import generate_judgment
from controller.settings import PACKAGE_DIR, load_object, pricing_snapshot
from tests.controller.support import ROOT, model_contract
from tests.controller.test_codex_cli import MockRunner
from tests.controller.test_commands import criterion, handoff, inputs, judgment


def test_pricing_snapshot_resolves_to_package_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = (PACKAGE_DIR / "prices.yaml").read_bytes()
    # A cwd-local decoy must never become pricing authority.
    decoy = tmp_path / "controller"
    decoy.mkdir()
    (decoy / "prices.yaml").write_text("invalid cwd snapshot")
    monkeypatch.chdir(tmp_path)
    path, data, book = pricing_snapshot()
    assert path == PACKAGE_DIR / "prices.yaml" and path.is_absolute()
    assert data == expected and book == load_object(path)
    prices, reference = configured_prices({"price_key": "gpt-6-luna"})
    assert prices is not None
    assert reference == (f"controller/prices.yaml@{book['checked_on']}#gpt-6-luna:sha256:"
                         f"{hashlib.sha256(expected).hexdigest()}")


@pytest.mark.parametrize("operation", ["contract", "judge", "handoff"])
def test_historical_operations_from_external_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    output = {"contract": model_contract, "judge": judgment, "handoff": handoff}[operation]()
    runner = MockRunner(output=output)
    backend = CodexCLIBackend(runner=runner, executable="/mock/codex")
    if operation == "contract":
        result = generate_contract(read_request(ROOT / "schemas/examples/prompt.json"), backend)
    elif operation == "judge":
        artifact = tmp_path / "diff.txt"
        artifact.write_text("synthetic diff")
        result = generate_judgment(criterion(), artifact, backend)
    else:
        contract, verdict = inputs()
        result = generate_handoff("Synthetic transcript", contract, verdict, backend)
    schema = "judgment" if operation == "judge" else operation
    schema_validator(f"{schema}.schema.json").validate(result)
    assert len(runner.calls) == 1
    assert backend.pricing_ref is not None
