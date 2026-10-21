"""Opt-in SC-2 integration: launch codex exec exactly once to inspect injection."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from plugin.demo import start


@pytest.mark.skipif(os.environ.get("HARNESS_CODEX_LIVE") != "1", reason="opt-in real Codex call")
def test_contract_visible_in_one_codex_exec(tmp_path: Path) -> None:
    output = Path(os.environ["HARNESS_CODEX_EVIDENCE"]) if "HARNESS_CODEX_EVIDENCE" in os.environ else tmp_path / "evidence"
    metadata = start(output)
    summary = json.loads((output / "request-summary.json").read_text())
    assert summary == {"contract_visible": True, "approval_pending": True, "verifier_calls": 0}
    command = json.loads((output / "request-result.json").read_text())["command"]
    assert command.count("exec") == 1 and "resume" not in command
    assert metadata["approval"] == "pending"
