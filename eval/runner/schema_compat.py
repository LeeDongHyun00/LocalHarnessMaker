"""Validate retained reports by the metric-presence version declared in 0009."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def report_version(report: dict[str, Any]) -> int:
    """The approved interface declares its version by the required metric entry."""
    return 2 if "task_false_done_rate" in report.get("metrics", {}) else 1


def validate_schema(report: dict[str, Any], repository: Path) -> None:
    """Undo exactly the two v2 additions to reconstruct the original v1 schema."""
    schema = json.loads((repository / "schemas/evaluation-report.schema.json").read_text())
    if report_version(report) == 1:
        metrics = schema["properties"]["metrics"]
        metrics["required"].remove("task_false_done_rate")
        metrics["properties"].pop("task_false_done_rate")
        schema["$defs"]["metric"]["properties"]["sample_unit"]["enum"].remove("claimed_complete_task")
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)
