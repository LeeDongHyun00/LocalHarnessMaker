"""Interrupted counters remain bounded evidence, never a price input."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core
from eval.runner.telemetry import recover_partial_usage, collect_runs, interrupted_pricing_evidence
from eval.runner.report import usage
from tests.eval.test_runner import setup, Executor
from tests.eval.test_restart_recovery import VERSION


def token_event(second: int, count: int) -> dict[str, Any]:
    """Create cumulative session counters, including overlapping reasoning."""
    return {'timestamp': f'2026-10-23T00:00:{second:02d}Z', 'type': 'event_msg',
            'payload': {'type': 'token_count', 'info': {'total_token_usage': {
                'input_tokens': count, 'cached_input_tokens': 1, 'output_tokens': 3,
                'reasoning_output_tokens': 2, 'total_tokens': count + 3}}}}


def test_last_cumulative_per_rollout_with_strict_process_bounds(tmp_path: Path) -> None:
    first, second = tmp_path / 'one.jsonl', tmp_path / 'two.jsonl'
    events = [token_event(s, n) for s, n in [(0, 5), (2, 7), (3, 11), (6, 1000)]]
    first.write_text(''.join(json.dumps(e) + '\n' for e in events))
    second.write_text(json.dumps(token_event(4, 19)) + '\n')
    segment = {'attempt': 1, 'interrupted': True, 'started_at': '2026-10-23T00:00:01+00:00',
               'exited_at': '2026-10-23T00:00:05+00:00'}
    normal = dict(segment, interrupted=False, exit_code=0, attempt=2)
    recover_partial_usage([segment, normal], [first, second])
    partial = segment['partial_usage']
    assert partial['lower_bound'] is True and 'Lower bound' in partial['note']
    assert [o['tokens']['input_tokens'] for o in partial['rollouts']] == [11, 19]
    assert partial['rollouts'][0]['tokens']['reasoning_output_tokens'] == 2
    assert 'partial_usage' not in normal and 'native_usage' not in segment
    before = copy.deepcopy(segment)
    recover_partial_usage([segment], [first, second])
    assert segment == before
    cli = tmp_path / 'exec.jsonl'
    cli.write_text('{"type":"thread.started","thread_id":"synthetic"}\n')
    pricing = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    assert usage(cli, 1, 'gpt-6.1-sol', pricing, tier='standard')['usd'] is None
    run = collect_runs([cli], [first, second], [segment])[0]
    assert run['tokens'] is None and run['partial_usage'] == partial


@pytest.mark.parametrize('case', ['no_tokens', 'missing_time', 'naive', 'outside', 'bad_counts'])
def test_unattributable_or_absent_records_do_not_invent_partial_usage(tmp_path: Path, case: str) -> None:
    segment = {'exit_code': -2, 'started_at': '2026-10-23T00:00:01Z', 'exited_at': '2026-10-23T00:00:05Z'}
    event = token_event(2, 7)
    if case == 'no_tokens':
        event['payload']['info'] = None
    elif case == 'missing_time':
        event.pop('timestamp')
    elif case == 'naive':
        segment['exited_at'] = '2026-10-23T00:00:05'
    elif case == 'outside':
        event = token_event(6, 100)
    else:
        event['payload']['info']['total_token_usage']['input_tokens'] = True
    native = tmp_path / 'native.jsonl'
    native.write_text(json.dumps(event) + '\n')
    recover_partial_usage([segment], [native])
    assert 'partial_usage' not in segment


@pytest.mark.parametrize('hard', [False, True])
def test_runtime_interruption_and_resume_keep_partial_counters_unpriced(
        setup: tuple[Path, Path, Path], hard: bool) -> None:
    root, config, out = setup
    executor = Executor(interrupt=not hard)

    def stop(argv: list[str], **kwargs: Any) -> Any:
        try:
            executor(argv, **kwargs)
        except KeyboardInterrupt:
            pass
        # Simulate a native record written before host loss; it never reaches
        # turn.completed. Hard loss bypasses the runner's post-call capture.
        kwargs['stdout'].write_text('{"type":"thread.started","thread_id":"unit-session"}\n')
        event = token_event(2, 17)
        event['timestamp'] = core.now()
        native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
        with native.open('a') as stream:
            stream.write(json.dumps(event) + '\n')
        if hard:
            raise RuntimeError('host restart')
        raise KeyboardInterrupt

    with pytest.raises(RuntimeError if hard else core.IncompleteRun):
        core.run(config, out, root, execute=stop, version=VERSION)
    if not hard:
        result = json.loads((out / 'bug-chunk-tail/result.json').read_text())
        assert result['segments'][0]['partial_usage']['lower_bound'] is True
        assert 'native_usage' not in result['segments'][0]
    resumed = json.loads(core.run(config, out, root, execute=Executor(), version=VERSION).read_text())
    task = resumed['tasks'][0]
    assert task['outcome'] == 'pass' and task['costs']['executor_usd'] is None
    checkpoint = json.loads((out / 'checkpoint.json').read_text())
    segment = checkpoint['tasks']['bug-chunk-tail']['segments'][0]
    assert segment['partial_usage']['rollouts'][0]['tokens']['input_tokens'] == 17
    assert 'native_usage' not in segment


@pytest.mark.parametrize('tiers', [['standard'], ['priority'], ['standard', 'priority'], [None], [{'bad': 1}]])
def test_interrupted_price_capture_needs_bounded_unambiguous_observations(tmp_path: Path, tiers: list[Any]) -> None:
    native = tmp_path / 'native.jsonl'
    events = [{'type': 'event_msg', 'timestamp': '2026-10-23T00:00:02Z',
               'payload': {'type': 'thread_settings_applied', 'thread_settings': {'service_tier': tier}}}
              for tier in tiers]
    # A later resume's tier cannot recover the earlier process's price.
    events.append({'type': 'event_msg', 'timestamp': '2026-10-23T00:00:06Z',
                   'payload': {'type': 'thread_settings_applied', 'thread_settings': {'service_tier': 'fast'}}})
    native.write_text(''.join(json.dumps(e) + '\n' for e in events))
    segment = {'started_at': '2026-10-23T00:00:01Z', 'exited_at': '2026-10-23T00:00:05Z'}
    found = interrupted_pricing_evidence(segment, [native])
    if len(tiers) == 1 and isinstance(tiers[0], str):
        assert found['tier'] == tiers[0] and len(found['records']) == 1
    else:
        assert found is None
