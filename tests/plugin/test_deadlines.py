"""Injected shutdown tests plus a short real inherited-pipe regression tree."""
from __future__ import annotations
import json
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

    owner = _process.ChildGroups(clock=lambda: ticks[0], sleep=sleep, kill=kill)
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
        def wait(self, timeout: float) -> int:
            assert sent == [1, 2]
            return 0
    owner = _process.ChildGroups(kill=kill)
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



def test_exited_child_with_grandchild_holding_pipes_returns_promptly(tmp_path: Path) -> None:
    """Leader exit, not inherited pipe EOF, must start group cleanup."""
    evidence = tmp_path / 'tree.json'
    ready = tmp_path / 'ready'
    grandchild = """
import pathlib, sys, time
pathlib.Path(sys.argv[1]).write_text('ready')
for _ in range(100):
    time.sleep(0.1)
"""
    child = """
import json, os, pathlib, subprocess, sys, time
process = subprocess.Popen([sys.executable, '-c', sys.argv[3], sys.argv[2]])
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid': process.pid, 'group': os.getpgrp()}))
for _ in range(100):
    if pathlib.Path(sys.argv[2]).exists():
        break
    time.sleep(0.01)
else:
    raise RuntimeError('grandchild did not start')
print('leader stdout', flush=True)
print('leader stderr', file=sys.stderr, flush=True)
sys.exit(3)
"""
    started = time.monotonic()
    try:
        result = run_group([sys.executable, '-c', child, str(evidence), str(ready), grandchild],
                           timeout=5, shell=False, text=True, capture_output=True)
        elapsed = time.monotonic() - started
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
            group = json.loads(evidence.read_text())['group']
            try:
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                pass
