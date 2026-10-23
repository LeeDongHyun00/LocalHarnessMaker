"""Persist a public stop reason while normal subprocess cleanup handles signals."""

from contextlib import contextmanager
import json
from pathlib import Path
import signal
from typing import Iterator

from eval.runner import core


@contextmanager
def stop_signals(out: Path) -> Iterator[None]:
    """Convert SIGINT/SIGTERM to cleanup-friendly interruption and retain diagnostics."""
    reason: str | None = None

    def record() -> None:
        out.mkdir(parents=True, exist_ok=True)
        path = out / "run-diagnostics.json"
        try:
            diagnostics = json.loads(path.read_text())
        except (OSError, ValueError):
            diagnostics = {}
        diagnostics.update(stop_reason=reason, stopped_at=core.now(), exit_code=130)
        core.write_json(path, diagnostics)

    def interrupted(signum: int, frame: object) -> None:
        nonlocal reason
        reason = signal.Signals(signum).name
        record()
        raise KeyboardInterrupt

    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        yield
    except KeyboardInterrupt:
        reason = reason or "SIGINT"
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if reason:
            # The runner may have caught the interruption to checkpoint the
            # segment; preserve the original signal over its generic stop text.
            record()
            raise KeyboardInterrupt
