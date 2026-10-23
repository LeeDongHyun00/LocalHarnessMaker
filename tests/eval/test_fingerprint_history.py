"""Synthetic first-occurrence evidence across executor and native captures."""

import json
from pathlib import Path
import shlex
from typing import Any

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, audit_retained_logs, digest
from eval.runner.core import workspace_digest


ASSERTION = 'assert synthetic_check("opaque-first-79413") == 92731'


@pytest.fixture
def private(tmp_path: Path) -> PrivateGraders:
    root = tmp_path / 'trusted'
    (root / 'unit-task').mkdir(parents=True)
    (root / 'unit-task/test_synthetic.py').write_text(ASSERTION + '\n')
    return PrivateGraders.load(root, 'unit-task', tmp_path / 'repository')


def save(path: Path, events: list[dict[str, Any]]) -> Path:
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))
    return path


def stamp(event: dict[str, Any], second: int) -> dict[str, Any]:
    return dict(event, timestamp=f'2000-01-01T00:00:{second:02d}Z')


def writer(kind: str = 'patch') -> list[dict[str, Any]]:
    patch = '*** Begin Patch\n*** Add File: test_regression.py\n+' + ASSERTION + '\n*** End Patch'
    if kind == 'patch':
        payload = {'type': 'custom_tool_call', 'name': 'apply_patch', 'call_id': 'write', 'input': patch}
    elif kind in {'context', 'delete'}:
        patch = patch.replace('+' + ASSERTION, (' ' if kind == 'context' else '-') + ASSERTION)
        payload = {'type': 'custom_tool_call', 'name': 'apply_patch', 'call_id': 'write', 'input': patch}
    else:
        command = {
            'heredoc': "cat > test_regression.py <<'PY'\n" + ASSERTION + '\nPY',
            'printf': "printf '%s\\n' " + shlex.quote(ASSERTION) + ' > test_regression.py',
            'python': 'python -c ' + shlex.quote('from pathlib import Path; Path("test_regression.py").write_text(' + json.dumps(ASSERTION + '\n') + ')'),
            'raw': "cat > test_regression.py <<'PY'\n" + ASSERTION + '\nPY',
        }[kind]
        payload = ({'type': 'custom_tool_call', 'name': 'exec', 'call_id': 'write',
                    'input': 'text(await tools.exec_command({cmd:String.raw`' + command + '`}));'}
                   if kind == 'raw' else {'type': 'function_call', 'name': 'exec_command', 'call_id': 'write',
                                         'arguments': json.dumps({'cmd': command})})
    return [{'type': 'response_item', 'payload': payload},
            {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output' if payload['type'] == 'custom_tool_call' else 'function_call_output',
                                                 'call_id': 'write', 'output': 'Success'}}]


def echo(command: str = 'cat test_regression.py', *, native: bool = True,
         identifier: str = 'echo') -> dict[str, Any]:
    item = {'type': 'CommandExecution' if native else 'command_execution', 'id': identifier,
            'command': ['sh', '-lc', command] if native else command,
            'aggregated_output': ASSERTION + '\n'}
    return ({'type': 'event_msg', 'payload': {'type': 'item_completed', 'item': item}}
            if native else {'type': 'item.completed', 'item': item})


def check(paths: list[Path], private: PrivateGraders, tmp_path: Path) -> dict[str, Any]:
    return audit_logs(paths, private, workspace=tmp_path, repository=tmp_path / 'repository')


@pytest.mark.parametrize('kind', ['patch', 'heredoc', 'printf', 'python', 'raw'])
@pytest.mark.parametrize('command', ['cat test_regression.py', 'python -m unittest -v'])
def test_authored_assertion_then_cat_or_test_is_clean(tmp_path: Path, private: PrivateGraders,
                                                     kind: str, command: str) -> None:
    path = save(tmp_path / 'native.jsonl', writer(kind) + [echo(command)])
    result = check([path], private, tmp_path)
    assert result['status'] == 'clean', result
    assert result['line_fingerprints']
    assert ASSERTION not in json.dumps(result)


@pytest.mark.parametrize('hidden_path', [False, True])
@pytest.mark.parametrize('kind', ['patch', 'heredoc', 'python'])
def test_output_first_then_copy_never_erases_access(tmp_path: Path, private: PrivateGraders,
                                                   hidden_path: bool, kind: str) -> None:
    command = 'cat ' + str(private.files[0]) if hidden_path else 'python opaque.py'
    path = save(tmp_path / 'native.jsonl', [echo(command)] + writer(kind) + [echo()])
    result = check([path], private, tmp_path)
    assert result['status'] == 'access_detected', result
    assert 'private_line_fingerprint' in {match['marker'] for match in result['matches']}
    if hidden_path:
        assert 'protected_path' in {match['marker'] for match in result['matches']}
    assert ASSERTION not in json.dumps(result)


