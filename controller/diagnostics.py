"""Opt-in metadata tracing; never retain prompts or provider payloads."""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def trace(step: str, **fields: Any) -> None:
    """Append and flush one record without changing controller behavior on I/O failure."""
    target = os.environ.get("HARNESS_CONTROLLER_TRACE")
    if not target:
        return
    try:
        with Path(target).open("a", encoding="utf-8") as output:
            output.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                                     "step": step, **fields}, ensure_ascii=True) + "\n")
            output.flush()
    except (OSError, ValueError):
        # Tracing is optional, including when the host supplies an unwritable path.
        pass


def byte_count(value: str | bytes | None) -> int:
    """Count captured bytes without copying their content into diagnostics."""
    return len(value.encode("utf-8", errors="replace") if isinstance(value, str) else value or b"")


def private_paths(text: str) -> str:
    """Hide home-directory paths in diagnostics other than the executable field."""
    text = re.sub(re.escape(str(Path.home())) + r"[^\s\"']*", "<home-path>", text)
    return re.sub(r"(?:/Users/|/home/)[^\s\"']+", "<home-path>", text)


def trace_failure(exc: BaseException, *, message: str | None = None) -> None:
    """Use a safe stage message when exception text may contain provider/request data."""
    trace("exception", exception_type=type(exc).__name__,
          message=private_paths(message if message is not None else "exception message redacted"))


def flush_diagnostics() -> None:
    """Flush existing handlers and piped stderr without closing caller-owned streams."""
    loggers = [logging.getLogger(), *[
        value for value in logging.root.manager.loggerDict.values()
        if isinstance(value, logging.Logger)
    ]]
    for logger in loggers:
        for handler in logger.handlers:
            try:
                handler.flush()
            except (OSError, ValueError):
                pass
    try:
        sys.stderr.flush()
    except (OSError, ValueError):
        pass
