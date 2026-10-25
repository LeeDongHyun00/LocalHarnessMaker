"""Every exported stream is an immutable, sanitized parser regression.

The checked-in synthetic seed proves the pipeline only. Host exports add one
file per retained report; this test discovers them without a manifest update.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.corpus_export import (Redactor, assert_safe, audit_record, canonical,
                                       content_hash, export_report, extract, main, write_records)

CORPUS = Path(__file__).parent / 'fixtures/corpus'
FILES = sorted(CORPUS.glob('*.jsonl'))
CASES = [(path.name, row) for path in FILES for row in map(json.loads, path.read_text().splitlines())]


def test_corpus_is_present() -> None:
    assert FILES and CASES, 'The corpus must not disappear or become empty'
    assert all(path.stat().st_size for path in FILES)
    ids = [row['id'] for _, row in CASES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(('filename', 'record'), CASES, ids=[row['id'] for _, row in CASES])
def test_corpus_regression(filename: str, record: dict[str, Any]) -> None:
    assert_safe(record)
    assert record['content_sha256'] == content_hash(record), filename
    assert audit_record(record) == record['expected'], (
        f"{record['id']}: review parser change; deliberately re-export with --rebaseline RECORD_ID")


def command(value: str) -> dict[str, Any]:
    return {'type': 'item.completed', 'item': {'id': 'cmd', 'type': 'command_execution',
            'command': value, 'aggregated_output': 'synthetic output', 'exit_code': 0}}


def script(call_id: str, source: str) -> list[dict[str, Any]]:
    return [{'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'exec',
             'call_id': call_id, 'input': source}},
            {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
             'call_id': call_id, 'output': ''}}]


def fixture_report(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    report = tmp_path / 'reports/synthetic'
    report.mkdir(parents=True)
    runtime = tmp_path / 'host-temp/runtime'
    runtime.mkdir(parents=True)
    events = [command('cat own.py'), command('cat "$UNRESOLVED"')]
    (runtime / 'events.jsonl').write_bytes(b''.join(canonical(e) + b'\n' for e in events))
    sessions = runtime / 'codex-home/sessions/nested'
    sessions.mkdir(parents=True)
    events = script('a', 'store("file","own.py");') + script(
        'b', 'text(await tools.exec_command({cmd:"cat " + load("file")}));')
    events += [command('cat ' + str(tmp_path / 'repository/secret'))]
    (sessions / 'rollout.jsonl').write_bytes(b''.join(canonical(e) + b'\n' for e in events))
    (report / 'checkpoint.json').write_text(json.dumps({'tasks': {'task': {
        'runtime': str(runtime), 'segments': [{'events': 'events.jsonl'}]}}}))
    (report / 'report.json').write_text(json.dumps({'tasks': [{'task_id': 'task'}]}))
    options = dict(home=tmp_path / 'home', temp=tmp_path / 'host-temp',
                   repository=tmp_path / 'repository', private_roots=[tmp_path / 'hidden'],
                   markers=['SECRET_PRIVATE_SENTINEL'])
    return report, options


def test_checkpoint_export_covers_both_streams_and_preserves_stores(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    rows = export_report(report, **options)
    assert len(rows) == 2
    assert {r['expected']['status'] for r in rows} == {'inconclusive', 'access_detected'}
    native = rows[1]
    assert len(native['events']) == 5
    assert native['expected']['error_kinds'] == []  # load resolves from earlier call
    assert native['expected']['markers'] == ['protected_path']
    assert '__REPOSITORY__' in json.dumps(native)
    assert str(tmp_path) not in json.dumps(rows)
    for row in rows:
        assert_safe(row)
        assert row['expected'] == audit_record(row)
        assert row['content_sha256'] == content_hash(row)


def test_redaction_drops_private_lines_before_extracting_and_caps_outputs(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    redactor = Redactor(runtime=runtime, **options)
    event = command('cat ' + str(options['home'] / 'public.txt'))
    event['item']['aggregated_output'] = 'x' * 3000
    native = {'type': 'event_msg', 'payload': {'type': 'item_completed', 'item': {
        'type': 'CommandExecution', 'command': 'echo safe', 'aggregated_output': 'y' * 3000}}}
    forbidden = [command('cat ' + str(options['private_roots'][0] / 'source.py')),
                 command('echo SECRET_PRIVATE_SENTINEL'), command('echo hidden'),
                 command('echo %53ECRET_PRIVATE_SENTINEL'),
                 command('echo \\u0053ECRET_PRIVATE_SENTINEL')]
    log = tmp_path / 'input.jsonl'
    log.write_bytes(b''.join(canonical(e) + b'\n' for e in [event, native, *forbidden]))
    rows, dropped = extract(log, redactor)
    assert dropped == 5 and len(rows) == 2
    assert len(rows[0]['item']['aggregated_output']) == 2000
    assert len(rows[1]['payload']['item']['aggregated_output']) == 2000
    assert '__HOME__' in rows[0]['item']['command']
    assert_safe(rows)


@pytest.mark.parametrize('text', ['cat /Users/person/secret', 'cat /tmp/secret',
                                 'cat /private/var/folders/secret', 'cat /scratch/custom/location', '<private_root>'])
def test_safety_gate_rejects_leaks(text: str) -> None:
    with pytest.raises(ValueError, match='Unsafe'):
        assert_safe({'events': [text]})


def test_rebaseline_requires_specific_record_and_lists_changes(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    rows = export_report(report, **options)
    path = tmp_path / 'output.jsonl'
    assert len(write_records(path, rows, set())) == 2
    before = path.read_bytes()
    assert write_records(path, rows, set()) == []
    rows[0]['expected']['status'] = 'clean'
    with pytest.raises(ValueError, match='--rebaseline'):
        write_records(path, rows, {'wrong-id'})
    assert path.read_bytes() == before
    changes = write_records(path, rows, {rows[0]['id']})
    assert len(changes) == 1
    assert changes[0]['before']['expected']['status'] == 'inconclusive'
    assert changes[0]['after']['expected']['status'] == 'clean'
    with pytest.raises(ValueError, match='removed'):
        write_records(path, rows[:1], set())


def test_missing_runtime_fails_without_fixture_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                    capsys: pytest.CaptureFixture[str]) -> None:
    report, options = fixture_report(tmp_path)
    state = json.loads((report / 'checkpoint.json').read_text())
    state['tasks']['task']['runtime'] = str(tmp_path / 'unavailable')
    (report / 'checkpoint.json').write_text(json.dumps(state))
    output = tmp_path / 'corpus'
    monkeypatch.setattr('sys.argv', ['corpus_export', '--reports-root', str(report.parent),
        '--report', report.name, '--output', str(output), '--private-root', str(options['private_roots'][0]),
        '--private-marker', options['markers'][0]])
    assert main() == 1
    assert not output.exists()
    assert str(tmp_path) not in capsys.readouterr().err


def test_redaction_preserves_javascript_regex_and_escape_syntax(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    source = r'const hits=[..."abc".matchAll(/^([a-z]+)$/gm)]; const unicode="\u0061";'
    redactor = Redactor(runtime=runtime, **options)
    assert redactor.text(source, code=True) == source


def test_structured_outputs_have_total_character_budget(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    event = script('one', 'text("output");')[1]
    event['payload']['output'] = [{'type': 'input_text', 'text': 'x' * 1500}] * 3
    log = tmp_path / 'large.jsonl'
    log.write_bytes(canonical(event) + b'\n')
    # Supply the matching call before its output.
    log.write_bytes(canonical(script('one', 'text("output");')[0]) + b'\n' + log.read_bytes())
    rows, _ = extract(log, Redactor(runtime=runtime, **options))
    assert len(rows[1]['payload']['output']) == 2000


def test_cli_export_and_explicit_rebaseline_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    report, options = fixture_report(tmp_path)
    output = tmp_path / 'corpus'
    argv = ['corpus_export', '--reports-root', str(report.parent), '--report', report.name,
            '--output', str(output), '--home', str(options['home']), '--temp-root', str(options['temp']),
            '--repository', str(options['repository']), '--private-root', str(options['private_roots'][0]),
            '--private-marker', options['markers'][0]]
    monkeypatch.setattr('sys.argv', argv)
    assert main() == 0
    initial = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(initial) == 2 and all(c['before'] is None for c in initial)
    path = output / 'synthetic.jsonl'
    old = path.read_bytes()
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    (runtime / 'events.jsonl').write_bytes(canonical(command('cat changed.py')) + b'\n')
    assert main() == 1
    failure = capsys.readouterr()
    record_id = initial[0]['id']
    assert record_id in failure.err and path.read_bytes() == old
    monkeypatch.setattr('sys.argv', argv + ['--rebaseline', record_id])
    assert main() == 0
    changes = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(changes) == 1 and changes[0]['id'] == record_id
    assert changes[0]['before']['expected']['status'] == 'inconclusive'
    assert changes[0]['after']['expected']['status'] == 'clean'
    assert_safe(changes)


def test_ci_checks_host_supplied_marker_without_storing_marker_text(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    row = export_report(report, **options)[0]
    assert 'SECRET_PRIVATE_SENTINEL' not in json.dumps(row)
    assert row['marker_guards']
    row['events'][0]['item']['aggregated_output'] = 'secret_private_sentinel'
    with pytest.raises(ValueError, match='Unsafe'):
        assert_safe(row)


@pytest.mark.parametrize('variable', ['LHM_PRIVATE_GRADERS', 'LHM_PRIVATE_V3'])
def test_runtime_private_basename_is_forbidden(variable: str, tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    report, options = fixture_report(tmp_path)
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    monkeypatch.setenv(variable, str(tmp_path / 'neutral-vault'))
    redactor = Redactor(runtime=runtime, **options)
    for text in ('NEUTRAL-VAULT', 'neutral%2dvault', r'neutral\u002dvault'):
        assert redactor.forbidden_line(text)
        with pytest.raises(ValueError, match='Unsafe'):
            assert_safe({'events': [text]})
    monkeypatch.setenv(variable, str(tmp_path / 'another-vault'))
    with pytest.raises(ValueError, match='Unsafe'):
        assert_safe({'events': ['another-vault']})


def test_supplied_private_root_basename_is_forbidden(tmp_path: Path) -> None:
    report, options = fixture_report(tmp_path)
    runtime = Path(json.loads((report / 'checkpoint.json').read_text())['tasks']['task']['runtime'])
    assert Redactor(runtime=runtime, **options).forbidden_line('echo hidden')
