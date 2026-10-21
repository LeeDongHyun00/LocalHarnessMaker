from __future__ import annotations

from itertools import product
import os
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


def test_unverifiable_items_receive_feedback() -> None:
    criteria, items = inputs()
    for item in items:
        item["status"] = "unverifiable"
    message = reinstruct(criteria, items, 1, 3)
    assert message is not None and len(message) <= 300
    assert message.startswith("Items 1 and 2 and 3 are not done.")
    assert "2 more failed items" in message


def test_every_status_mix_retries_until_exhaustion() -> None:
    criteria, items = inputs()
    for statuses in product(("pass", "fail", "unverifiable"), repeat=len(items)):
        for item, status in zip(items, statuses):
            item["status"] = status
        overall = "pass" if all(status == "pass" for status in statuses) else "fail"
        for attempt in (1, 2):
            message = reinstruct(criteria, items, attempt, 3)
            if overall == "fail":
                assert message is not None and 0 < len(message) <= 300
                numbers = [n for n, status in enumerate(statuses, 1) if status != "pass"]
                assert message.startswith("Items " + " and ".join(map(str, numbers[:3])) + " are not done.")
            else:
                assert message is None
        assert reinstruct(criteria, items, 3, 3) is None


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


def test_unset_max_attempts_defaults_to_three(
    contract: dict[str, Any], workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("HARNESS_MAX_ATTEMPTS", "HARNESS_BACKEND"):
        monkeypatch.delenv(name, raising=False)
        assert name not in os.environ
    contract["success_criteria"] = [{"id": "SC-1", "description": "Missing file", "check": {
        "type": "file_exists", "path": "absent"}}]
    for attempt in (1, 2, 3, 4):
        verdict = check_contract(contract, workspace, transcript, attempt)
        assert verdict["overall"] == "fail"
        assert (verdict["reinstruct_message"] is not None) == (attempt < 3)
