"""Bounded ownership of verifier child process groups and shutdown signals."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import errno
import locale
import os
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Iterator


CLEANUP_SECONDS = 2.0
POLL_SECONDS = 0.05
DRAIN_SECONDS = 0.2
SHUTDOWN_SIGNALS = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)


class Shutdown(BaseException):
    """Escape input/transport exception handlers after an external shutdown."""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"verifier interrupted by {signal.Signals(signum).name}")


class LaunchError(OSError):
    """Only process creation failed; later execution/cleanup is not a launch."""


class ProcessGroups:
    """Track detached groups; injected OS operations keep lifecycle tests local."""

    def __init__(
        self, *, clock: Callable[[], float] | None = None,
        kill_group: Callable[[int, int], None] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.clock = clock or time.monotonic
        self.kill_group = kill_group or os.killpg
        self.sleep = sleep or time.sleep
        self.children: dict[int, Any] = {}
        self.launching = False
        self.deferred_shutdown: Callable[[], None] | None = None

    def _signal_child(self, pid: int, sig: int) -> bool:
        """Use Popen's identity/exit checks before signaling the known child."""
        process = self.children[pid]
        try:
            if process.poll() is not None:
                return False
            if sig:
                process.send_signal(sig)
            return process.poll() is None
        except OSError:
            # Exit and permission races also apply to the direct-PID fallback.
            return False

    def _signal(self, pid: int, sig: int) -> bool:
        try:
            self.kill_group(pid, sig)
            return True
        except OSError as exc:
            # macOS may report EPERM for an exiting Seatbelt process group.
            # ESRCH also need not mean that the known direct child has exited.
            if not isinstance(exc, (PermissionError, ProcessLookupError)) and exc.errno not in {
                errno.EPERM, errno.ESRCH,
            }:
                print(f"verifier cleanup: cannot signal group {pid}: {exc}", file=sys.stderr)
            return self._signal_child(pid, sig)

    def cleanup(self, *, graceful: bool) -> None:
        """TERM all groups together, share one grace period, then KILL survivors."""
        children = dict(self.children)
        if graceful and children:
            deadline = self.clock() + CLEANUP_SECONDS
            alive = {pid for pid in children if self._signal(pid, signal.SIGTERM)}
            while alive:
                # Reap leaders so zombies do not consume the entire grace period.
                for pid in alive:
                    try:
                        children[pid].poll()
                    except OSError:
                        pass
                alive = {pid for pid in alive if self._signal(pid, 0)}
                remaining = deadline - self.clock()
                if not alive or remaining <= 0:
                    break
                self.sleep(min(0.02, remaining))
        else:
            alive = set(children)
        for pid in alive:
            self._signal(pid, signal.SIGKILL)
        for pid, process in children.items():
            try:
                process.wait(timeout=0.1)
            except (OSError, subprocess.TimeoutExpired):
                # Retry only the known child, without an unbounded wait or
                # replacing the original timeout/shutdown with a cleanup error.
                self._signal_child(pid, signal.SIGKILL)
                try:
                    process.wait(timeout=0.1)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            self.children.pop(pid, None)


_active: ContextVar[ProcessGroups | None] = ContextVar("verifier_process_groups", default=None)


@contextmanager
def shutdown_scope(
    groups: ProcessGroups | None = None,
    set_signal: Callable[..., Any] = signal.signal,
) -> Iterator[ProcessGroups]:
    """Install CLI-only handlers and restore the caller's signal state."""
    owner = groups or ProcessGroups()
    previous: dict[int, Any] = {}
    token = _active.set(owner)

    def interrupted(signum: int, frame: Any) -> None:
        if owner.launching:
            # Let Popen finish and register its PID before unwinding. Do not
            # block signals across fork: children would inherit the signal mask.
            owner.deferred_shutdown = lambda: interrupted(signum, frame)
            return
        # A second signal must not interrupt the two-second teardown.
        for sig in SHUTDOWN_SIGNALS:
            set_signal(sig, signal.SIG_IGN)
        raise Shutdown(signum)

    try:
        for sig in SHUTDOWN_SIGNALS:
            previous[sig] = set_signal(sig, interrupted)
        yield owner
    finally:
        try:
            owner.cleanup(graceful=True)
        finally:
            _active.reset(token)
            for sig, handler in previous.items():
                set_signal(sig, handler)


