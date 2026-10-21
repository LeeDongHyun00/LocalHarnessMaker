"""Exercise adversarial log evidence without referencing real grader locations."""

import json
import os
from pathlib import Path
from urllib.parse import quote

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, executor_environment
from eval.metrics import pass_rate


@pytest.fixture
def private(tmp_path: Path) -> PrivateGraders:
    root = tmp_path / "trusted-storage"
    task = root / "unit-task"
    task.mkdir(parents=True)
    grader = task / "test_private_synthetic.py"
    grader.write_text("# Synthetic audit marker only\n")
    return PrivateGraders.load(root, "unit-task", tmp_path / "repository")


@pytest.mark.parametrize("encoding", ["plain", "json_escape", "url"])
def test_private_path_match_invalidates_and_redacts(tmp_path: Path, private: PrivateGraders, encoding: str) -> None:
    value = str(private.root)
    if encoding == "url":
        value = quote(value, safe="")
    data = json.dumps({"type": "item.completed", "item": {"command": "cat " + value}})
    if encoding == "json_escape":
        data = data.replace("/", "\\u002f")
    log = tmp_path / "events.jsonl"
    log.write_text(data + '\n{"type":"turn.completed"}\n')
    audit = audit_logs([log], private)
    assert audit["status"] == "access_detected"
    assert audit["matches"][0]["line"] == 1
    serialized = private.redact(json.dumps(audit))
    assert str(private.root) not in serialized
    published = private.redact(data)
    assert str(private.root) not in json.dumps(json.loads(published), ensure_ascii=False)


def test_basename_match_even_without_a_path(tmp_path: Path, private: PrivateGraders) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(json.dumps({"type": "item.completed", "text": private.files[0].name}) + '\n{"type":"turn.completed"}\n')
    assert audit_logs([log], private)["status"] == "access_detected"


@pytest.mark.parametrize("text", ["", "not json\n", "[]\n", '{"type":"turn.started"}\n'])
def test_incomplete_or_malformed_logs_are_not_clean(tmp_path: Path, private: PrivateGraders, text: str) -> None:
    log = tmp_path / "events.jsonl"
    log.write_text(text)
    assert audit_logs([log], private)["status"] == "inconclusive"


def test_environment_removes_locations_and_api_keys(private: PrivateGraders, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LHM_PRIVATE_GRADERS", str(private.root))
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-do-not-forward")
    monkeypatch.setenv("EXTRA_LOCATION", str(private.root))
    monkeypatch.setenv("TMPDIR", str(private.root))
    result = executor_environment(private, tmp_path / "runtime-home")
    assert not {"LHM_PRIVATE_GRADERS", "EXTRA_LOCATION", "OPENAI_API_KEY", "TMPDIR"} & result.keys()
    assert str(private.root) not in json.dumps(result)
    assert result["HARNESS_NESTED"] == "1"


def test_private_root_inside_repo_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        PrivateGraders.load(tmp_path / "repository/private", "task", tmp_path / "repository")


def test_historical_grader_names_are_also_audited(tmp_path: Path, private: PrivateGraders) -> None:
    historical = PrivateGraders(private.root, private.files, name_aliases=("old_private_check.py",))
    log = tmp_path / "events.jsonl"
    log.write_text('{"type":"item.completed","text":"old_private_check.py"}\n{"type":"turn.completed"}\n')
    audit = audit_logs([log], historical)
    assert audit["status"] == "access_detected"
    assert audit["matches"][0]["marker"] == "historical_grader_1"


def test_pass_rate_excludes_invalid_and_preserves_empty_denominator() -> None:
    assert pass_rate([]) is None
    assert pass_rate([{"outcome": "invalid"}]) is None
    assert pass_rate([{"outcome": "pass"}, {"outcome": "fail"}, {"outcome": "invalid"}]) == 0.5
