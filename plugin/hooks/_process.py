"""Own child groups through normal return, exceptions and catchable shutdown signals."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from types import FrameType
from typing import Any, Callable

SHUTDOWN_SIGNALS = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
CLEANUP_RESERVE = 4.0  # TERM grace 2s, bounded reap 0.5s, plus output/startup margin.


class ChildGroups:
    """Install signal handlers before spawning; retain ownership until cleanup ends."""

    def __init__(self, *, clock: Callable[[], float] | None = None,
                 sleep: Callable[[float], None] | None = None,
                 kill: Callable[[int, int], None] | None = None) -> None:
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.kill = kill or os.killpg
        self.children: list[Any] = []
        self.previous: dict[int, Any] = {}
        self.launching = False
        self.pending_signal: int | None = None
        self.after_cleanup: Callable[[], None] | None = None

    def interrupted(self, signum: int, frame: FrameType | None) -> None:
        """Unwind the owner so finally performs the same cleanup as deadlines."""
        if self.launching:
            self.pending_signal = signum
            return
        raise SystemExit(128 + signum)

    def __enter__(self) -> ChildGroups:
        for signum in SHUTDOWN_SIGNALS:
            self.previous[signum] = signal.signal(signum, self.interrupted)
        return self

    def alive(self, pid: int) -> bool:
        try:
            self.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def cleanup(self) -> None:
        """TERM all owned groups together, grant 2s, KILL survivors, reap parents."""
        for child in self.children:
            try:
                self.kill(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        end = self.clock() + 2.0
        while any(self.alive(child.pid) for child in self.children) and self.clock() < end:
            # poll reaps exited parents, so their zombies do not extend the grace.
            for child in self.children:
                child.poll()
            self.sleep(min(0.02, max(0.0, end - self.clock())))
        for child in self.children:
            if self.alive(child.pid):
                try:
                    self.kill(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                child.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
        try:
            if self.after_cleanup is not None:
                self.after_cleanup()
        finally:
            for child in self.children:
                for stream in (child.stdout, child.stderr, child.stdin):
                    if stream is not None:
                        stream.close()

    def __exit__(self, *exception: Any) -> None:
        # A second terminal signal must not interrupt cleanup halfway through.
        for signum in SHUTDOWN_SIGNALS:
            signal.signal(signum, signal.SIG_IGN)
        try:
            self.cleanup()
        finally:
            for signum, handler in self.previous.items():
                signal.signal(signum, handler)


def run_group(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Run one child session with signal-safe ownership and bounded shutdown."""
    timeout = kwargs.pop('timeout')
    input_text = kwargs.pop('input', None)
    kwargs.pop('capture_output', None)
    kwargs.pop('check', None)
    if input_text is not None:
        kwargs['stdin'] = subprocess.PIPE
    with ChildGroups() as owner:
        # Defer signals during spawn/register without masking them in the child.
        owner.launching = True
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True, **kwargs)
            owner.children.append(process)
        finally:
            owner.launching = False
        if owner.pending_signal is not None:
            owner.interrupted(owner.pending_signal, None)
        deadline = owner.clock() + timeout
        output: list[Any] = [None, None]

        def drain() -> None:
            # Cleanup has terminated the group. Bound even an escaped process
            # that still holds a pipe, rather than waiting for EOF indefinitely.
            try:
                output[:] = process.communicate(timeout=0.25)
            except subprocess.TimeoutExpired as exc:
                output[:] = [exc.output, exc.stderr]
                for index, stream in enumerate((process.stdout, process.stderr)):
                    value = output[index]
                    if isinstance(value, bytes) and process.text_mode:
                        output[index] = value.decode(stream.encoding, stream.errors).replace("\r\n", "\n").replace("\r", "\n")

        while True:
            remaining = max(0.0, deadline - owner.clock())
            try:
                # Short slices let us observe leader exit even when descendants
                # keep stdout/stderr open. communicate still drains large output
                # and writes stdin without blocking the parent's exit polling.
                output[:] = process.communicate(input=input_text, timeout=min(0.05, remaining))
                break
            except subprocess.TimeoutExpired as exc:
                input_text = None  # communicate retains its pending stdin buffer.
                if process.poll() is not None:
                    owner.after_cleanup = drain
                    break
                if owner.clock() >= deadline:
                    raise subprocess.TimeoutExpired(command, timeout, output=exc.output, stderr=exc.stderr) from exc
    return subprocess.CompletedProcess(command, process.returncode, *output)
