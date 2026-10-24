"""Calibration scoring and previews, with no live calls."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from controller.measure_v3 import FIXTURES, main, measure, score
from controller.settings import load_object
from controller.v3_wire import CLAIMS, REQUIREMENTS
from jsonschema import Draft202012Validator


def gold(phase: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = load_object(FIXTURES / ("requirements.json" if phase == "requirements" else "claim-audit.json"))["cases"]
    predictions = {}
    for case in cases:
        if phase == "requirements":
            predictions[case["id"]] = {"requirements": copy.deepcopy(case["expected_rows"]), "open_questions": [
                {"text": question["text"], "requirement_numbers": question["requirement_numbers"]}
                for question in case["expected_questions"]]}
        else:
            predictions[case["id"]] = {"claims": case["expected_claims"]}
    return cases, predictions


@pytest.mark.parametrize("phase", ["requirements", "claim_audit"])
def test_fixtures_and_gold_roundtrip(phase: str) -> None:
    cases, predictions = gold(phase)
    assert len(cases) == 40
    assert sum("eval/tasks/" in case["source"]["path"] for case in cases) == 20
    assert sum("eval/tasks-v2/" in case["source"]["path"] for case in cases) == 20
    for case in cases:
        assert case["source"]["path"].endswith("/prompt.md")
        assert len(case["source"]["sha256"]) == 64
        for row in case["expected_rows"]:
            assert row["source_excerpt"] in case["request"]
        Draft202012Validator(REQUIREMENTS if phase == "requirements" else CLAIMS).validate(predictions[case["id"]])
    result = score(cases, predictions, phase)
    assert result["schema_valid"] == 40
    for metric in result["metrics"].values():
        assert metric["precision"] == metric["recall"] == 1
        assert metric["false_positive"] == metric["false_negative"] == 0


def test_scoring_misses_duplicates_and_question_false_positives() -> None:
    cases, predictions = gold("requirements")
    selected = cases[:2]
    response = predictions[selected[0]["id"]]
    original = len(response["requirements"])
    response["requirements"].append(response["requirements"][0].copy())
    response["open_questions"] = [{"text": "Which unnecessary question?", "requirement_numbers": []}]
    predictions.pop(selected[1]["id"])
    result = score(selected, predictions, "requirements")
    assert result["schema_valid"] == 1
    assert result["metrics"]["rows"]["true_positive"] == original
    assert result["metrics"]["rows"]["false_positive"] == 1
    assert result["metrics"]["rows"]["false_negative"] == len(selected[1]["expected_rows"])
    assert result["metrics"]["open_questions"]["precision"] == 0
    assert result["metrics"]["open_questions"]["recall"] == 0


@pytest.mark.parametrize("phase", ["requirements", "claim-audit"])
def test_preview_never_calls(tmp_path: Path, phase: str, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "out.json"
    assert main(["--phase", phase, "--out", str(output)]) == 1
    captured = capsys.readouterr()
    assert "40 maximum provider calls" in captured.err
    assert "0.048000" in captured.err and "No calls" in captured.err
    assert not output.exists()


def test_score_saved_predictions_has_no_model_quality_claim(tmp_path: Path) -> None:
    _, predictions = gold("requirements")
    source = tmp_path / "predictions.json"
    source.write_text(json.dumps(predictions))
    output = tmp_path / "score.json"
    assert main(["--phase", "requirements", "--predictions", str(source), "--out", str(output)]) == 0
    result = load_object(output)
    assert result["measurement"] == "supplied_predictions"
    assert result["model"] is None and result["total_usd"] is None and result["calls"] == []
