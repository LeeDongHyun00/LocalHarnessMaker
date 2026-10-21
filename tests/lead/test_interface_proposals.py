"""Check published interfaces and the approved records without model calls."""

from __future__ import annotations

import copy
from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
import pytest
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "docs/decisions"
JUDGE = DECISIONS / "0002-judgment-schema-proposal.md"
REPORT = DECISIONS / "0003-evaluation-report-schema-proposal.md"
BACKEND = DECISIONS / "0004-codex-cli-backend-and-nested-guard-proposal.md"


def json_blocks(path: Path) -> list[dict[str, Any]]:
    """Read embedded JSON without treating Markdown prose as executable code."""
    return [json.loads(value) for value in re.findall(r"```json\n(.*?)\n```", path.read_text(), re.DOTALL)]


def judgment_fixtures() -> list[dict[str, Any]]:
    """Load the published input/output contracts and examples."""
    names = ["judgment-input.schema.json", "judgment.schema.json",
             "examples/criterion.json", "examples/judgment.json"]
    return [json.loads((ROOT / "schemas" / name).read_text()) for name in names]


def report_fixtures() -> list[dict[str, Any]]:
    """Load the published report contract and example."""
    return [json.loads((ROOT / "schemas" / name).read_text())
            for name in ["evaluation-report.schema.json", "examples/evaluation_report.json"]]


def report_validator() -> Draft202012Validator:
    return Draft202012Validator(report_fixtures()[0], format_checker=FormatChecker())


def test_published_schema_definitions_and_examples() -> None:
    input_schema, output_schema, criterion, judgment = judgment_fixtures()
    report_schema, example = report_fixtures()
    for schema in [input_schema, output_schema, report_schema]:
        Draft202012Validator.check_schema(schema)
    contract = json.loads((ROOT / "schemas/contract.schema.json").read_text())
    registry = Registry().with_resource("contract.schema.json", Resource.from_contents(contract))
    input_validator = Draft202012Validator(input_schema, registry=registry)
    input_validator.validate(criterion)
    for invalid in [[criterion], {"success_criteria": [criterion]}, {"check": criterion["check"]},
                    {**criterion, "extra": True}]:
        assert not input_validator.is_valid(invalid)
    mechanical = copy.deepcopy(criterion)
    mechanical["check"] = {"type": "file_exists", "path": "app/main.py"}
    assert not input_validator.is_valid(mechanical)
    Draft202012Validator(output_schema).validate(judgment)
    report_validator().validate(example)
    assert output_schema["$defs"]["usage"] == report_schema["$defs"]["usage"]


@pytest.mark.parametrize("status", ["pass", "fail", "unverifiable"])
def test_judgment_uses_verdict_status_vocabulary(status: str) -> None:
    _, schema, _, judgment = judgment_fixtures()
    judgment["status"] = status
    Draft202012Validator(schema).validate(judgment)


@pytest.mark.parametrize("field,value", [("status", "unknown"), ("criterion_id", ""), ("model", "")])
def test_invalid_judgment_identity_and_status_are_rejected(field: str, value: Any) -> None:
    _, schema, _, judgment = judgment_fixtures()
    judgment[field] = value
    assert not Draft202012Validator(schema).is_valid(judgment)


@pytest.mark.parametrize("field", ["input_tokens", "cached_input_tokens", "output_tokens", "usd"])
def test_unknown_judgment_accounting_is_nullable(field: str) -> None:
    _, schema, _, judgment = judgment_fixtures()
    judgment["usage"][field] = None
    Draft202012Validator(schema).validate(judgment)
    judgment["usage"][field] = -1
    assert not Draft202012Validator(schema).is_valid(judgment)


@pytest.mark.parametrize("field", ["criterion_id", "status", "reason", "evidence", "model", "usage", "extra"])
def test_judgment_requires_exactly_the_six_fields(field: str) -> None:
    _, schema, _, judgment = judgment_fixtures()
    if field == "extra":
        judgment[field] = True
    else:
        judgment.pop(field)
    assert not Draft202012Validator(schema).is_valid(judgment)


