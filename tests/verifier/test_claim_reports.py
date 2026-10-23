"""Labeled synthetic reports and deterministic claim-observation regressions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from verifier.claims import claim_observations, claimed_criteria, extract_claims


FIXTURE = json.loads((Path(__file__).parent / "fixtures/claim_reports.json").read_text())


@pytest.mark.parametrize("case", FIXTURE["reports"], ids=lambda case: case["name"])
def test_labeled_final_report(case: dict[str, Any]) -> None:
    descriptions = FIXTURE["descriptions"]
    claims = extract_claims(str(case["text"]), descriptions, descriptions)
    assert set(claims) == set(case["expected"])
    assert all(clause and clause in case["text"] for clause in claims.values())


def test_fixture_precision_recall(claim_metrics: Callable[[dict[str, int]], None]) -> None:
    cases = FIXTURE["reports"]
    descriptions = FIXTURE["descriptions"]
    assert len(cases) >= 30
    assert len({case["name"] for case in cases}) == len(cases)
    true_positive = false_positive = false_negative = 0
    for case in cases:
        expected = set(case["expected"])
        assert expected <= set(descriptions)
        observed = claimed_criteria(case["text"], descriptions, descriptions)
        true_positive += len(expected & observed)
        false_positive += len(observed - expected)
        false_negative += len(expected - observed)
    claim_metrics({"reports": len(cases), "tp": true_positive,
                   "fp": false_positive, "fn": false_negative})
    assert true_positive > 0
    assert false_positive == false_negative == 0


def test_exact_supporting_clause_and_first_affirmation() -> None:
    report = "SC-1 pending.  **SC-2** completed! SC-1 is DONE; SC-2 passing."
    assert extract_claims(report, ["SC-1", "SC-2"]) == {
        "SC-1": "SC-1 is DONE;", "SC-2": "**SC-2** completed!",
    }


def test_description_shared_vocabulary_needs_distinctive_word() -> None:
    descriptions = {"SC-1": "Export CSV report", "SC-2": "Export JSON report"}
    assert extract_claims("Export report completed.", descriptions, descriptions) == {}
    assert extract_claims("CSV report done.", descriptions, descriptions) == {"SC-1": "CSV report done."}
    assert extract_claims("JSON report done.", descriptions, descriptions) == {"SC-2": "JSON report done."}


def test_identical_descriptions_are_ambiguous() -> None:
    descriptions = {"SC-1": "Export CSV report", "SC-2": "Export CSV report"}
    assert extract_claims("Export CSV report done.", descriptions, descriptions) == {}


def test_unknown_table_status_cannot_borrow_completion_from_description() -> None:
    descriptions = {"SC-1": "Unit tests pass"}
    report = "| Description | Status |\n| --- | --- |\n| Unit tests pass | N/A |"
    assert extract_claims(report, descriptions, descriptions) == {}


def test_unchecked_checklist_row_with_status_cells_stays_unclaimed() -> None:
    assert extract_claims("- [ ] SC-1 | Passed", ["SC-1"]) == {}
    assert extract_claims("- [x] SC-1 | Passed", ["SC-1"]) == {"SC-1": "- [x] SC-1 | Passed"}


def test_description_one_word_and_whole_word_boundaries() -> None:
    descriptions = {"SC-1": "Authentication", "SC-2": "Authorization"}
    assert claimed_criteria("Authentication done.", descriptions, descriptions) == {"SC-1"}
    assert claimed_criteria("Preauthentication done.", descriptions, descriptions) == set()


def test_description_does_not_bridge_a_negative() -> None:
    descriptions = {"SC-1": "Authentication validation"}
    assert extract_claims("Authentication pending, validation completed.", descriptions, descriptions) == {}


def test_empty_criteria() -> None:
    assert extract_claims("All success criteria met.", []) == {}
    assert claim_observations([], {}, {"items": [{"id": "contract-quality", "status": "unverifiable"}]}) == {
        "items": [], "summary": {"claimed_items": 0, "claimed_and_pass": 0, "claimed_and_fail": 0,
                                  "claimed_and_unverifiable": 0, "unclaimed_items": 0},
    }
