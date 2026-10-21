from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from verifier.check import check_contract
from verifier.claims import claimed_criteria, last_report
from verifier.sandbox import Execution


def report_record(text: str, phase: str = "final_answer", role: str = "assistant") -> dict[str, Any]:
    return {"type": "response_item", "payload": {"type": "message", "role": role,
            "phase": phase, "content": [{"type": "output_text", "text": text}]}}


@pytest.mark.parametrize("mode", ["exec", "tui"])
def test_measured_last_report(mode: str) -> None:
    source = Path(__file__).resolve().parents[2] / "plugin/evidence" / f"2026-10-21-{mode}"
    assert last_report(source / "transcript-excerpt.jsonl") == "SECOND_REPLY"


def test_only_latest_final_report(workspace: Path) -> None:
    records = [report_record("SC-1 done"), report_record("SC-2 done", role="user"),
               {"type": "response_item", "payload": {"type": "function_call_output", "output": "SC-1 done"}},
               report_record("SC-1 not done. SC-2 implemented."),
               report_record("SC-3 completed", phase="commentary"),
               {"type": "event_msg", "payload": {"type": "agent_message", "message": "SC-3 done"}}]
    path = workspace / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records))
    assert claimed_criteria(last_report(path), ["SC-1", "SC-2", "SC-3"]) == {"SC-2"}


@pytest.mark.parametrize(("text", "expected"), [
    ("SC-1 done. SC-2 completed. SC-3 passing.", {"SC-1", "SC-2", "SC-3"}),
    ("| SC-1 | implemented | app.py |\n| SC-2 | not done | absent |", {"SC-1"}),
    ("SC-1 and SC-2 completed", {"SC-1", "SC-2"}),
    ("SC-1, SC-2, SC-3 done.", {"SC-1", "SC-2", "SC-3"}),
    ("Done: SC-1, SC-2, SC-3.", {"SC-1", "SC-2", "SC-3"}),
    ("All done except SC-3.", set()),
    ("All done but SC-3.", set()),
    ("All done other than SC-3.", set()),
    ("All done apart from SC-3.", set()),
    ("All done besides SC-3.", set()),
    ("All done excluding SC-3.", set()),
    ("SC-1, SC-2 done except SC-3.", {"SC-1", "SC-2"}),
    ("Done: SC-1, SC-2, excluding SC-3.", {"SC-1", "SC-2"}),
    ("SC-1 completed, SC-2 not done", {"SC-1"}),
    ("SC-1 done and SC-2 not done", {"SC-1"}),
    ("SC-1 not done and SC-2 completed", {"SC-2"}),
    ("Completed SC-1", {"SC-1"}),
    ("Completed SC-1 and SC-2", {"SC-1", "SC-2"}),
    ("Not completed: SC-1", set()),
    ("SC-1 not completed. SC-2 never implemented. SC-3 will be done.", set()),
    ("SC-1 pending. SC-2 unverifiable. SC-3 failed.", set()),
    ("SC-10 done. All tasks done.", set()),
    ("> SC-1 done\n```\nSC-2 completed\n```\nSC-3 passing", {"SC-3"}),
])
def test_explicit_claim_scope(text: str, expected: set[str]) -> None:
    assert claimed_criteria(text, ["SC-1", "SC-2", "SC-3"]) == expected


@pytest.mark.parametrize("record", [[], {"role": "assistant", "content": "SC-1 done"},
                                      {"type": "response_item", "payload": []},
                                      {**report_record("done"), "payload": {
                                          **report_record("done")["payload"], "content": "done"}}])
def test_invalid_or_unsupported_transcript(workspace: Path, record: Any) -> None:
    path = workspace / "invalid.jsonl"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        last_report(path)


def test_claimed_without_evidence_regression(contract: dict[str, Any]) -> None:
    fixtures = Path(__file__).parent / "fixtures"
    contract["success_criteria"] = contract["success_criteria"][:3]

    def failed(command: str, root: Path, timeout: float) -> Execution:
        return Execution(1, "AssertionError: broken health payload")

    verdict = check_contract(contract, fixtures / "ws_claimed", fixtures / "transcript_claimed.jsonl", 1, failed)
    assert verdict["overall"] == "fail"
    assert all(item["status"] == "fail" and item["reason"] == "claimed_without_evidence"
               for item in verdict["items"])
    assert all("AssertionError" in item["evidence"] for item in verdict["items"])


def test_no_false_done_for_unverifiable_or_pass(contract: dict[str, Any], workspace: Path, transcript: Path) -> None:
    contract["success_criteria"] = contract["success_criteria"][:2]

    def runner(command: str, root: Path, timeout: float) -> Execution:
        return Execution(0) if "py_compile" in command else Execution(error="missing dependency")

    verdict = check_contract(contract, workspace, transcript, 1, runner)
    assert [item["status"] for item in verdict["items"]] == ["pass", "unverifiable"]
    assert all(item["reason"] != "claimed_without_evidence" for item in verdict["items"])


@pytest.mark.parametrize("report", ["SC-1 done. SC-3 is pending.", "SC-1 done. All done except SC-3."])
def test_unclaimed_failure_keeps_mechanical_reason(
    contract: dict[str, Any], workspace: Path, report: str,
) -> None:
    contract["success_criteria"] = [
        {"id": identifier, "description": "Required file", "check": {
            "type": "file_exists", "path": "absent"}}
        for identifier in ("SC-1", "SC-3")
    ]
    transcript = workspace / "claims.jsonl"
    transcript.write_text(json.dumps(report_record(report)))
    verdict = check_contract(contract, workspace, transcript, 1)
    assert [item["status"] for item in verdict["items"]] == ["fail", "fail"]
    assert [item["reason"] for item in verdict["items"]] == [
        "claimed_without_evidence", "required file is missing",
    ]
