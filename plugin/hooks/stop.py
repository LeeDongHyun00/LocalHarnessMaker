"""Codex Stop entry point."""

import os

if os.environ.get("HARNESS_NESTED") == "1":
    raise SystemExit(0)

import sys
sys.dont_write_bytecode = True
import time


def main() -> int:
    """Catch runtime import failures as well as handler failures."""
    if os.environ.get("HARNESS_NESTED") == "1":
        return 0
    started = None
    try:
        from _scope import read_scoped_payload
        payload = read_scoped_payload()
        if payload is None:
            return 0
        started = time.perf_counter()
        from _entrypoint import execute
        return execute("Stop", started, payload)
    except Exception as exc:
        print(f"harness warning: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"harness elapsed_seconds={(time.perf_counter() - started) if started is not None else 0.0:.6f}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
