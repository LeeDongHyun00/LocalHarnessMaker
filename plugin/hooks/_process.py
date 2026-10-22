"""Own child groups through normal return, exceptions and catchable shutdown signals."""
from __future__ import annotations

import os
import errno
import sys
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
                 kill: Callable[[int, int], None] | None = None,
                 members: Callable[[int], list[int]] | None = None,
                 kill_pid: Callable[[int, int], None] | None = None,
                 get_group: Callable[[int], int] | None = None) -> None:
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.kill = kill or os.killpg
        self.members = members or self.list_members
        self.kill_pid = kill_pid or os.kill
        self.get_group = get_group or os.getpgid
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

    @staticmethod
    def warn(message: str) -> None:
        print(f"plugin cleanup: {message}", file=sys.stderr)

    @staticmethod
    def list_members(group: int) -> list[int]:
        """Read numeric identities without a shell; zombies are already exited."""
        result = subprocess.run(['ps', '-A', '-o', 'pid=,pgid=,stat='],
                                capture_output=True, text=True, timeout=0.2, check=True,
                                shell=False)
        members: list[int] = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if (len(fields) != 3 or not fields[0].isascii() or not fields[0].isdigit()
                    or not fields[1].isascii() or not fields[1].isdigit()):
                raise ValueError('malformed ps process identity')
            pid, pgid = int(fields[0]), int(fields[1])
            if pid > 0 and pgid == group and not fields[2].startswith('Z'):
                members.append(pid)
        return members

    def reap(self, group: int) -> None:
        for child in self.children:
            if child.pid == group:
                try:
                    child.poll()
                except OSError as exc:
                    self.warn(f'cannot reap leader {group}: {exc}')

    def signal_group(self, group: int, signum: int) -> bool:
        """Reap/retry group races, then signal live members individually."""
        for attempt in range(3):
            self.reap(group)
            try:
                self.kill(group, signum)
                return True
            except OSError as exc:
                exited = any(child.pid == group and getattr(child, "returncode", None) is not None
                             for child in self.children)
                if attempt == 0 and not (exc.errno == errno.ESRCH and exited):
                    self.warn(f'group {group} signal {signum}: {exc}; reaping/retrying')
                if attempt < 2:
                    self.sleep(0.01)
        try:
            members = self.members(group)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            self.warn(f'cannot inspect group {group}: {exc}; cleanup unverified')
            # Still try the known leader when process listing is unavailable.
            members = [group]
        live = False
        for pid in members:
            try:
                # A PID from ps may have exited/reused since the snapshot.
                if self.get_group(pid) != group:
                    continue
                self.kill_pid(pid, signum)
                live = True
            except ProcessLookupError as exc:
                self.warn(f'member {pid} exited during signal {signum}: {exc}')
            except OSError as exc:
                self.warn(f'cannot signal member {pid} in group {group}: {exc}')
                live = True
        return live

    def alive(self, pid: int) -> bool:
        return self.signal_group(pid, 0)

    def live_members_remain(self, group: int) -> bool:
        """Verify KILL completion without mistaking unreaped orphans for live work."""
        self.reap(group)
        try:
            return bool(self.members(group))
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            self.warn(f'cannot verify live members of group {group}: {exc}')
            return self.alive(group)

    def cleanup(self) -> None:
        """TERM all owned groups together, grant 2s, KILL survivors, reap parents."""
        for child in self.children:
            self.signal_group(child.pid, signal.SIGTERM)
        end = self.clock() + 2.0
        while any(self.alive(child.pid) for child in self.children) and self.clock() < end:
            self.sleep(min(0.02, max(0.0, end - self.clock())))
        for child in self.children:
            if self.alive(child.pid):
                self.signal_group(child.pid, signal.SIGKILL)
            try:
                child.wait(timeout=0.5)
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.warn(f'cannot reap leader {child.pid}: {exc}')
            # KILL delivery and orphan reaping are asynchronous. Verify with a
            # bounded wait, retrying KILL if live members remain.
            end = self.clock() + 0.3
            while self.live_members_remain(child.pid):
                if self.clock() >= end:
                    self.warn(f'group {child.pid} cleanup unverified: members may remain')
                    break
                self.signal_group(child.pid, signal.SIGKILL)
                self.sleep(0.01)
        try:
            if self.after_cleanup is not None:
                self.after_cleanup()
        finally:
            for child in self.children:
                for stream in (child.stdout, child.stderr, child.stdin):
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError as exc:
                            self.warn(f'cannot close child stream: {exc}')

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
