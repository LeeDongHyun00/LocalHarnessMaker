"""Exercise all three reference workspaces without claiming task completion."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reports = Path(tempfile.mkdtemp(prefix="localharness-verifier-smoke-"))
    schema = json.loads((root / "schemas/verdict.schema.json").read_text())
    validator = Draft202012Validator(schema)
    for name in ("pass", "fail", "claimed"):
        output = reports / f"{name}.json"
        command = [
            sys.executable, "-m", "verifier", "check",
            "--contract", "schemas/examples/contract.json",
            "--workspace", f"tests/verifier/fixtures/ws_{name}",
            "--transcript", f"tests/verifier/fixtures/transcript_{name}.jsonl",
            "--attempt", "1", "--out", str(output),
        ]
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if completed.returncode != 0:
            print(completed.stderr, file=sys.stderr)
            return completed.returncode
        if completed.stdout != str(output) + "\n":
            raise AssertionError("CLI stdout is not exactly one output path")
        verdict = json.loads(output.read_text())
        validator.validate(verdict)
        statuses = ", ".join(f"{item['id']}={item['status']}" for item in verdict["items"])
        print(f"{name}: exit=0 schema=valid overall={verdict['overall']} {statuses}")
        print(completed.stderr.strip())
    print(f"reports: {reports}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
