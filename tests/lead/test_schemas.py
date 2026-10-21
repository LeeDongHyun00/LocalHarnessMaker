"""Regression coverage for shared interface validation and reference samples."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
spec = importlib.util.spec_from_file_location("validate_schemas", ROOT / "docs/validate_schemas.py")
assert spec is not None and spec.loader is not None
validator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator_module)


def load(path: str) -> Any:
    """Read a schema or sample relative to schemas/."""
    return json.loads((SCHEMAS / path).read_text(encoding="utf-8"))


def contract_with(check: dict[str, Any]) -> dict[str, Any]:
    """Replace one criterion check without changing the remaining contract."""
    contract = load("examples/contract.json")
    contract["success_criteria"][0]["check"] = check
    return contract


def test_all_schemas_and_examples_validate() -> None:
    assert validator_module.validate_tree() == (6, 8)


@pytest.mark.parametrize("check", [
    {"type": "command", "command": "python -m pytest", "expected": {"exit_code": 0}},
    {"type": "file_exists", "path": "app/main.py"},
    {"type": "regex", "path": "app/main.py", "pattern": "health"},
    {"type": "llm_judge", "rubric": "Existing behavior is preserved."},
])
def test_exactly_four_supported_check_variants(check: dict[str, Any]) -> None:
    Draft202012Validator(load("contract.schema.json")).validate(contract_with(check))


@pytest.mark.parametrize("check", [
    {"type": "shell", "command": "true", "expected": {"exit_code": 0}},
    {"type": "command", "command": "true"},
    {"type": "command", "command": "true", "expected": 0},
    {"type": "command", "command": "true", "expected": {"stdout": ""}},
    {"type": "file_exists"},
    {"type": "file_exists", "path": "app/main.py", "pattern": "health"},
    {"type": "regex", "path": "app/main.py"},
    {"type": "llm_judge"},
    {"type": "llm_judge", "rubric": "Review", "command": "true"},
])
def test_unknown_incomplete_and_mixed_checks_are_rejected(check: dict[str, Any]) -> None:
    assert not Draft202012Validator(load("contract.schema.json")).is_valid(contract_with(check))


def test_expected_stdout_is_optional_but_must_be_a_string() -> None:
    check = {"type": "command", "command": "true", "expected": {"exit_code": 0, "stdout": 42}}
    assert not Draft202012Validator(load("contract.schema.json")).is_valid(contract_with(check))


@pytest.mark.parametrize("field", ["assumptions", "reasoning_effort", "cost_estimate"])
def test_contract_requires_assumptions_and_code_computed_fields(field: str) -> None:
    contract = load("examples/contract.json")
    contract.pop(field)
    assert not Draft202012Validator(load("contract.schema.json")).is_valid(contract)


def test_empty_and_all_judge_contracts_can_reach_runtime_quality_checks() -> None:
    contract = load("examples/contract.json")
    validator = Draft202012Validator(load("contract.schema.json"))
    contract["success_criteria"] = [contract["success_criteria"][-1]]
    validator.validate(contract)
    contract["success_criteria"] = []
    validator.validate(contract)


@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
def test_supported_reasoning_efforts(effort: str) -> None:
    contract = load("examples/contract.json")
    contract["reasoning_effort"]["value"] = effort
    Draft202012Validator(load("contract.schema.json")).validate(contract)


@pytest.mark.parametrize("section,field,value", [
    ("reasoning_effort", "value", "none"),
    ("cost_estimate", "input_tokens", -1),
    ("cost_estimate", "output_tokens", 1.5),
    ("cost_estimate", "usd", -0.01),
])
def test_invalid_effort_and_usage_are_rejected(section: str, field: str, value: Any) -> None:
    contract = load("examples/contract.json")
    contract[section][field] = value
    assert not Draft202012Validator(load("contract.schema.json")).is_valid(contract)


@pytest.mark.parametrize("status", ["fail", "unverifiable"])
def test_nonpassing_items_cannot_produce_an_overall_pass(status: str) -> None:
    verdict = load("examples/verdict_pass.json")
    verdict["items"][0]["status"] = status
    assert not Draft202012Validator(load("verdict.schema.json")).is_valid(verdict)


def test_verdict_overall_and_retry_message_consistency() -> None:
    validator = Draft202012Validator(load("verdict.schema.json"))
    passed = load("examples/verdict_pass.json")
    passed["overall"] = "fail"
    assert not validator.is_valid(passed)
    passed = load("examples/verdict_pass.json")
    passed["reinstruct_message"] = "Continue"
    assert not validator.is_valid(passed)
    failed = load("examples/verdict_fail.json")
    failed["reinstruct_message"] = None
    validator.validate(failed)
    failed["reinstruct_message"] = "x" * 301
    assert not validator.is_valid(failed)
    failed["reinstruct_message"] = None
    failed["attempt"] = 0
    assert not validator.is_valid(failed)


@pytest.mark.parametrize("name,sample", [
    ("contract", "contract"), ("verdict", "verdict_pass"), ("handoff", "handoff"),
])
def test_unknown_fields_are_rejected(name: str, sample: str) -> None:
    artifact = load(f"examples/{sample}.json")
    artifact["unexpected"] = True
    assert not Draft202012Validator(load(f"{name}.schema.json")).is_valid(artifact)


def test_reference_task_and_handoff_are_consistent() -> None:
    contract = load("examples/contract.json")
    criteria = contract["success_criteria"]
    ids = [item["id"] for item in criteria]
    assert len(ids) == len(set(ids))
    assert [item["check"]["type"] for item in criteria].count("command") == 3
    assert [item["check"]["type"] for item in criteria].count("llm_judge") == 1
    commands = [{key: value for key, value in item["check"].items() if key != "type"}
                for item in criteria if item["check"]["type"] == "command"]
    assert contract["verification"] == commands
    assert isinstance(load("examples/prompt.json"), str)
    failed = load("examples/verdict_fail.json")
    passed = load("examples/verdict_pass.json")
    assert [item["id"] for item in failed["items"]] == ids
    assert [item["id"] for item in passed["items"]] == ids
    assert passed["attempt"] == failed["attempt"] + 1
    handoff = load("examples/handoff.json")
    assert {item["criterion_id"] for item in handoff["done"]} == {item["id"] for item in failed["items"] if item["status"] == "pass"}
    assert {item["criterion_id"] for item in handoff["remaining"]} == {item["id"] for item in failed["items"] if item["status"] != "pass"}
    assert handoff["verify_commands"] == [item["command"] for item in commands]
    assert all("SYNTHETIC" in item["evidence"] for verdict in [passed, failed] for item in verdict["items"])


@pytest.mark.parametrize("mutation", ["missing_schema", "missing_example", "unmapped_example", "invalid_example", "invalid_schema", "wrong_draft"])
def test_validation_fails_for_incomplete_or_invalid_trees(tmp_path: Path, mutation: str) -> None:
    directory = tmp_path / "schemas"
    # Omit files while copying rather than deleting repository artifacts.
    omitted = {"missing_schema": "handoff.schema.json", "missing_example": "prompt.json"}.get(mutation)
    shutil.copytree(SCHEMAS, directory, ignore=lambda _path, names: [name for name in names if name == omitted])
    if mutation == "unmapped_example":
        (directory / "examples/unmapped.json").write_text("{}", encoding="utf-8")
    elif mutation == "invalid_example":
        (directory / "examples/contract.json").write_text("{}", encoding="utf-8")
    elif mutation in {"invalid_schema", "wrong_draft"}:
        schema = copy.deepcopy(load("handoff.schema.json"))
        schema["type" if mutation == "invalid_schema" else "$schema"] = "invalid"
        (directory / "handoff.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(ValueError):
        validator_module.validate_tree(directory)


@pytest.mark.parametrize("missing", ["judgment-input.schema.json", "judgment.schema.json", "evaluation-report.schema.json"])
def test_new_schemas_cannot_be_silently_omitted(tmp_path: Path, missing: str) -> None:
    directory = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, directory, ignore=lambda _path, names: [name for name in names if name == missing])
    with pytest.raises(ValueError, match="Missing required shared schema"):
        validator_module.validate_tree(directory)


@pytest.mark.parametrize("name", ["criterion.json", "judgment.json", "evaluation_report.json"])
def test_new_examples_are_required_and_validated(tmp_path: Path, name: str) -> None:
    missing = tmp_path / "missing"
    shutil.copytree(SCHEMAS, missing, ignore=lambda _path, names: [item for item in names if item == name])
    with pytest.raises(ValueError, match="Missing required reference sample"):
        validator_module.validate_tree(missing)
    invalid = tmp_path / "invalid"
    shutil.copytree(SCHEMAS, invalid)
    (invalid / "examples" / name).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        validator_module.validate_tree(invalid)


@pytest.mark.parametrize("timestamp", ["not-a-date", "2026-02-30T12:00:00Z", "2026-10-21T12:00:00", "2026-10-21T12:00:00+01:60"])
def test_report_example_datetime_formats_are_checked(tmp_path: Path, timestamp: str) -> None:
    directory = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, directory)
    report = load("examples/evaluation_report.json")
    report["metadata"]["created_at"] = timestamp
    (directory / "examples/evaluation_report.json").write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="date-time"):
        validator_module.validate_tree(directory)


def test_missing_schema_reference_fails_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def reject_network(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Schema validation must not open network connections")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    directory = tmp_path / "schemas"
    shutil.copytree(SCHEMAS, directory)
    criterion_schema = load("judgment-input.schema.json")
    criterion_schema["allOf"][0]["$ref"] = "https://invalid.example/unregistered-schema.json"
    (directory / "judgment-input.schema.json").write_text(json.dumps(criterion_schema), encoding="utf-8")
    with pytest.raises(ValueError, match="Unresolvable"):
        validator_module.validate_tree(directory)
