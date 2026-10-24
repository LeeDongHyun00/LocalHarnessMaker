"""Verifier command-line entry points."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from jsonschema import ValidationError

from verifier.check import check_contract
from verifier.handoff_validate import HandoffInputError, validate_handoff
from verifier.processes import Shutdown, shutdown_scope
from verifier.sample import OUTPUT_NAME, SampleInputError, sample_report
from verifier.ledger import InvalidLedger, validate_ledger
from verifier.v3_report import check_requirements


class InputParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"input error: {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = InputParser(prog="python -m verifier")
    commands = parser.add_subparsers(dest="operation", required=True, parser_class=InputParser)
    check = commands.add_parser("check")
    source = check.add_mutually_exclusive_group(required=True)
    source.add_argument("--contract", type=Path)
    source.add_argument("--requirements", type=Path)
    check.add_argument("--workspace", required=True, type=Path)
    check.add_argument("--transcript", type=Path)
    check.add_argument("--attempt", type=int)
    check.add_argument("--out", type=Path)
    check.add_argument("--session-id")
    check.add_argument("--artifacts", type=Path)
    check.add_argument("--round", dest="round_number", type=int)
    check.add_argument("--claim-audit", type=Path)
    check.add_argument("--final-message", type=Path)
    ledger = commands.add_parser("ledger-validate")
    ledger.add_argument("--ledger", required=True, type=Path)
    ledger.add_argument("--workspace", required=True, type=Path)
    ledger.add_argument("--session-id", required=True)
    ledger.add_argument("--artifacts", required=True, type=Path)
    handoff = commands.add_parser("validate-handoff")
    handoff.add_argument("--handoff", required=True)
    sample = commands.add_parser("sample")
    sample.add_argument("--reports", required=True, type=Path)
    sample.add_argument("--n", type=int, default=20)
    sample.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.operation == "ledger-validate":
        try:
            result = validate_ledger(args.ledger, args.workspace, args.session_id, args.artifacts)
        except InvalidLedger as exc:
            print(f"Ledger advisory: {exc}; ledger will not be injected.")
            return 1
        except Exception as exc:
            print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        if result["validation"]["status"] != "valid":
            print(f"Ledger advisory: {result['validation']['reason']}; ledger will not be injected.")
            return 1
        print(args.ledger)
        return 0
    if args.operation == "check" and args.requirements is not None:
        try:
            if any(value is not None for value in (args.contract, args.transcript, args.attempt, args.out)):
                raise ValueError("historical flags cannot be combined with --requirements")
            if args.session_id is None or args.artifacts is None or args.round_number is None:
                raise ValueError("--session-id, --artifacts and --round are required with --requirements")
            result = check_requirements(args.requirements, args.workspace, args.session_id, args.artifacts,
                                        args.round_number, args.claim_audit, args.final_message)
        except (Exception, Shutdown) as exc:
            print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, separators=(",", ":")))
        return 0
    if args.operation == "check":
        if any(value is None for value in (args.transcript, args.attempt, args.out)):
            parser.error("--contract requires --transcript, --attempt and --out")
        if any(value is not None for value in (args.session_id, args.artifacts, args.round_number,
                                               args.claim_audit, args.final_message)):
            parser.error("v3 flags cannot be combined with --contract")
    if args.operation == "sample":
        try:
            review = sample_report(args.reports, args.n)
        except SampleInputError as exc:
            print(f"input error: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        output = args.out if args.out is not None else args.reports / OUTPUT_NAME
        try:
            output.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception as exc:
            print(f"internal error: cannot write sample: {exc}", file=sys.stderr)
            return 2
        print(f"verifier sample selected={len(review['samples'])} available={review['available']} "
              f"seed={review['seed']}", file=sys.stderr)
        print(output)
        return 0
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
        with shutdown_scope():
            try:
                serialized, claims = _check(args)
            except (ValueError, OSError, ValidationError) as exc:
                print(f"input error: {exc}", file=sys.stderr)
                return 1
    except Shutdown as exc:
        print(f"internal error: {exc}; child process groups cleaned up", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    # Exiting shutdown_scope finishes cleanup and restores handlers. Publish
    # nothing until that exit has succeeded, including its final cleanup pass.
    try:
        args.out.with_suffix(".claims.json").write_text(claims, encoding="utf-8")
        args.out.write_text(serialized, encoding="utf-8")
    except Exception as exc:
        print(f"internal error: cannot write verdict/claims: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


def _check(args: argparse.Namespace) -> tuple[str, str]:
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    observations: dict[str, Any] = {}
    verdict = check_contract(contract, args.workspace, args.transcript, args.attempt, observations=observations)
    return (json.dumps(verdict, indent=2, ensure_ascii=False) + "\n",
            json.dumps(observations, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main())
