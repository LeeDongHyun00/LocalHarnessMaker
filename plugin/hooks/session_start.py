"""Codex SessionStart entry point."""

import os

if os.environ.get("HARNESS_NESTED") == "1":
    raise SystemExit(0)

import sys
import time


def main() -> int:
    """Catch runtime import failures as well as handler failures."""
    if os.environ.get("HARNESS_NESTED") == "1":
        return 0
    started = time.perf_counter()
    try:
        from _entrypoint import execute
        return execute("SessionStart", started)
    except Exception as exc:
        print(f"harness warning: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"harness elapsed_seconds={time.perf_counter() - started:.6f}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