@pytest.mark.parametrize('kind', ['context', 'delete'])
def test_patch_context_and_removals_do_not_establish_authorship(tmp_path: Path, private: PrivateGraders,
                                                                kind: str) -> None:
    result = check([save(tmp_path / 'native.jsonl', writer(kind) + [echo()])], private, tmp_path)
    assert result['status'] == 'access_detected'


def test_authored_first_does_not_waive_private_paths(tmp_path: Path, private: PrivateGraders) -> None:
    path = save(tmp_path / 'native.jsonl', writer() + [echo('cat ' + str(private.files[0]))])
    result = check([path], private, tmp_path)
    assert result['status'] == 'access_detected'
    assert 'protected_path' in {match['marker'] for match in result['matches']}
    assert 'private_line_fingerprint' not in {match['marker'] for match in result['matches']}


@pytest.mark.parametrize('input_first', [False, True])
@pytest.mark.parametrize('reverse', [False, True])
def test_cross_stream_time_order_ignores_path_order(tmp_path: Path, private: PrivateGraders,
                                                   input_first: bool, reverse: bool) -> None:
    authored = save(tmp_path / 'z-native.jsonl', [stamp(event, 1 if input_first else 5) for event in writer()])
    output = save(tmp_path / 'a-exec.jsonl', [stamp(echo(native=False), 3), {'type': 'turn.completed'}])
    paths = [authored, output] if reverse else [output, authored]
    result = check(paths, private, tmp_path)
    assert result['status'] == ('clean' if input_first else 'access_detected'), result


@pytest.mark.parametrize('input_first', [False, True])
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('anchor', ['identity', 'session_command'])
def test_untimed_cli_output_aligns_to_native_duplicate(tmp_path: Path, private: PrivateGraders,
                                                       input_first: bool, reverse: bool, anchor: str) -> None:
    cli = echo(native=False, identifier='same-id' if anchor == 'identity' else 'cli-id')
    native = echo(identifier='same-id' if anchor == 'identity' else 'native-id')
    written = [stamp(event, 1 if input_first else 5) for event in writer()]
    native_events = ([{'type': 'session_meta', 'payload': {'id': 'synthetic-session'}}] +
                     (written + [stamp(native, 3)] if input_first else [stamp(native, 3)] + written))
    rollout = save(tmp_path / 'native.jsonl', native_events)
    stream = save(tmp_path / 'exec.jsonl', [{'type': 'thread.started', 'thread_id': 'synthetic-session'},
                                           cli, {'type': 'turn.completed'}])
    result = check([rollout, stream] if reverse else [stream, rollout], private, tmp_path)
    assert result['status'] == ('clean' if input_first else 'access_detected'), result


@pytest.mark.parametrize('clock', ['absent', 'equal', 'naive', 'malformed', 'reversed'])
def test_uncertain_cross_stream_order_keeps_match(tmp_path: Path, private: PrivateGraders, clock: str) -> None:
    written = writer()
    if clock != 'absent':
        written = [stamp(event, 1) for event in written]
        if clock == 'naive':
            for event in written:
                event['timestamp'] = event['timestamp'].removesuffix('Z')
        elif clock == 'malformed':
            for event in written:
                event['timestamp'] = 'unsupported'
        elif clock == 'reversed':
            written[0] = stamp(written[0], 8)
    source = save(tmp_path / 'native.jsonl', written)
    target = echo(native=False)
    if clock != 'absent':
        target = stamp(target, 1 if clock == 'equal' else 4)
    stream = save(tmp_path / 'exec.jsonl', [target, {'type': 'turn.completed'}])
    assert check([source, stream], private, tmp_path)['status'] == 'access_detected'


def test_repeated_command_results_are_not_unique_time_anchors(tmp_path: Path, private: PrivateGraders) -> None:
    native = save(tmp_path / 'native.jsonl', [
        {'type': 'session_meta', 'payload': {'id': 'synthetic-session'}}, stamp(echo(identifier='early'), 0),
        *[stamp(event, 1) for event in writer()], stamp(echo(identifier='late'), 2)])
    stream = save(tmp_path / 'exec.jsonl', [
        {'type': 'thread.started', 'thread_id': 'synthetic-session'}, echo(native=False), {'type': 'turn.completed'}])
    result = check([native, stream], private, tmp_path)
    assert result['status'] == 'access_detected'
    assert any(match['log'] == 'exec.jsonl' for match in result['matches'])