@pytest.mark.parametrize("mutation", ["extra_field", "negative_cost", "negative_count", "wrong_unit", "missing_reasons", "invalid_grading"])
def test_report_rejects_malformed_accounting_and_invalidity(mutation: str) -> None:
    _, example = report_fixtures()
    task = example["tasks"][0]
    if mutation == "extra_field":
        example["extra"] = True
    elif mutation == "negative_cost":
        task["costs"]["total_usd"] = -1
    elif mutation == "negative_count":
        task["done_claims"]["claimed_items"] = -1
    elif mutation == "wrong_unit":
        example["metrics"]["pass_rate"]["sample_unit"] = "claimed_criterion"
    else:
        task["outcome"] = "invalid"
        task["grading"] = None
        task["invalid_reasons"] = [] if mutation == "missing_reasons" else ["Synthetic mismatch"]
        example["validity"] = {"status": "invalid", "reasons": ["Synthetic mismatch"]}
        if mutation == "invalid_grading":
            task["grading"] = report_fixtures()[1]["tasks"][0]["grading"]
    assert not report_validator().is_valid(example)


@pytest.mark.parametrize("name", ["pass_rate", "false_done_rate", "cost_per_pass", "avg_attempts", "handoff_success", "parity"])
def test_report_requires_each_metric_and_95_percent_interval(name: str) -> None:
    _, example = report_fixtures()
    invalid = copy.deepcopy(example)
    invalid["metrics"].pop(name)
    assert not report_validator().is_valid(invalid)
    invalid = copy.deepcopy(example)
    invalid["metrics"][name]["ci95"]["level"] = 0.90
    assert not report_validator().is_valid(invalid)


@pytest.mark.parametrize("status", ["access_detected", "inconclusive"])
def test_audit_failure_cannot_be_a_valid_pass(status: str) -> None:
    _, example = report_fixtures()
    task = example["tasks"][0]
    task["grader_access_audit"]["status"] = status
    task["grader_access_audit"]["reason"] = "Synthetic audit failure"
    if status == "access_detected":
        task["grader_access_audit"]["matches"] = [{
            "event_log": "events/synthetic-feature-1.jsonl", "line": 4, "tool": "exec_command",
            "path": "/private-eval-fixture/graders", "operation": "read", "evidence": "SYNTHETIC read attempt"}]
    assert not report_validator().is_valid(example)
    task["outcome"] = "invalid"
    task["invalid_reasons"] = ["Synthetic audit failure"]
    task["grading"] = None
    # Check this task only: report-level aggregates require runtime recomputation.
    schema = report_fixtures()[0]
    task_schema = {"$schema": schema["$schema"], "$ref": "#/$defs/task", "$defs": schema["$defs"]}
    Draft202012Validator(task_schema).validate(task)


def test_report_does_not_present_unknown_metrics_as_zero() -> None:
    _, example = report_fixtures()
    metric = example["metrics"]["parity"]
    assert metric["sample_size"] == 0 and metric["value"] is None
    metric["value"] = 0
    assert not report_validator().is_valid(example)


def test_invalid_task_marks_aggregate_report_invalid() -> None:
    _, example = report_fixtures()
    task = example["tasks"][0]
    task["outcome"] = "invalid"
    task["invalid_reasons"] = ["Synthetic configuration mismatch"]
    task["grading"] = None
    assert not report_validator().is_valid(example)
    example["validity"] = {"status": "invalid", "reasons": ["Synthetic configuration mismatch"]}
    # Aggregate arithmetic is deliberately a separate proposed runtime check.
    report_validator().validate(example)


def test_two_session_results_require_handoff_evidence() -> None:
    _, example = report_fixtures()
    task = example["tasks"][0]
    task["two_session"] = True
    assert not report_validator().is_valid(example)
    task["handoff"] = {"day2_pass": True, "user_restated_day1_context": False,
                       "evidence": {"path": "handoff/day-2.jsonl", "sha256": "5" * 64}}
    report_validator().validate(example)


