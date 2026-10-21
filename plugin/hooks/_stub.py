"""CLI fixture adapter. Copies schema examples byte-for-byte; never calls a model.

This helper is not a lifecycle hook. Its caller intentionally sets the nested
guard in its child environment; only lifecycle entry points bypass on that flag.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


EXAMPLES = Path(__file__).resolve().parents[2] / "schemas/examples"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", choices=("controller", "verifier"))
    parser.add_argument("operation", choices=("contract", "check", "handoff", "validate-handoff"))
    parser.add_argument("--prompt")
    parser.add_argument("--handoff")
    parser.add_argument("--cases")
    parser.add_argument("--backend", choices=("codex_cli", "cheap_api", "local"))
    parser.add_argument("--contract")
    parser.add_argument("--workspace")
    parser.add_argument("--transcript")
    parser.add_argument("--verdict")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.operation == "validate-handoff":
        print(args.handoff)
        return 0
    names = {"contract": "contract.json", "handoff": "handoff.json",
             "check": "verdict_fail.json" if args.attempt == 1 else "verdict_pass.json"}
    if args.out is None:
        parser.error("--out is required")
    shutil.copyfile(EXAMPLES / names[args.operation], args.out)
    print("harness stub: SYNTHETIC fixture; no task verification or model call", file=sys.stderr)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
