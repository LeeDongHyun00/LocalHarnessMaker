"""Retrieval fixtures are hand-written, not collected model output."""

import json
from pathlib import Path

import pytest

from controller.cases import retrieve_cases
from controller.errors import InputError
from controller.settings import load_object
from tests.controller.support import ROOT


def test_bm25_top_three_dedup_and_stable_ties(tmp_path: Path) -> None:
    cases = []
    for word in ("health", "invoice", "health", "health", "health"):
        case = load_object(ROOT / "schemas/examples/contract.json")
        case["task_summary"] = f"{word} {len(cases)}"
        case["constraints"] = []
        case["success_criteria"] = [{"id": "SC-1", "description": word,
            "check": {"type": "file_exists", "path": f"{word}.txt"}}]
        cases.append(case)
    nested = tmp_path / "verified"
    nested.mkdir()
    (nested / "cases.jsonl").write_text("\n".join(json.dumps(c) for c in [*cases, cases[0]]))
    result = retrieve_cases("health", tmp_path)
    assert [c["task_summary"] for c in result] == ["health 0", "health 2", "health 3"]
    assert retrieve_cases("unrelated", tmp_path) == []


@pytest.mark.parametrize("content", ["broken", "{}", "[]"])
def test_bad_case_fails_closed(content: str, tmp_path: Path) -> None:
    (tmp_path / "cases.jsonl").write_text(content)
    with pytest.raises(InputError):
        retrieve_cases("health", tmp_path)


def test_empty_library(tmp_path: Path) -> None:
    assert retrieve_cases("request", tmp_path) == []
