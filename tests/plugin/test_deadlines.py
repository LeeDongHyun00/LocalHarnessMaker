"""Injected shutdown tests plus a short real inherited-pipe regression tree."""
from __future__ import annotations
import json
import errno
import os
import sys
import time
from pathlib import Path
import signal
import subprocess
from typing import Any
import pytest
from plugin.hooks import _process
from plugin.hooks._config import OUTER
from plugin.hooks._process import CLEANUP_RESERVE
from plugin.hooks._runtime import Runtime, run_group


@pytest.mark.parametrize('ending', ['normal', 'timeout', 'exception', 'term', 'hup', 'int', 'spawn_signal'])
@pytest.mark.parametrize('cooperative', [False, True])
def test_owned_tree_shutdown(monkeypatch: pytest.MonkeyPatch, ending: str, cooperative: bool) -> None:
    ticks = [0.0]
    alive = {23456: True}
    sent: list[tuple[int, int, float]] = []
    handlers: dict[int, Any] = {sig: 'old' for sig in _process.SHUTDOWN_SIGNALS}
    initial = dict(handlers)
    reaped: list[float] = []

    def kill(pid: int, signum: int) -> None:
        if not alive[pid]:
            raise ProcessLookupError
        if signum:
            sent.append((pid, signum, ticks[0]))
            if cooperative or signum == signal.SIGKILL:
                alive[pid] = False

    def sleep(seconds: float) -> None:
        assert 0 <= seconds <= 1
        ticks[0] += seconds

    def install(signum: int, handler: Any) -> Any:
        previous = handlers[signum]
        handlers[signum] = handler
        return previous

    owner = _process.ChildGroups(clock=lambda: ticks[0], sleep=sleep, kill=kill, members=lambda group: [])
    monkeypatch.setattr(_process, 'ChildGroups', lambda: owner)
    monkeypatch.setattr(signal, 'signal', install)

    class Process:
        pid = 23456
        returncode = 0
        stdin = stdout = stderr = None

        def poll(self) -> int | None:
            return 0 if not alive[self.pid] else None

        def wait(self, timeout: float) -> int:
            reaped.append(timeout)
            return 0

        def communicate(self, **kwargs: Any) -> tuple[str, str]:
            if ending == 'timeout':
                ticks[0] += kwargs['timeout']
                raise subprocess.TimeoutExpired('fake', kwargs['timeout'])
            if ending == 'exception':
                raise OSError('pipe failed')
            if ending in {'term', 'hup', 'int'}:
                signum = {'term': signal.SIGTERM, 'hup': signal.SIGHUP, 'int': signal.SIGINT}[ending]
                handlers[signum](signum, None)
            return 'output', ''

    def popen(command: list[str], **kwargs: Any) -> Process:
        assert kwargs['start_new_session'] is True and kwargs['shell'] is False
        assert callable(handlers[signal.SIGHUP])
        if ending == 'spawn_signal':
            handlers[signal.SIGTERM](signal.SIGTERM, None)
        return Process()

    monkeypatch.setattr(subprocess, 'Popen', popen)
    if ending == 'normal':
        assert run_group(['fake'], timeout=1, shell=False, text=True).stdout == 'output'
    else:
        error = subprocess.TimeoutExpired if ending == 'timeout' else OSError if ending == 'exception' else SystemExit
        with pytest.raises(error):
            run_group(['fake'], timeout=1, shell=False, text=True)
    assert sent[0][1] == signal.SIGTERM
    assert [item[1] for item in sent] == ([signal.SIGTERM] if cooperative else [signal.SIGTERM, signal.SIGKILL])
    if not cooperative:
        assert sent[-1][2] - sent[0][2] == pytest.approx(2, abs=0.02)
    assert not alive[23456] and reaped == [0.5]
    assert handlers == initial


def test_all_owned_groups_are_terminated_before_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    dead: set[int] = set()
    sent: list[int] = []
    def kill(pid: int, signum: int) -> None:
        if pid in dead:
            raise ProcessLookupError
        if signum == signal.SIGTERM:
            sent.append(pid)
            dead.add(pid)
    class Process:
        stdin = stdout = stderr = None
        def __init__(self, pid: int) -> None:
            self.pid = pid
        def poll(self) -> int | None:
            return 0 if self.pid in dead else None
        def wait(self, timeout: float) -> int:
            assert sent == [1, 2]
            return 0
    owner = _process.ChildGroups(kill=kill, members=lambda group: [])
    owner.children = [Process(1), Process(2)]
    owner.cleanup()