def test_example_costs_recompute_from_synthetic_api_equivalent_rates() -> None:
    _, example = report_fixtures()
    rates = {item["model"]: item for item in example["metadata"]["pricing"]["rates"]}
    total = Decimal(0)
    for task in example["tasks"]:
        subtotal = Decimal(0)
        for call in task["calls"]:
            usage = call["usage"]
            price = rates[call["model"]]
            usd = ((usage["input_tokens"] - usage["cached_input_tokens"]) * Decimal(str(price["input_per_million_usd"]))
                   + usage["cached_input_tokens"] * Decimal(str(price["cached_input_per_million_usd"]))
                   + usage["output_tokens"] * Decimal(str(price["output_per_million_usd"]))) / 1_000_000
            assert usd == Decimal(str(usage["usd"]))
            subtotal += usd
        assert subtotal == Decimal(str(task["costs"]["total_usd"]))
        total += subtotal
    assert total == Decimal(str(example["accounting"]["total_cost_usd"]))
    assert total == Decimal(str(example["metrics"]["cost_per_pass"]["value"]))


def test_published_hook_contract_has_working_evidence_links() -> None:
    path = ROOT / "docs/hooks-contract.md"
    content = path.read_text()
    assert "Status: published by Role 1" in content
    links = re.findall(r"\]\(([^)]+)\)", content)
    evidence_links = [target for target in links if not target.startswith("https://")]
    assert evidence_links
    for target in evidence_links:
        assert target.startswith("../plugin/evidence/")
        assert (path.parent / target).resolve().is_file(), target


def test_backend_example_is_explicitly_guarded_and_uses_selected_model() -> None:
    example, = json_blocks(BACKEND)
    assert example["child_env_overrides"] == {"HARNESS_NESTED": "1"}
    argv = example["child_argv"]
    assert argv[argv.index("--model") + 1] == "gpt-6-luna"
    assert "--json" in argv and "--output-last-message" in argv
    assert example["hook_result_with_guard"] == {"exit_code": 0, "stdout": "", "stderr": ""}
    assert "--backend" in example["controller_command"]


@pytest.mark.parametrize("path", [JUDGE, REPORT, BACKEND])
def test_each_proposal_has_review_requirements(path: Path) -> None:
    content = path.read_text()
    assert "## Assumptions" in content
    assert "affected roles" in content.lower()
    assert "## Tests to add after approval" in content
    assert json_blocks(path)


def test_published_artifacts_match_approved_records() -> None:
    assert judgment_fixtures() == json_blocks(JUDGE)
    assert report_fixtures() == json_blocks(REPORT)
    assert (ROOT / "schemas/VERSION").read_text().strip() == "1"
    for path in [JUDGE, REPORT, BACKEND]:
        assert "Status: approved by the user on 2026-10-21" in path.read_text()


def test_cli_table_and_authorized_role_prompts_match_version_one() -> None:
    interfaces = (ROOT / "docs/interfaces.md").read_text()
    rows = [line for line in interfaces.splitlines() if line.startswith("| `python -m ")]
    assert len(rows) == 6
    assert all("codex_cli_OR_cheap_api_OR_local" in row for row in rows[:3])
    assert "judgment-input.schema.json" in rows[2] and "judgment.schema.json" in rows[2]
    assert "evaluation-report.schema.json" in rows[5]
    for name in ["AGENTS.md", "docs/interfaces.md", "prompts/03-controller-engineer.md",
                 "prompts/05-eval-engineer.md"]:
        content = (ROOT / name).read_text()
        assert "gpt-6-luna" in content and "codex_cli" in content
        assert "HARNESS_NESTED=1" in content
        assert "API-equivalent" in content
    evaluation_prompt = (ROOT / "prompts/05-eval-engineer.md").read_text()
    assert "access audit" in evaluation_prompt
    assert "hidden_tests/ (never visible" not in evaluation_prompt
