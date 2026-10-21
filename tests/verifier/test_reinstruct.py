from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from verifier.check import check_contract
from verifier.reinstruct import reinstruct


def inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    criteria = [{"id": f"SC-{n}", "description": f"description {n}"} for n in range(1, 6)]
    items = [{"id": c["id"], "status": "fail" if n in {3, 5} else "pass",
              "reason": f"reason {n}", "evidence": f"command {n}\nerror: failure {n}"}
             for n, c in enumerate(criteria, 1)]
    return criteria, items


def test_only_failed_items_and_one_line_evidence() -> None:
    criteria, items = inputs()
    message = reinstruct(criteria, items, 1, 3)
    assert message is not None and len(message) <= 300
    assert message.startswith("Items 3 and 5 are not done.")
    for n in (3, 5):
        assert f"{n}. description {n}: error: failure {n}" in message
    for n in (1, 2, 4):
        assert f"description {n}" not in message and f"failure {n}" not in message


@pytest.mark.parametrize("attempt", [3, 4, 100])
def test_retry_exhaustion(attempt: int) -> None:
    assert reinstruct(*inputs(), attempt, 3) is None


def test_pass_and_unverifiable_are_not_failed_feedback() -> None:
    criteria, items = inputs()
    for item in items:
        item["status"] = "unverifiable"
    assert reinstruct(criteria, items, 1, 3) is None


def test_long_feedback_stays_bounded() -> None:
    criteria, items = inputs()
    for c, item in zip(criteria, items):
        c["description"] = "long description " * 100
        item.update(status="fail", evidence="failure evidence\n" * 100)
    message = reinstruct(criteria, items, 1, 3)
    assert message is not None and len(message) <= 300
    assert "2 more failed items" in message
    assert len(message.splitlines()) == 5


@pytest.mark.parametrize(("limit", "attempt", "has_message"), [("2", 1, True), ("2", 2, False), ("1", 1, False)])
def test_shared_environment_limit(contract: dict[str, Any], workspace: Path, transcript: Path,
                                  monkeypatch: pytest.MonkeyPatch, limit: str, attempt: int,
                                  has_message: bool) -> None:
    monkeypatch.setenv("HARNESS_MAX_ATTEMPTS", limit)
    contract["success_criteria"] = [{"id": "SC-1", "description": "Missing file",
                                      "check": {"type": "file_exists", "path": "missing"}}]
    verdict = check_contract(contract, workspace, transcript, attempt)
    assert (verdict["reinstruct_message"] is not None) == has_message


@pytest.mark.parametrize("limit", ["0", "-1", "invalid"])
def test_invalid_limit_before_execution(contract: dict[str, Any], workspace: Path, transcript: Path,
                                        monkeypatch: pytest.MonkeyPatch, limit: str) -> None:
    monkeypatch.setenv("HARNESS_MAX_ATTEMPTS", limit)
    with pytest.raises(ValueError):
        check_contract(contract, workspace, transcript, 1)