def test_runtime_budgets_equal_registered_integer_timeouts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = json.loads((Path(__file__).resolve().parents[2] / 'plugin/hooks/hooks.json').read_text())
    for event in OUTER:
        monkeypatch.delenv(f'HARNESS_{event.upper()}_TIMEOUT', raising=False)
        registered = config['hooks'][event][0]['hooks'][0]['timeout']
        assert type(registered) is int
        runtime = Runtime({'cwd': str(tmp_path), 'session_id': 'test', 'hook_event_name': event}, clock=lambda: 0)
        assert runtime.deadline + CLEANUP_RESERVE == registered == OUTER[event]


def test_stop_cumulative_budget_with_injected_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('HARNESS_STUB', raising=False)
    monkeypatch.setenv('HARNESS_STOP_TIMEOUT', '660')
    ticks = [0.0]
    deadlines: list[float] = []
    def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs['env']['HARNESS_NESTED'] == '1'
        deadlines.append(kwargs['timeout'])
        ticks[0] += kwargs['timeout'] + 2.5  # Include cleanup in the fake elapsed budget.
        return subprocess.CompletedProcess(command, 0, str(tmp_path / 'out') + '\n', '')
    runtime = Runtime({'cwd': str(tmp_path), 'session_id': 'test', 'hook_event_name': 'Stop'},
                      runner=runner, clock=lambda: ticks[0])
    for module, operation in [('verifier', 'check'), ('controller', 'handoff'), ('verifier', 'validate-handoff')]:
        runtime.call(module, operation, [], tmp_path / 'out')
    assert deadlines == [480, 120, 5]
    ticks[0] = 655
    runtime.call('controller', 'handoff', [], tmp_path / 'out')
    assert deadlines[-1] == 1
    with pytest.raises(TimeoutError):
        runtime.call('controller', 'handoff', [], tmp_path / 'out')



@pytest.mark.parametrize('repeat', range(20))
def test_exited_child_with_grandchild_holding_pipes_returns_promptly(tmp_path: Path, repeat: int) -> None:
    """Leader exit, not inherited pipe EOF, must start group cleanup."""
    evidence = tmp_path / 'tree.json'
    ready = tmp_path / 'ready'
    grandchild = """
import pathlib, sys, time
pathlib.Path(sys.argv[1]).write_text('ready')
for _ in range(300):
    time.sleep(0.1)
"""
    child = """
import json, os, pathlib, subprocess, sys, time
process = subprocess.Popen([sys.executable, '-c', sys.argv[3], sys.argv[2]])
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid': process.pid, 'group': os.getpgrp()}))
for _ in range(500):
    if pathlib.Path(sys.argv[2]).exists():
        break
    time.sleep(0.01)
else:
    raise RuntimeError('grandchild did not start')
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid': process.pid, 'group': os.getpgrp(),
                                               'exiting_at': time.monotonic()}))
print('leader stdout', flush=True)
print('leader stderr', file=sys.stderr, flush=True)
sys.exit(3)
"""
    try:
        result = run_group([sys.executable, '-c', child, str(evidence), str(ready), grandchild],
                           timeout=10, shell=False, text=True, capture_output=True)
        tree = json.loads(evidence.read_text())
        elapsed = time.monotonic() - tree['exiting_at']
        assert result.returncode == 3
        assert result.stdout == 'leader stdout\n'
        assert result.stderr == 'leader stderr\n'
        assert ready.exists()
        assert elapsed < 3, f'waited {elapsed:.3f}s for inherited pipe EOF'
        pid = json.loads(evidence.read_text())['pid']
        # Orphan reaping belongs to init/launchd. Probe directly because this
        # sandbox blocks ps; on Linux, a zombie has exited but awaits init reap.
        def grandchild_alive() -> bool:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False
            stat = Path(f'/proc/{pid}/stat')
            try:
                if stat.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    return False
            except FileNotFoundError:
                pass
            return True
        reap_deadline = time.monotonic() + 0.5
        while grandchild_alive() and time.monotonic() < reap_deadline:
            time.sleep(0.01)
        assert not grandchild_alive(), f'grandchild {pid} survived cleanup'
    finally:
        if evidence.exists():
            tree = json.loads(evidence.read_text())
            try:
                os.killpg(tree['group'], signal.SIGKILL)
            except (PermissionError, ProcessLookupError):
                try:
                    os.kill(tree['pid'], signal.SIGKILL)
                except (PermissionError, ProcessLookupError):
                    pass


