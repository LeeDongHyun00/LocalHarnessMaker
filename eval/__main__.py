"""The frozen eval run command surface."""

import argparse
import os
from pathlib import Path
import sys

from eval.runner.core import run


class InputParser(argparse.ArgumentParser):
    """Preserve the project convention that malformed inputs exit with 1."""

    def error(self, message: str) -> None:
        raise ValueError(message)


def main() -> int:
    """Print one output path; keep diagnostics and private locations off stdout."""
    parser = InputParser()
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("run")
    command.add_argument("--config", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    try:
        args = parser.parse_args()
    except ValueError:
        print("Input error: use eval run --config FILE --out DIR", file=sys.stderr)
        return 1
    value = os.environ.get("LHM_PRIVATE_GRADERS")
    if not value:
        print("Set LHM_PRIVATE_GRADERS in the trusted parent environment", file=sys.stderr)
        return 1
    try:
        output = run(args.config, args.out, Path(value))
    except (ValueError, FileNotFoundError) as exc:
        # Path-bearing exceptions stay outside repository artifacts and terminal output.
        print(f"Input error: {type(exc).__name__}; verify config, login and external grader setup", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Internal error: {type(exc).__name__}; inspect retained external runtime logs", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
