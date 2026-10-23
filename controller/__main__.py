"""Controller CLI: one successful output path on stdout, diagnostics on stderr."""

import argparse
import json
import logging
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from controller.backends.base import Backend
from controller.backends.routing import RoutedBackend
from controller.judge import generate_judgment
from controller.handoff_gen import generate_handoff, validate_handoff_inputs
from controller.generation import read_text, validate_input
from controller.cases import retrieve_cases
from controller.contract_gen import generate_contract, read_request
from controller.errors import BackendError, InputError
from controller.settings import load_object


class Parser(argparse.ArgumentParser):
    """Align input errors with the shared CLI exit-code convention."""

    def error(self, message: str) -> None:
        raise InputError(message)


def write_json(path: Path, value: dict[str, Any]) -> None:
    """Publish the already validated artifact with an atomic replacement."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
        suffix=".tmp", delete=False,
    ) as output:
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        temporary = Path(output.name)
    temporary.replace(path)


def main(
    argv: Sequence[str] | None = None, *,
    backend_factory: Callable[[str], Backend] | None = None,
) -> int:
    factory = backend_factory or RoutedBackend
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    parser = Parser(prog="python -m controller")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    contract_parser = commands.add_parser("contract")
    contract_parser.add_argument("--prompt", required=True, type=Path)
    contract_parser.add_argument("--handoff", required=True)
    contract_parser.add_argument("--cases", required=True, type=Path)
    judge_parser = commands.add_parser("judge")
    judge_parser.add_argument("--criterion", required=True, type=Path)
    judge_parser.add_argument("--artifact", required=True, type=Path)
    handoff_parser = commands.add_parser("handoff")
    handoff_parser.add_argument("--transcript", required=True, type=Path)
    handoff_parser.add_argument("--contract", required=True, type=Path)
    handoff_parser.add_argument("--verdict", required=True, type=Path)
    for subparser in (contract_parser, judge_parser, handoff_parser):
        subparser.add_argument("--backend", required=True, choices=("codex_cli", "cheap_api", "local"))
        subparser.add_argument("--out", required=True, type=Path)
    try:
        args = parser.parse_args(argv)
        if not args.out.parent.is_dir() or args.out.is_dir():
            raise InputError("--out must have an existing parent directory and name a file")
        if args.command == "contract":
            request = read_request(args.prompt)
            handoff = None if args.handoff == "none" else load_object(Path(args.handoff))
            if handoff is not None:
                validate_input(handoff, "handoff.schema.json")
            examples = retrieve_cases(request, args.cases)
            result = generate_contract(request, factory(args.backend), handoff=handoff, examples=examples)
        elif args.command == "judge":
            criterion = load_object(args.criterion)
            validate_input(criterion, "judgment-input.schema.json")
            result = generate_judgment(criterion, args.artifact, factory(args.backend))
        else:
            transcript = read_text(args.transcript)
            contract, verdict = load_object(args.contract), load_object(args.verdict)
            validate_handoff_inputs(contract, verdict)
            result = generate_handoff(transcript, contract, verdict, factory(args.backend))
        write_json(args.out, result)
    except InputError as exc:
        print(f"controller: {exc}", file=sys.stderr)
        return 1
    except (BackendError, OSError) as exc:
        print(f"controller: {exc}", file=sys.stderr)
        return 2
    except Exception:
        # Never echo remote bodies or credentials through exception text.
        print("controller: unexpected internal error", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