@pytest.mark.parametrize('failure', [errno.EPERM, errno.ESRCH])
@pytest.mark.parametrize('ending', ['normal', 'timeout', 'term', 'hup', 'int'])
@pytest.mark.parametrize('persistent', [False, True])
def test_group_errors_preserve_result_and_remove_members(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    failure: int, ending: str, persistent: bool,
) -> None:
    ticks = [0.0]
    live = {12340, 12341}
    polls: list[int] = []
    group_calls: list[int] = []
    pid_calls: list[tuple[int, int]] = []
    listings: list[set[int]] = []
    failed: set[int] = set()

    def kill_group(group: int, sig: int) -> None:
        assert polls, 'reap the leader before retrying killpg'
        group_calls.append(sig)
        if persistent or sig not in failed:
            failed.add(sig)
            raise OSError(failure, os.strerror(failure))
        if not live:
            raise ProcessLookupError(errno.ESRCH, 'gone')
        if sig == signal.SIGKILL:
            live.clear()

    def members(group: int) -> list[int]:
        listings.append(set(live))
        return sorted(live)

    def kill_pid(pid: int, sig: int) -> None:
        pid_calls.append((pid, sig))
        if sig == signal.SIGKILL:
            live.discard(pid)

    def sleep(seconds: float) -> None:
        ticks[0] += seconds

    owner = _process.ChildGroups(clock=lambda: ticks[0], sleep=sleep, kill=kill_group,
                                 members=members, kill_pid=kill_pid, get_group=lambda pid: 12340)
    monkeypatch.setattr(_process, 'ChildGroups', lambda: owner)

    class Process:
        pid = 12340
        returncode = 3
        stdin = stdout = stderr = None

        def poll(self) -> int | None:
            polls.append(self.pid)
            if ending == 'normal':
                live.discard(self.pid)
                return 3
            return None if self.pid in live else 3

        def wait(self, timeout: float) -> int:
            assert self.pid not in live
            return 3

        def communicate(self, **kwargs: Any) -> tuple[str, str]:
            if ending == 'timeout':
                ticks[0] += kwargs['timeout']
                raise subprocess.TimeoutExpired('fake', kwargs['timeout'])
            if ending != 'normal':
                owner.interrupted({'term': signal.SIGTERM, 'hup': signal.SIGHUP,
                                   'int': signal.SIGINT}[ending], None)
            return 'output', 'error'

    monkeypatch.setattr(subprocess, 'Popen', lambda *args, **kwargs: Process())
    if ending == 'normal':
        result = run_group(['fake'], timeout=0.1, text=True)
        assert (result.returncode, result.stdout, result.stderr) == (3, 'output', 'error')
    else:
        with pytest.raises(subprocess.TimeoutExpired if ending == 'timeout' else SystemExit):
            run_group(['fake'], timeout=0.1, text=True)
    assert not live
    assert signal.SIGTERM in group_calls and signal.SIGKILL in group_calls and 0 in group_calls
    assert listings and listings[-1] == set(), 'verify the final group is empty'
    if persistent:
        assert (12341, signal.SIGTERM) in pid_calls
        assert (12341, signal.SIGKILL) in pid_calls
    assert 'reaping/retrying' in capsys.readouterr().err
    assert ticks[0] < 3


def test_process_listing_filters_groups_and_zombies(monkeypatch: pytest.MonkeyPatch) -> None:
    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command == ['ps', '-A', '-o', 'pid=,pgid=,stat=']
        assert kwargs['shell'] is False and kwargs['timeout'] == 0.2
        return subprocess.CompletedProcess(command, 0, '  11 10 S\n12 10 Z+\n13 20 R\n', '')
    monkeypatch.setattr(subprocess, 'run', run)
    assert _process.ChildGroups.list_members(10) == [11]


@pytest.mark.parametrize('failure', [errno.EPERM, errno.ESRCH])
def test_individual_signal_errors_do_not_escape(
    capsys: pytest.CaptureFixture[str], failure: int,
) -> None:
    def deny(pid: int, sig: int) -> None:
        raise OSError(failure, os.strerror(failure))
    ticks = [0.0]
    def sleep(seconds: float) -> None:
        ticks[0] += seconds
    owner = _process.ChildGroups(kill=deny, kill_pid=deny, members=lambda group: [101],
                                 get_group=lambda pid: 100, clock=lambda: ticks[0], sleep=sleep)
    class Process:
        pid = 100
        stdin = stdout = stderr = None
        def poll(self) -> int:
            return 0
        def wait(self, timeout: float) -> int:
            raise OSError(failure, os.strerror(failure))
    owner.children = [Process()]
    owner.cleanup()
    assert 'cannot reap leader' in capsys.readouterr().err
    assert ticks[0] < 3
