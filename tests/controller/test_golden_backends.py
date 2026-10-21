"""Thirty authored samples compare adapter plumbing, never live model quality."""

import json
from decimal import Decimal

import pytest

from controller.analyze import Prices
from controller.backends.cheap_api import CheapAPIBackend
from controller.backends.codex_cli import CodexCLIBackend
from controller.backends.local import LocalBackend
from controller.contract_gen import generate_contract
from tests.controller.support import ROOT, RecordingTransport, response
from tests.controller.test_codex_cli import MockRunner
from tests.controller.test_local import envelope, local_config


@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api", "local"])
def test_thirty_authored_golden_samples(selected: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-golden-placeholder")
    samples = json.loads((ROOT / "tests/controller/fixtures/requests-v1.json").read_text())
    passed = covered = ambiguous = 0
    for sample in samples:
        check = sample["check"]
        golden = {"task_summary": sample["summary"], "constraints": [sample["constraint"]],
            "success_criteria": [{"id": "SC-1", "description": sample["summary"], "check": check}],
            "verification": [{"command": check["command"], "expected": check["expected"]}]
                if check["type"] == "command" else [],
            "stop_conditions": ["Approved prerequisites or scope are unavailable."],
            "assumptions": sample["assumptions"]}
        if selected == "codex_cli":
            backend = CodexCLIBackend(runner=MockRunner(output=golden), executable="/mock/codex")
        elif selected == "cheap_api":
            backend = CheapAPIBackend(transport=RecordingTransport([response(golden)]))
        else:
            # Synthetic explicit prices exercise non-null contract accounting;
            # production local prices remain unknown and are never invented.
            backend = LocalBackend(config=local_config(), transport=RecordingTransport([envelope(golden)]),
                prices=Prices(Decimal(1), Decimal('.5'), Decimal(2)))
        result = generate_contract(sample["prompt"], backend)
        assert result["success_criteria"] == golden["success_criteria"]
        assert result["assumptions"] == sample["assumptions"]
        passed += 1
        if sample["ambiguous"]:
            ambiguous += 1
            covered += bool(result["assumptions"])
    print(f"Mocked {selected}: schema={passed}/30; ambiguous assumptions={covered}/{ambiguous}; "
          "latency/cost are synthetic, live comparison pending")
    assert len({sample["id"] for sample in samples}) == passed == 30
    assert covered == ambiguous == 8
