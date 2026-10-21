"""Verifier-owned fixtures only; no imports from the controller."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
collect_ignore_glob = ["fixtures/*"]


@pytest.fixture
def contract() -> dict[str, Any]:
    return copy.deepcopy(json.loads((ROOT / "schemas/examples/contract.json").read_text()))


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "report.txt").write_text("health ok\nroute preserved\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def transcript() -> Path:
    return FIXTURES / "transcript_pass.jsonl"
