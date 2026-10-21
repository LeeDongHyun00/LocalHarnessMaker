"""Verifier command-line entry points."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from jsonschema import ValidationError

from verifier.check import check_contract
from verifier.handoff_validate import HandoffInputError, validate_handoff


class InputParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"input error: {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = InputParser(prog="python -m verifier")
    commands = parser.add_subparsers(dest="operation", required=True, parser_class=InputParser)
    check = commands.add_parser("check")
    check.add_argument("--contract", required=True, type=Path)
    check.add_argument("--workspace", required=True, type=Path)
    check.add_argument("--transcript", required=True, type=Path)
    check.add_argument("--attempt", required=True, type=int)
    check.add_argument("--out", required=True, type=Path)
    handoff = commands.add_parser("validate-handoff")
    handoff.add_argument("--handoff", required=True)
    args = parser.parse_args(argv)
    if args.operation == "validate-handoff":
        try:
            validate_handoff(Path(args.handoff))
        except HandoffInputError as exc:
            print(f"input error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(args.handoff)
        return 0
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        verdict = check_contract(contract, args.workspace, args.transcript, args.attempt)
        serialized = json.dumps(verdict, indent=2, ensure_ascii=False) + "\n"
    except (ValueError, OSError, ValidationError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    try:
        args.out.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        print(f"internal error: cannot write verdict: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
