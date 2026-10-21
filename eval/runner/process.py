"""Mockable child-process execution with bounded process-group cleanup."""

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
from typing import Callable


@dataclass(frozen=True)
class ProcessResult:
    """Capture process termination, including deadline expiry."""

    returncode: int
    timed_out: bool = False


def run_process(
    argv: list[str], *, cwd: Path, env: dict[str, str], stdin: str,
    stdout: Path, stderr: Path, timeout: float,
    on_start: Callable[[int], None] | None = None,
) -> ProcessResult:
    """Retain complete disk logs and stop descendants before allowing grading."""
    with stdout.open("wb") as output, stderr.open("wb") as error:
        process = subprocess.Popen(
            argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=output,
            stderr=error, start_new_session=True,
        )
        try:
            if on_start:
                on_start(process.pid)
            process.communicate(stdin.encode(), timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            if isinstance(exc, KeyboardInterrupt):
                raise
            return ProcessResult(process.returncode, timed_out=True)
        # Prevent surviving command children from observing the later grading copy.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return ProcessResult(process.returncode)
