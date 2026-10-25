"""Exercise installed packages at frozen CLI/adapter boundaries, without providers."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from importlib.metadata import distributions
from io import StringIO
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import sysconfig
from typing import Any

from controller.__main__ import main as controller_main
from controller.backends.base import Message, Usage
import controller.v3 as controller_v3
from jsonschema import Draft202012Validator, FormatChecker
from plugin.v3_adapter import Adapter
import pytest
from referencing import Registry, Resource
from verifier.__main__ import main as verifier_main

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"


def validator(name: str) -> Draft202012Validator:
    registry = Registry().with_resources(
        (path.name, Resource.from_contents(json.loads(path.read_text(encoding="utf-8"))))
        for path in SCHEMAS.glob("*.schema.json")
    )
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def reference(directory: Path, relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": sha256((directory / relative).read_bytes()).hexdigest()}


@pytest.mark.parametrize("changed_final", [False, True], ids=["merge-audit", "retain-stale-audit"])
def test_frozen_v3_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed_final: bool,
) -> None:
    # No sys.path modifications or source loading: use the editable installation.
    # Ignore the source-tree egg-info, which has no PEP 610 installation record.
    installed = next(d for d in distributions(path=[sysconfig.get_paths()["purelib"]])
                     if d.metadata["Name"] == "local-harness-maker")
    direct_url = json.loads(installed.read_text("direct_url.json") or "{}")
    assert direct_url.get("dir_info", {}).get("editable") is True
    workspace = tmp_path.resolve()
    session_id = "lead-contract-fixture"
    directory = workspace / ".localharness/v3/sessions" / sha256(session_id.encode()).hexdigest()
    (directory / "evidence").mkdir(parents=True)
    prompt = directory / "evidence/prompt.txt"
    prompt.write_text("Create `app.py`.\nPreserve `config.txt`.\n", encoding="utf-8")
    (workspace / "config.txt").write_text("fixture configuration\n", encoding="utf-8")

    # SessionStart's prerequisite is synthetic; no installed Codex is launched.
    pin = read(SCHEMAS / "examples/pin-check.json")
    (directory / "evidence/models.json").write_text('["gpt-6-luna"]', encoding="utf-8")
    (directory / "evidence/prices.json").write_bytes((ROOT / "controller/prices.yaml").read_bytes())
    pin.update(session_id=session_id,
               model_list=reference(directory, "evidence/models.json"),
               pricing_snapshot=reference(directory, "evidence/prices.json"))
    (directory / "pin-check.json").write_text(json.dumps(pin), encoding="utf-8")
    validator("pin-check").validate(pin)

    calls: list[str] = []
    claim_text = "Preserved config.txt."
    citation = ""

    class FixedLuna:
        model = "gpt-6-luna"

        def __init__(self, prices: Any, pricing_ref: str) -> None:
            assert pricing_ref == pin["pricing_ref"]

        def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
            inputs = json.loads(messages[-1]["content"])
            if "request" in inputs:
                calls.append("requirements")
                return {"requirements": [
                    {"kind": "named_file", "text": "Create app.py", "source_excerpt": "Create `app.py`."},
                    {"kind": "protected_file", "text": "Preserve config.txt", "source_excerpt": "Preserve `config.txt`."},
                ], "open_questions": []}
            calls.append("claim_audit")
            return {"claims": [{"requirement_id": "R-2", "claim_excerpt": claim_text,
                                "citations": [{"citation_excerpt": citation}], "assessment": "supported"}]}

        def usage(self) -> Usage:
            return Usage(input_tokens=100, cached_input_tokens=0, output_tokens=20,
                         usd=None, latency_seconds=0.01)

    monkeypatch.setattr(controller_v3, "PinnedLunaClient", FixedLuna)
    operations: list[tuple[str, str]] = []

    def invoke(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        # Use the real hook adapter argv and real CLI parsers in process so the
        # only provider boundary remains mocked in this interpreter.
        assert command[:2] == [sys.executable, "-m"]
        assert kwargs["shell"] is False and kwargs["env"]["HARNESS_NESTED"] == "1"
        module, operation = command[2:4]
        operations.append((module, operation))
        entry = {"controller": controller_main, "verifier": verifier_main}[module]
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = entry(command[3:])
        assert code == 0, f"{module} {operation}: exit={code}, stderr={stderr.getvalue()}"
        return subprocess.CompletedProcess(command, code, stdout.getvalue(), stderr.getvalue())

    monkeypatch.delenv("HARNESS_PYTHON", raising=False)
    adapter = Adapter(runner=invoke)
    common = {"session_id": session_id, "directory": directory}
    adapter.call("controller", "requirements", prompt=prompt, **common)
    requirements = directory / "requirements.json"
    table = read(requirements)
    validator("requirements").validate(table)
    assert table["state"] == "ready"
    assert table["requirements"][0]["check"] == {"type": "file_exists", "path": "app.py"}
    assert table["requirements"][1]["check"]["type"] == "file_unchanged"

    def check(round_number: int, final: Path, audit: Path | None = None) -> dict[str, Any]:
        result = adapter.call("verifier", "check", requirements=requirements, workspace=workspace,
                              round_number=round_number, final=final, audit=audit, **common)
        assert len(result.stdout.splitlines()) == 1 and result.stdout.endswith("\n")
        summary = json.loads(result.stdout)
        assert set(summary) == {"overall", "failed_rows", "unverifiable_rows", "retry_warranted"}
        validator("completion-report").validate(read(directory / "completion-report.json"))
        return summary

    final = directory / "evidence/final.txt"
    final.write_text(claim_text, encoding="utf-8")
    assert check(1, final) == {"overall": "fail", "failed_rows": ["R-1"],
                               "unverifiable_rows": [], "retry_warranted": True}
    first = read(directory / "completion-report.json")
    assert first["check_round"] == 1
    assert first["retry"]["used"] == 1 and first["retry"]["failed_requirement_ids"] == ["R-1"]
    evidence = first["items"][1]["evidence"][0]
    citation = f"Evidence: `{evidence['path']}`."
    final = directory / "evidence/audit-input.txt"
    final.write_text(f"{claim_text} {citation}\n", encoding="utf-8")
    adapter.call("controller", "claim-audit", requirements=requirements, final=final, **common)
    audit_path = directory / "claim-audit.json"
    audit_bytes = audit_path.read_bytes()
    audit = read(audit_path)
    audit_validator = validator("completion-report")
    audit_validator.evolve(schema=audit_validator.schema["properties"]["claim_audit"]).validate(audit)
    assert audit["status"] == "complete" and audit["claims"][0]["assessment"] == "supported"
    assert audit["claims"][0]["cited_evidence"][0]["sha256"] == evidence["sha256"]

    immutable = {p: p.read_bytes() for p in (directory / "evidence").iterdir() if p != final}
    (workspace / "app.py").write_text("def health():\n    return True\n", encoding="utf-8")
    if changed_final:
        final = directory / "evidence/repaired-final.txt"
        final.write_text(f"Created app.py. {claim_text} {citation}\n", encoding="utf-8")
    assert check(2, final, audit_path) == {"overall": "pass", "failed_rows": [],
                                         "unverifiable_rows": [], "retry_warranted": False}
    report = read(directory / "completion-report.json")
    assert report["check_round"] == 2 and report["retry"] == first["retry"]

    ledger = read(SCHEMAS / "examples/ledger.json")
    ledger.update(session_id=session_id, requirements=reference(directory, "requirements.json"),
                  open_items=[], validation=None)
    ledger["decisions"][0]["fixes"][0]["path"] = "app.py"
    ledger_path = directory / "ledger.json"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    validator("ledger").validate(ledger)
    adapter.call("verifier", "ledger-validate", ledger=ledger_path, workspace=workspace, **common)
    validator("ledger").validate(read(ledger_path))
    assert read(ledger_path)["validation"]["status"] == "valid"
    latest = workspace / ".localharness/v3/latest-ledger.json"
    validator("ledger").validate(read(latest))
    assert latest.read_bytes() == ledger_path.read_bytes()

    records = [json.loads(line) for line in (directory / "luna-calls.jsonl").read_text().splitlines()]
    for record in records:
        validator("luna-call").validate(record)
    assert [r["phase"] for r in records] == calls == ["requirements", "claim_audit"]
    assert all(r["model"] == "gpt-6-luna" and r["reasoning_effort"] == "low" for r in records)
    assert {"pin-check.json", "requirements.json", "claim-audit.json", "completion-report.json",
            "ledger.json", "luna-calls.jsonl"} <= {p.name for p in directory.iterdir()}
    assert operations == [("controller", "requirements"), ("verifier", "check"),
                          ("controller", "claim-audit"), ("verifier", "check"),
                          ("verifier", "ledger-validate")]
    for path, data in immutable.items():
        assert path.read_bytes() == data, path
    assert audit_path.read_bytes() == audit_bytes
    # Assert after ledger validation so a merge defect still exercises the entire chain.
    merged = report["claim_audit"]
    assert merged["status"] == ("stale" if changed_final else "complete"), (
        "Role 4 defect: round 2 ignored the supplied claim-audit.json after round 1; "
        f"expected retained audit, got {merged}"
    )
    assert merged["claims"] == audit["claims"] and merged["luna_call"] == audit["luna_call"]
    assert merged["audited_final_message"]["sha256"] == audit["audited_final_message"]["sha256"]


def required_flags(usage: str) -> set[str]:
    """Exclude optional groups and conditional mutually exclusive mode selectors."""
    while re.search(r"\[[^\[\]]*\]", usage):
        usage = re.sub(r"\[[^\[\]]*\]", "", usage)
    usage = re.sub(r"\([^()]*\|[^()]*\)", "", usage)
    return set(re.findall(r"--[a-z][a-z-]*", usage))


def documented_operations() -> dict[tuple[str, str], tuple[set[str], set[str]]]:
    """Read all six historical signatures and all five frozen v3 signatures."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    section = agents.split("### 3.2 Command line interfaces\n", 1)[1].split("### 3.3 ", 1)[0]
    signatures = re.findall(r"^\d+\. (python -m .+)$|^\| `(python -m [^`]+)`", section, re.M)
    assert len(signatures) == 11, "section 3.2 operation inventory changed; review contract coverage"
    operations: dict[tuple[str, str], tuple[set[str], set[str]]] = {}
    for historical, frozen in signatures:
        signature = historical or frozen
        parts = signature.split()
        module = parts[2]
        operation = parts[3] if not parts[3].startswith("--") else ""
        # verifier check retains both documented modes in a single parser;
        # its --help must expose exactly their union, with no extra flags.
        key = (module, operation)
        flags = set(re.findall(r"--[a-z][a-z-]*", signature))
        required = required_flags(signature)
        if key in operations:
            previous_flags, previous_required = operations[key]
            operations[key] = previous_flags | flags, previous_required & required
        else:
            operations[key] = flags, required
    return operations


@pytest.mark.parametrize("module,operation,expected,required", [
    (module, operation, flags, required)
    for (module, operation), (flags, required) in documented_operations().items()
])
def test_section_3_2_arguments_match_cli_help(
    module: str, operation: str, expected: set[str], required: set[str], tmp_path: Path,
) -> None:
    command = [sys.executable, "-m", module, *([operation] if operation else []), "--help"]
    # An unrelated cwd and no PYTHONPATH ensure imports use the editable package.
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(command, cwd=tmp_path, env=env, shell=False,
                            text=True, capture_output=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    usage, options = result.stdout.split("options:\n", 1)
    actual = set(re.findall(r"--[a-z][a-z-]*", options)) - {"--help"}
    assert actual == expected, (
        f"{module} {operation}: undocumented={sorted(actual - expected)}, missing={sorted(expected - actual)}"
    )
    assert required_flags(usage) == required, f"{module} {operation}: required/optional drift\n{usage}"
    assert "positional arguments:" not in result.stdout
    # Every documented flag consumes exactly one value; --help is the only switch.
    option_rows = [line.strip().split("  ", 1)[0] for line in options.splitlines()
                   if line.lstrip().startswith("--")]
    assert all(len(row.split()) == 2 for row in option_rows), option_rows
