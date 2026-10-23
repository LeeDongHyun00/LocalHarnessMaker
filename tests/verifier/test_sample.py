"""Synthetic report fixtures need no grading copies, graders or executor runs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import pytest

from verifier.__main__ import main
from verifier.sample import OUTPUT_NAME, SampleInputError, sample_report
from verifier.schema import validate


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def report_factory(tmp_path: Path) -> Callable[..., tuple[Path, dict[str, Any]]]:
    template = json.loads((ROOT / "schemas/examples/evaluation_report.json").read_text())

    def make(types: tuple[str, ...] = ("bug", "feature", "refactor"), *, attempts: int = 1,
             absolute: bool = False, name: str = "reports") -> tuple[Path, dict[str, Any]]:
        root = tmp_path / name
        root.mkdir(exist_ok=True)
        report = copy.deepcopy(template)
        report["tasks"] = []
        for index, task_type in enumerate(types):
            task = copy.deepcopy(template["tasks"][0])
            task["task_id"], task["task_type"] = f"task-{index:02}", task_type
            task["attempts"] = attempts
            task["artifacts"] = [{"path": "grading/never-read.log", "sha256": "0" * 64},
                                 {"path": "result.json", "sha256": "0" * 64}]
            task["outcome"], task["grading"]["result"] = "fail", "fail"
            task["grading"]["failed_tests"] = 1
            for attempt in range(1, attempts + 1):
                verdict = {"attempt": attempt, "overall": "pass", "reinstruct_message": None,
                           "items": [{"id": "SC-1", "status": "pass", "evidence": "exact evidence\n☃",
                                      "reason": "exact reason\nsecond line"}]}
                if attempt > 1:
                    verdict["overall"], verdict["reinstruct_message"] = "fail", "Review SC-2 and SC-3."
                    verdict["items"].extend([
                        {"id": "SC-2", "status": "fail", "evidence": "test failed", "reason": "claimed_without_evidence"},
                        {"id": "SC-3", "status": "unverifiable", "evidence": "llm_judge: unavailable", "reason": "judge timeout"},
                    ])
                path = root / task["task_id"] / f"verdict-{attempt}.json"
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(verdict) + "\n")
                task["artifacts"].append({"path": str(path) if absolute else path.relative_to(root).as_posix(),
                                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            report["tasks"].append(task)
        report["accounting"].update(attempted_tasks=len(types), valid_tasks=len(types))
        save(root, report)
        validate(report, "evaluation-report.schema.json")
        return root, report
    return make


@pytest.fixture
def retained_report(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], request: pytest.FixtureRequest,
) -> tuple[Path, dict[str, Any]]:
    """Mirror full-harness: v1 report, checkout-relative hashes, inline results.

    Also exercise retained verdict-N/day-1/day-2 files and coexistence without
    counting both copies. All content is synthetic; no host evidence is needed.
    """
    mode = getattr(request, "param", "inline")
    root, report = report_factory(attempts=2, name="full-harness")
    report["metrics"].pop("task_false_done_rate")
    for index, task in enumerate(report["tasks"]):
        listed = task["artifacts"][-2:]
        verdicts = [json.loads((root / a["path"]).read_text()) for a in listed]
        if index == 2:
            task["two_session"] = True
            task["handoff"] = {"day2_pass": False, "user_restated_day1_context": False,
                               "evidence": {"path": "unused-handoff.json", "sha256": "0" * 64}}
            # Attempt numbers restart in the second session; retain both.
            verdicts[1]["attempt"] = 1
        result = root / task["task_id"] / "result.json"
        result.write_text(json.dumps({"task_id": task["task_id"], "task_type": task["task_type"],
                                      "verdicts": verdicts, "grading": {"result": "pass"}}))
        task["artifacts"] = [{"path": f"eval/reports/full-harness/{task['task_id']}/result.json",
                              "sha256": hashlib.sha256(result.read_bytes()).hexdigest()}]
        if mode in {"standalone", "both"}:
            for number, verdict in enumerate(verdicts, 1):
                name = f"day-{number}-verdict-1.json" if index == 2 else f"verdict-{number}.json"
                path = result.parent / name
                path.write_text(json.dumps(verdict))
                task["artifacts"].append({"path": f"eval/reports/full-harness/{task['task_id']}/{name}",
                                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    save(root, report)
    return root, report


def save(root: Path, report: dict[str, Any]) -> None:
    (root / "report.json").write_text(json.dumps(report) + "\n")


@pytest.mark.parametrize("retained_report", ["inline", "standalone", "both"], indirect=True)
def test_real_retained_layout_selects_verdicts_with_report_grading(
    retained_report: tuple[Path, dict[str, Any]], tmp_path: Path,
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, report = retained_report
    output = tmp_path / "review.json"
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    original = Path.read_bytes
    allowed = {root / "report.json"} | {
        root / Path(a["path"]).relative_to("eval/reports/full-harness")
        for task in report["tasks"] for a in task["artifacts"]}

    def read(path: Path) -> bytes:
        assert path in allowed, f"unexpected evidence access: {path}"
        return original(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", read)
        assert main(["sample", "--reports", str(root), "--out", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == str(output) + "\n"
    assert captured.err == "verifier sample selected=6 available=6 seed=42\n"
    review = json.loads(output.read_text())
    assert len(review["samples"]) == review["available"] == 6
    assert len({s["task_type"] for s in review["samples"][:3]}) == 3
    for sample in review["samples"]:
        source = json.loads((root / sample["verdict_path"]).read_text())
        verdict = source["verdicts"][sample["verdict_index"]] if "verdict_index" in sample else source
        assert sample["items"] == verdict["items"]
        assert sample["attempt"] == verdict["attempt"]
        assert sample["final_grading_outcome"] == sample["task_outcome"] == "fail"
        assert sample["verdict_sha256"] == hashlib.sha256((root / sample["verdict_path"]).read_bytes()).hexdigest()
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    first = output.read_bytes()
    assert main(["sample", "--reports", str(root), "--out", str(output)]) == 0
    assert output.read_bytes() == first


@pytest.mark.parametrize("damage", ["hash", "json", "schema", "identity", "not_list", "missing"])
def test_inline_results_are_hash_and_schema_checked(
    retained_report: tuple[Path, dict[str, Any]], damage: str,
    capsys: pytest.CaptureFixture[str], tmp_path: Path,
) -> None:
    root, report = retained_report
    artifact = report["tasks"][0]["artifacts"][0]
    path = root / Path(artifact["path"]).relative_to("eval/reports/full-harness")
    result = json.loads(path.read_text())
    if damage == "schema":
        result["verdicts"][0]["items"][0]["status"] = "unknown"
    elif damage == "identity":
        result["task_id"] = "another-task"
    elif damage == "not_list":
        result["verdicts"] = {}
    path.write_text("{" if damage == "json" else json.dumps(result) + " ")
    if damage != "hash":
        artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if damage == "missing":
        artifact["path"] = "task-00/missing/result.json"
    save(root, report)
    output = tmp_path / "review.json"
    output.write_text("previous")
    assert main(["sample", "--reports", str(root), "--out", str(output)]) == 1
    assert capsys.readouterr().out == ""
    assert output.read_text() == "previous"


def test_v1_report_still_rejects_unknown_fields(retained_report: tuple[Path, dict[str, Any]]) -> None:
    root, report = retained_report
    report["metrics"]["unknown"] = report["metrics"]["pass_rate"]
    save(root, report)
    with pytest.raises(SampleInputError, match="invalid report.json"):
        sample_report(root)


@pytest.mark.parametrize("absolute", [False, True])
def test_sample_cli_exact_stdout_and_review_fields(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], absolute: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, report = report_factory(attempts=2, absolute=absolute)
    before = (root / "report.json").read_bytes()
    assert main(["sample", "--reports", str(root)]) == 0
    captured = capsys.readouterr()
    assert captured.out == str(root / OUTPUT_NAME) + "\n"
    assert captured.err == "verifier sample selected=6 available=6 seed=42\n"
    review = json.loads((root / OUTPUT_NAME).read_text())
    assert review["seed"] == 42 and review["available"] == 6 and review["requested"] == 20
    assert review["report_sha256"] == hashlib.sha256(before).hexdigest()
    assert (root / "report.json").read_bytes() == before
    for sample in review["samples"]:
        task = next(task for task in report["tasks"] if task["task_id"] == sample["task_id"])
        assert sample["task_type"] == task["task_type"]
        assert sample["attempt"] in {1, 2}
        assert sample["final_grading_outcome"] == sample["task_outcome"] == "fail"
        original = json.loads((root / sample["verdict_path"]).read_text())
        assert sample["overall"] == original["overall"]
        assert sample["items"] == original["items"]
        assert sample["verdict_sha256"] == hashlib.sha256((root / sample["verdict_path"]).read_bytes()).hexdigest()
    # An identical invocation produces byte-identical human-review output.
    first = (root / OUTPUT_NAME).read_bytes()
    assert main(["sample", "--reports", str(root)]) == 0
    assert (root / OUTPUT_NAME).read_bytes() == first


def test_seeded_rounds_spread_across_types_and_ignore_input_order(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]],
) -> None:
    root, report = report_factory(("bug",) * 9 + ("feature",) * 3 + ("refactor",), attempts=2)
    first = sample_report(root, 7)
    assert len(first["samples"]) == 7
    assert len({item["task_type"] for item in first["samples"][:3]}) == 3
    assert len({item["task_type"] for item in first["samples"][3:6]}) == 3
    for task in report["tasks"]:
        task["artifacts"].reverse()
    report["tasks"].reverse()
    report["metadata"]["seed"] = 999
    save(root, report)
    assert sample_report(root, 7)["samples"] == first["samples"]


def test_runner_prefixed_and_archived_verdict_artifacts(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]],
) -> None:
    root, report = report_factory(("bug",), attempts=2)
    destinations = ["task-00/day1-verdict-1.json",
                    "task-00/control-interruptions/aborted/day2-verdict-2.json"]
    verdicts = report["tasks"][0]["artifacts"][-2:]
    for artifact, destination in zip(verdicts, destinations):
        path = root / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((root / artifact["path"]).read_bytes())
        artifact["path"] = destination
    save(root, report)
    review = sample_report(root)
    assert review["available"] == 2  # Unlisted originals are never discovered.
    assert {sample["verdict_path"] for sample in review["samples"]} == set(destinations)
    assert {sample["attempt"] for sample in review["samples"]} == {1, 2}


def test_only_report_and_named_verdicts_are_opened(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, report = report_factory()
    allowed = {root / "report.json"} | {
        root / artifact["path"] for task in report["tasks"] for artifact in task["artifacts"]
        if "verdict-" in artifact["path"]}
    opened: set[Path] = set()
    original = Path.read_bytes

    def read(path: Path) -> bytes:
        assert path in allowed, f"unexpected evidence access: {path}"
        opened.add(path)
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    assert sample_report(root)["available"] == 3
    assert opened == allowed


@pytest.mark.parametrize("outcome", ["invalid", "timeout", "error"])
def test_missing_final_grading_is_explicit_and_does_not_hide_task_outcome(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], outcome: str,
) -> None:
    root, report = report_factory(("bug",))
    task = report["tasks"][0]
    task["outcome"], task["grading"] = outcome, None
    if outcome == "invalid":
        task["invalid_reasons"] = ["synthetic incomplete access audit"]
        task["grader_access_audit"].update(status="inconclusive", reason=task["invalid_reasons"][0])
        report["validity"] = {"status": "invalid", "reasons": task["invalid_reasons"]}
        report["accounting"].update(valid_tasks=0, invalid_tasks=1)
    save(root, report)
    sample = sample_report(root)["samples"][0]
    assert sample["task_outcome"] == outcome
    assert sample["final_grading_outcome"] is None
    assert sample["invalid_reasons"] == task["invalid_reasons"]


@pytest.mark.parametrize("damage", ["report_json", "report_schema", "report_missing", "verdict_missing",
                                    "hash", "verdict_schema", "verdict_json", "duplicate_task", "duplicate_path"])
def test_invalid_input_preserves_previous_output_and_prints_no_path(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], damage: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, report = report_factory(("bug",))
    artifact = report["tasks"][0]["artifacts"][-1]
    path = root / artifact["path"]
    if damage == "report_json":
        (root / "report.json").write_text("{")
    elif damage == "report_schema":
        report["unknown"] = True
        save(root, report)
    elif damage == "report_missing":
        root = root / "missing"
        root.mkdir()
    elif damage == "verdict_missing":
        artifact["path"] = "verdict-99.json"
        save(root, report)
    elif damage == "hash":
        path.write_text(path.read_text() + " ")
    elif damage in {"verdict_json", "verdict_schema"}:
        path.write_text("{" if damage == "verdict_json" else "{}")
        artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        save(root, report)
    elif damage == "duplicate_task":
        report["tasks"].append(copy.deepcopy(report["tasks"][0]))
        save(root, report)
    elif damage == "duplicate_path":
        report["tasks"][0]["artifacts"].append(copy.deepcopy(artifact))
        save(root, report)
    output = root / OUTPUT_NAME
    output.write_text("previous output")
    assert main(["sample", "--reports", str(root)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("input error:")
    assert output.read_text() == "previous output"


@pytest.mark.parametrize("kind", ["absolute", "traversal", "symlink"])
def test_rejects_verdict_paths_outside_report_before_opening(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, report = report_factory(("bug",))
    outside = root.parent / "verdict-9.json"
    outside.write_text("never read this")
    if kind == "symlink":
        (root / "verdict-9.json").symlink_to(outside)
    artifact = report["tasks"][0]["artifacts"][-1]
    artifact["path"] = str(outside) if kind == "absolute" else "../verdict-9.json" if kind == "traversal" else "verdict-9.json"
    save(root, report)
    original = Path.read_bytes
    def read(path: Path) -> bytes:
        assert path != outside
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(SampleInputError, match="inside the report directory"):
        sample_report(root)


def test_empty_report_verdict_pool_is_a_successful_empty_sample(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]],
) -> None:
    root, report = report_factory(("bug",))
    report["tasks"][0]["artifacts"] = []
    save(root, report)
    review = sample_report(root)
    assert review["samples"] == [] and review["available"] == 0


@pytest.mark.parametrize("n", ["0", "-1", "bad"])
def test_invalid_n_is_input_error(
    tmp_path: Path, n: str, capsys: pytest.CaptureFixture[str],
) -> None:
    try:
        code = main(["sample", "--reports", str(tmp_path), "--n", n])
    except SystemExit as exc:
        code = exc.code
    assert code == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("failure", ["schema", "output"])
def test_internal_errors_have_exit_two_and_no_stdout(
    report_factory: Callable[..., tuple[Path, dict[str, Any]]], failure: str,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, _ = report_factory()
    if failure == "schema":
        def broken(*args: Any) -> None:
            raise FileNotFoundError("missing validator schema")
        monkeypatch.setattr("verifier.sample.validate", broken)
    else:
        (root / OUTPUT_NAME).mkdir()
    assert main(["sample", "--reports", str(root)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("internal error:")


def test_module_entrypoint_uses_the_synthetic_report(
    retained_report: tuple[Path, dict[str, Any]], tmp_path: Path,
) -> None:
    root, _ = retained_report
    output = tmp_path / "module-review.json"
    result = subprocess.run([sys.executable, "-m", "verifier", "sample", "--reports", str(root),
                             "--n", "2", "--out", str(output)],
                            capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout == str(output) + "\n"
    review = json.loads(output.read_text())
    assert len(review["samples"]) == 2 and review["available"] == 6
    assert not (root / OUTPUT_NAME).exists()