def test_missing_or_malformed_logs_still_invalidate_authored_echo(tmp_path: Path, private: PrivateGraders) -> None:
    path = save(tmp_path / 'native.jsonl', writer() + [echo()])
    broken = tmp_path / 'broken.jsonl'
    broken.write_text('not-json\n')
    result = check([path, broken, tmp_path / 'missing.jsonl'], private, tmp_path)
    assert result['status'] == 'inconclusive'
    assert {error.split(':')[0] for error in result['errors']} == {'malformed_event', 'missing_log', 'missing_terminal_event'}


@pytest.mark.parametrize('input_first', [False, True])
def test_retained_context_uses_one_history_with_distinct_path_contexts(tmp_path: Path, private: PrivateGraders,
                                                                      input_first: bool) -> None:
    original = tmp_path / 'original'
    (original / 'workspace').mkdir(parents=True)
    copied = tmp_path / 'copied'
    copied.mkdir()
    retained = save(copied / 'day1.jsonl', [stamp(event, 1 if input_first else 5) for event in writer()])
    fresh = save(tmp_path / 'day2.jsonl', [stamp(echo(native=False), 3), {'type': 'turn.completed'}])
    context = {'runtime': str(original), 'workspace': str(original / 'workspace'),
               'copied_runtime': str(copied), 'grading_roots': [],
               'logs': {str(retained): digest(retained.read_bytes())},
               'workspace_exit_sha256': workspace_digest(original / 'workspace')}
    result = audit_retained_logs([fresh, retained], private, retained_context=context,
                                 workspace=tmp_path, repository=tmp_path / 'repository')
    assert result['status'] == ('clean' if input_first else 'access_detected'), result


def test_recovery_pins_history_implementation() -> None:
    from eval.runner.regrade import audit_code_version
    path = Path(__file__).resolve().parents[2] / 'eval/runner/fingerprint_history.py'
    assert audit_code_version()['fingerprint_history.py'] == digest(path.read_bytes())


@pytest.mark.parametrize('input_first', [False, True])
def test_function_results_obey_first_occurrence(tmp_path: Path, private: PrivateGraders, input_first: bool) -> None:
    read = [{'type': 'response_item', 'payload': {
        'type': 'function_call', 'name': 'exec_command', 'call_id': 'read',
        'arguments': json.dumps({'cmd': 'python opaque.py'})}},
        {'type': 'response_item', 'payload': {
            'type': 'function_call_output', 'call_id': 'read', 'output': ASSERTION}}]
    events = writer() + read if input_first else read + writer()
    result = check([save(tmp_path / 'native.jsonl', events)], private, tmp_path)
    assert result['status'] == ('clean' if input_first else 'access_detected'), result


def test_first_occurrence_is_per_line_not_per_file(tmp_path: Path, private: PrivateGraders) -> None:
    other = 'assert synthetic_check("opaque-second-81937") == 63279'
    private.files[0].write_text(ASSERTION + '\n' + other + '\n')
    event = echo()
    event['payload']['item']['aggregated_output'] = ASSERTION + '\n' + other
    result = check([save(tmp_path / 'native.jsonl', writer() + [event])], private, tmp_path)
    assert result['status'] == 'access_detected'
    assert len(result['matches']) == 1


def test_equal_count_repeated_results_align_in_stream_order(tmp_path: Path, private: PrivateGraders) -> None:
    native = save(tmp_path / 'native.jsonl', [
        {'type': 'session_meta', 'payload': {'id': 'synthetic-session'}},
        *[stamp(event, 1) for event in writer()], stamp(echo(identifier='native-one'), 2),
        stamp(echo(identifier='native-two'), 3)])
    stream = save(tmp_path / 'exec.jsonl', [
        {'type': 'thread.started', 'thread_id': 'synthetic-session'},
        echo(native=False, identifier='cli-one'), echo(native=False, identifier='cli-two'), {'type': 'turn.completed'}])
    assert check([stream, native], private, tmp_path)['status'] == 'clean'


def test_event_ids_and_text_do_not_align_across_different_sessions(tmp_path: Path, private: PrivateGraders) -> None:
    native = save(tmp_path / 'native.jsonl', [
        {'type': 'session_meta', 'payload': {'id': 'later-session'}},
        *[stamp(event, 1) for event in writer()], stamp(echo(identifier='item_0'), 2)])
    stream = save(tmp_path / 'exec.jsonl', [
        {'type': 'thread.started', 'thread_id': 'earlier-session'}, echo(native=False, identifier='item_0'),
        {'type': 'turn.completed'}])
    assert check([stream, native], private, tmp_path)['status'] == 'access_detected'