def _partial_output(data: bytes | str | None, stream: Any, text: bool) -> bytes | str:
    """TimeoutExpired stores bytes even for Popen(text=True)."""
    if not text:
        return data or b""
    if isinstance(data, bytes):
        data = data.decode(getattr(stream, "encoding", None) or locale.getencoding(),
                           getattr(stream, "errors", None) or "strict")
    return (data or "").replace("\r\n", "\n").replace("\r", "\n")


def _capture(
    process: Any, argv: list[str], timeout: float, deadline: float,
    owner: ProcessGroups, now: Callable[[], float], text: bool,
) -> subprocess.CompletedProcess[Any]:
    """Drain in short communicate slices and observe leader exit independently."""
    partial_stdout: bytes | str | None = None
    partial_stderr: bytes | str | None = None
    first = True
    while True:
        code = process.poll()
        if code is not None:
            # Pipe EOF can be held open by descendants long after the leader
            # exits. Kill the group now, preserving the leader's own result.
            owner.cleanup(graceful=False)
            try:
                stdout, stderr = process.communicate(input=None, timeout=DRAIN_SECONDS)
            except subprocess.TimeoutExpired as exc:
                # An escaped or unsignalable descendant must not hold us here.
                stdout = _partial_output(
                    exc.output if exc.output is not None else partial_stdout, process.stdout, text,
                )
                stderr = _partial_output(
                    exc.stderr if exc.stderr is not None else partial_stderr, process.stderr, text,
                )
            return subprocess.CompletedProcess(argv, code, stdout, stderr)
        remaining = deadline - now()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(argv, timeout, output=partial_stdout, stderr=partial_stderr)
        try:
            # Popen.communicate uses selectors on POSIX and retains captured
            # chunks between calls. Never wait for EOF for the full criterion.
            stdout, stderr = process.communicate(
                input="" if first and text else None, timeout=min(POLL_SECONDS, remaining),
            )
        except subprocess.TimeoutExpired as exc:
            if exc.output is not None:
                partial_stdout = exc.output
            if exc.stderr is not None:
                partial_stderr = exc.stderr
        else:
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        first = False


def run_owned(
    argv: list[str], *, timeout: float, runner: Callable[..., Any] | None = None,
    clock: Callable[[], float] | None = None,
    kill_group: Callable[[int, int], None] | None = None,
    sleep: Callable[[float], None] | None = None, **kwargs: Any,
) -> subprocess.CompletedProcess[Any]:
    """Capture a child with bounded waits and cleanup on every exit path."""
    now = clock or time.monotonic
    owner = _active.get() or ProcessGroups(clock=now, kill_group=kill_group, sleep=sleep)
    started = now()
    # Defer shutdown until Popen's PID has been registered. Otherwise a signal
    # between fork/exec and registration could strand a detached group.
    process = None
    normal = False
    try:
        owner.launching = True
        try:
            try:
                process = (runner or subprocess.Popen)(argv, start_new_session=True, shell=False, **kwargs)
            except OSError as exc:
                raise LaunchError(str(exc)) from exc
            owner.children[process.pid] = process
        finally:
            owner.launching = False
            deferred = owner.deferred_shutdown
            owner.deferred_shutdown = None
            if deferred is not None:
                deferred()
        result = _capture(process, argv, timeout, started + timeout, owner, now, bool(kwargs.get("text")))
        normal = True
        return result
    finally:
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, SHUTDOWN_SIGNALS)
        try:
            owner.cleanup(graceful=not normal)
            # Escaped descendants may retain pipe handles; never communicate unboundedly.
            if process is not None:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError:
                            pass
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, mask)
