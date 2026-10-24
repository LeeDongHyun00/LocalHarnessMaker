"""Validate the proposed hook artifacts without executing embedded commands."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
import pytest
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
NEW = ["requirements", "completion-report", "ledger", "pin-check", "luna-call"]


def load(path: str) -> dict[str, Any]:
    return json.loads((SCHEMAS / path).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    registry = Registry().with_resources(
        (path.name, Resource.from_contents(json.loads(path.read_text())))
        for path in SCHEMAS.glob("*.schema.json")
    )
    return Draft202012Validator(load(f"{name}.schema.json"), registry=registry,
                               format_checker=FormatChecker())


@pytest.mark.parametrize("name", NEW)
def test_proposed_artifacts_are_closed_and_required(name: str, tmp_path: Path) -> None:
    sample = load(f"examples/{name}.json")
    check = validator(name)
    check.validate(sample)
    assert not check.is_valid({**sample, "unexpected": True})
    for field in sample:
        invalid = copy.deepcopy(sample)
        invalid.pop(field)
        assert not check.is_valid(invalid), field
    spec = importlib.util.spec_from_file_location("v3_validation", ROOT / "docs/validate_schemas.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for omitted in [f"{name}.schema.json", f"{name}.json"]:
        directory = tmp_path / omitted
        shutil.copytree(SCHEMAS, directory, ignore=lambda _path, names: [n for n in names if n == omitted])
        with pytest.raises(ValueError, match="Missing required"):
            module.validate_tree(directory)


@pytest.mark.parametrize("kind,check", [
    ("protected_file", {"type": "file_exists", "path": "settings.json"}),
    ("named_file", {"type": "command", "argv": ["true"], "cwd": ".", "expected_exit_code": 0, "origin": "request"}),
    ("behavior", {"type": "llm_judge", "rubric": "looks correct"}),
    ("constraint", {"type": "regex", "path": "app.py", "pattern": ".*"}),
    ("test_command", {"type": "command", "command": "pytest"}),
])
def test_requirement_kinds_cannot_smuggle_in_incompatible_checks(kind: str, check: dict[str, Any]) -> None:
    sample = load("examples/requirements.json")
    sample["requirements"][0].update(kind=kind, check=check)
    assert not validator("requirements").is_valid(sample)


@pytest.mark.parametrize("mutation", ["empty", "unanswered", "missing_call", "fake_kind", "bad_id", "bad_hash"])
def test_ready_requirements_reject_missing_provenance_and_ambiguity(mutation: str) -> None:
    sample = load("examples/requirements.json")
    if mutation == "empty":
        sample["requirements"] = []
    elif mutation == "unanswered":
        sample["open_questions"] = [{"id": "Q-1", "text": "Which behavior?", "requirement_ids": ["R-1"], "answer": None}]
    elif mutation == "missing_call":
        sample["luna_call"] = None
    elif mutation == "fake_kind":
        sample["requirements"][0]["kind"] = "judge"
    elif mutation == "bad_id":
        sample["requirements"][0]["id"] = "R-0"
    else:
        sample["prompt"]["sha256"] = "not-a-hash"
    assert not validator("requirements").is_valid(sample)


def test_unanswered_question_is_explicitly_pending() -> None:
    sample = load("examples/requirements.json")
    sample.update(state="pending_questions", open_questions=[{
        "id": "Q-1", "text": "Accept subclasses?", "requirement_ids": ["R-1"], "answer": None,
    }])
    validator("requirements").validate(sample)
    sample["open_questions"][0]["answer"] = "Yes."
    assert not validator("requirements").is_valid(sample)
    sample["state"] = "ready"
    validator("requirements").validate(sample)


@pytest.mark.parametrize("mutation", ["second_retry", "round_without_retry", "retry_without_failure", "unsupported_pass", "missing_audit_source", "stale_without_reason", "repeat_failure_without_advice"])
def test_completion_report_rejects_unsupported_evidence_and_retry_states(mutation: str) -> None:
    sample = load("examples/completion-report.json")
    if mutation == "second_retry":
        sample["retry"]["used"] = 2
    elif mutation == "round_without_retry":
        sample["check_round"] = 2
    elif mutation == "retry_without_failure":
        sample["retry"].update(used=1, reason="Fix check")
    elif mutation == "unsupported_pass":
        sample["items"][0]["status"] = "pass"
    elif mutation == "missing_audit_source":
        sample["claim_audit"]["audited_final_message"] = None
    elif mutation == "stale_without_reason":
        sample["claim_audit"]["status"] = "stale"
    else:
        sample["check_round"] = 2
        sample["retry"].update(used=1, failed_requirement_ids=["R-6"], reason="Executed tests failed.")
        sample["items"][-1]["status"] = "fail"
    assert not validator("completion-report").is_valid(sample)


def test_stale_audit_retains_its_source_after_single_repair() -> None:
    sample = load("examples/completion-report.json")
    sample["check_round"] = 2
    sample["retry"].update(used=1, failed_requirement_ids=["R-6"], reason="Executed tests failed.")
    sample["current_final_message"] = {"path": "evidence/final-2.txt", "sha256": "b" * 64}
    sample["claim_audit"].update(status="stale", reason="Executor final message changed after repair.")
    validator("completion-report").validate(sample)
    assert sample["claim_audit"]["audited_final_message"] != sample["current_final_message"]


@pytest.mark.parametrize("mutation", ["model", "effort", "bad_status", "negative_tokens", "negative_latency", "errorless_failure"])
def test_control_accounting_rejects_wrong_pin_and_invalid_usage(mutation: str) -> None:
    sample = load("examples/luna-call.json")
    field, value = {
        "model": ("model", "another-model"), "effort": ("reasoning_effort", "medium"),
        "bad_status": ("status", "ignored"), "negative_tokens": ("input_tokens", -1),
        "negative_latency": ("latency_seconds", -0.1), "errorless_failure": ("status", "timeout"),
    }[mutation]
    sample[field] = value
    assert not validator("luna-call").is_valid(sample)


def test_failed_call_and_pin_mismatch_keep_actual_identity_and_unknown_cost() -> None:
    sample = load("examples/luna-call.json")
    sample.update(status="pin_mismatch", model="different-model", error="Provider identity differs from pin.")
    validator("luna-call").validate(sample)
    assert sample["usd"] is None and sample["input_tokens"] is None
    sample.update(status="timeout", model=None, error="Deadline exceeded.")
    validator("luna-call").validate(sample)


@pytest.mark.parametrize("field", ["codex_version_verified", "model_listed", "pricing_covered"])
def test_enabled_pin_requires_all_three_observed_checks(field: str) -> None:
    sample = load("examples/pin-check.json")
    sample["checks"][field] = False
    assert not validator("pin-check").is_valid(sample)
    sample.update(status="disabled", reason_codes=["model_missing"], advisory="Pinned hooks disabled.")
    validator("pin-check").validate(sample)


def test_executor_ledger_and_invalid_validation_are_representable_but_not_valid_injection() -> None:
    sample = load("examples/ledger.json")
    sample["validation"] = None
    validator("ledger").validate(sample)
    sample = load("examples/ledger.json")
    sample["validation"]["identifiers"][0].update(found=False, sha256=None)
    assert not validator("ledger").is_valid(sample)
    sample["validation"].update(status="invalid", reason="Identifier absent.")
    validator("ledger").validate(sample)


def test_direction_and_schema_set_are_approved_and_frozen() -> None:
    decision = (ROOT / "docs/decisions/0011-pinned-luna-hook-direction.md").read_text()
    assert "Status: accepted by the user on 2026-10-25" in decision
    assert "01:55 KST" in decision
    assert "d82b87a" in decision
    assert "and frozen" in decision
    plan = (ROOT / "docs/plan.md").read_text()
    assert "resolved, accepted by the user on 2026-10-25" in plan
    assert "record-only after 0011" in plan
    for name in ["AGENTS.md", "docs/interfaces-v3.md", *[f"prompts/{n}" for n in [
        "01-tech-lead.md", "02-plugin-engineer.md", "03-controller-engineer.md",
        "04-verifier-engineer.md", "05-eval-engineer.md",
    ]]]:
        content = (ROOT / name).read_text()
        assert "frozen" in content.lower(), name
        assert "01:55 KST" in content, name
    # The old report schema is deliberately not relabeled as interface v3.
    assert "Interface version 2" in load("evaluation-report.schema.json")["description"]
