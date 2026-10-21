"""Contract CLI: one successful output path on stdout, diagnostics on stderr."""

import argparse
import json
import logging
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from controller.backends.cheap_api import CheapAPIBackend
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


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    parser = Parser(prog="python -m controller")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    contract_parser = commands.add_parser("contract")
    contract_parser.add_argument("--prompt", required=True, type=Path)
    contract_parser.add_argument("--handoff", required=True)
    contract_parser.add_argument("--cases", required=True, type=Path)
    contract_parser.add_argument("--backend", required=True, choices=("cheap_api", "local"))
    contract_parser.add_argument("--out", required=True, type=Path)
    try:
        args = parser.parse_args(argv)
        request = read_request(args.prompt)
        handoff = None if args.handoff == "none" else load_object(Path(args.handoff))
        if not args.cases.is_dir():
            raise InputError("--cases must reference an existing directory")
        if not args.out.parent.is_dir() or args.out.is_dir():
            raise InputError("--out must have an existing parent directory and name a file")
        if args.backend == "local":
            raise InputError("The local backend is pending D-3; no API fallback was made")
        # Retrieval is a D-2 deliverable; avoid silently ignoring supplied cases.
        if any(args.cases.glob("*.jsonl")):
            raise InputError("JSONL case retrieval is pending D-2; use an empty cases directory")
        result = generate_contract(request, CheapAPIBackend(), handoff=handoff)
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
