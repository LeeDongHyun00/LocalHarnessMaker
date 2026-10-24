"""Session-authored FILE headers, output provenance and hostile computed paths."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, digest
from eval.runner.javascript_derived import PATTERNS, concrete, manifest_matches, reduce_script
from tests.eval.test_access_audit import private


FIXTURES = Path(__file__).parent / 'fixtures'
SOURCES = ''.join('FILE ' + name + ' SHA256 ' + 'a' * 64 + '\n# synthetic source\n'
                  for name in ['README.md', 'verify.py', 'test_public.py', 'project/compat.py'])
RECORD_HASHES = {
    1: 'a804a466d4840c4995cb21d8372b92984817db5a617c1aa5a1e3e7cfe0377e7f',
    2: '6b6d08cbd92cc81394f0eee8c6c33182df81dbbae89c03e44178767245beba15',
}


def run_scripts(tmp_path: Path, private: PrivateGraders,
                scripts: list[tuple[str, Any]], *, session: str = 'synthetic') -> dict[str, Any]:
    workspace = tmp_path / 'workspace'
    workspace.mkdir(exist_ok=True)
    rows: list[dict[str, Any]] = [{'type': 'session_meta', 'payload': {'id': session}}]
    for i, (source, output) in enumerate(scripts):
        rows.append({'type': 'response_item', 'payload': {
            'type': 'custom_tool_call', 'name': 'exec', 'call_id': f'call-{i}', 'input': source}})
        rows.append({'type': 'response_item', 'payload': {
            'type': 'custom_tool_call_output', 'call_id': f'call-{i}', 'output': output}})
    log = tmp_path / 'synthetic.jsonl'
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    return audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository')


def stored(value: str = SOURCES, helper: str = 'store') -> str:
    return f'{helper}("original_sources",{json.dumps(value)});'


@pytest.mark.parametrize('record', [1, 2])
@pytest.mark.parametrize('helper', ['store', 'save'])
def test_retained_records_resolve_only_with_session_store(tmp_path: Path, private: PrivateGraders,
                                                          record: int, helper: str) -> None:
    source = (FIXTURES / f'derived-record-{record}.js').read_text()
    assert digest(source.encode()) == RECORD_HASHES[record]
    result = run_scripts(tmp_path, private, [(stored(helper=helper), ''), (source, '')])
    assert result['status'] == 'clean', result
    assert result['errors'] == result['matches'] == []
    assert [(r['line'], r['reason']) for r in result['resolutions'] if r['line'] == 4] == [
        (4, 'derived_from_audited_outputs')]
    reduced = reduce_script(source, {'original_sources': SOURCES})
    assert reduced is not None and len(reduced.commands) == (2 if record == 1 else 1)
    assert all('None' not in command['cmd'] for command in reduced.commands)
    if record == 1:
        assert reduced.commands[0]['cmd'] == 'python verify.py'
        expected = {name: 'a' * 64 for name in ['README.md', 'verify.py', 'test_public.py', 'project/compat.py']}
        assert 'expected = ' + json.dumps(expected, separators=(',', ':')) + '\n' in reduced.commands[1]['cmd']
    else:
        assert 'original = json.loads(' in reduced.commands[0]['cmd']
        assert 'verification.json' in reduced.commands[0]['cmd']


@pytest.mark.parametrize('record', [1, 2])
def test_verbatim_alone_has_no_proven_load_source(tmp_path: Path, private: PrivateGraders, record: int) -> None:
    source = (FIXTURES / f'derived-record-{record}.js').read_text()
    result = run_scripts(tmp_path, private, [(source, '')])
    assert result['status'] == 'inconclusive', result
    assert result['resolutions'] == []
    assert 'unresolved_custom_input:synthetic.jsonl:2' in result['errors']


def test_same_script_literal_store_and_computed_command(tmp_path: Path, private: PrivateGraders) -> None:
    source = stored('solution.py') + 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    result = run_scripts(tmp_path, private, [(source, '')])
    assert result['status'] == 'clean', result
    assert result['resolutions'][0]['reason'] == 'derived_from_audited_outputs'


@pytest.mark.parametrize('record', [1, 2])
def test_load_can_come_from_paired_audited_tool_result(tmp_path: Path, private: PrivateGraders, record: int) -> None:
    bootstrap = ('const result = await tools.exec_command({cmd:"cat source-manifest.txt"});'
                 'store("original_sources",result.output); text(result);')
    output = [{'type': 'text', 'text': json.dumps({'output': SOURCES})}]
    source = (FIXTURES / f'derived-record-{record}.js').read_text()
    result = run_scripts(tmp_path, private, [(bootstrap, output), (source, '')])
    assert result['status'] == 'clean', result
    assert result['resolutions'][-1]['line'] == 4


def test_private_path_through_tool_result_is_detected_at_source(tmp_path: Path, private: PrivateGraders) -> None:
    bootstrap = ('const result = await tools.exec_command({cmd:"cat source-manifest.txt"});'
                 'store("original_sources",result.output); text(result);')
    output = [{'type': 'text', 'text': json.dumps({'output': str(private.root / 'test_synthetic.py')})}]
    computed = 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    result = run_scripts(tmp_path, private, [(bootstrap, output), (computed, '')])
    assert result['status'] == 'access_detected', result
    assert any(match['line'] == 3 and match['tool'] == 'exec' for match in result['matches'])
    assert not any(match['line'] == 2 for match in result['matches'])


@pytest.mark.parametrize('source', [
    'process.env.PATH', 'process.argv[1]', 'fetch("https://synthetic.invalid")',
    'fs.readFileSync("solution.py")', 'readFile("solution.py")',
    'load("never_stored")', 'globalThis.secret', 'Deno.env.get("secret")',
])
def test_unknown_source_stays_inconclusive(tmp_path: Path, private: PrivateGraders, source: str) -> None:
    script = f'const unknown = {source}; await tools.exec_command({{cmd:"cat " + unknown}});'
    result = run_scripts(tmp_path, private, [(stored(), ''), (script, '')])
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:4' in result['errors']


@pytest.mark.parametrize('mutation', [
    'const tools = other;', 'tools.exec_command = other;', 'const run = tools.exec_command;',
    'const JSON = other;', 'JSON.stringify = other;',
    'const load = other;', 'eval("opaque");', 'Function("opaque")();',
    'const alias = tools; alias.exec_command({cmd:"cat solution.py"});',
    'await tools[load("original_sources")]({cmd:"cat solution.py"});',
    'await tools["exec_command"]({cmd:"cat solution.py"});',
    'await tools.unknown_tool({path:"solution.py"});',
])
def test_reflection_aliases_and_unknown_tools_are_not_exempt(tmp_path: Path, private: PrivateGraders,
                                                           mutation: str) -> None:
    script = mutation + 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    result = run_scripts(tmp_path, private, [(stored('solution.py'), ''), (script, '')])
    assert result['status'] == 'inconclusive', result


def test_pure_computation_can_synthesize_private_path_and_is_still_audited(tmp_path: Path,
                                                                        private: PrivateGraders) -> None:
    # Neither input fragment names the private root. Provenance alone is unsafe.
    path = str(private.root / 'synthetic.py')
    middle = len(path) // 2
    script = ('const left = ' + json.dumps(path[:middle]) + '; const right = ' + json.dumps(path[middle:]) +
              '; await tools.exec_command({cmd:"cat " + left + right});')
    result = run_scripts(tmp_path, private, [(script, '')])
    assert result['status'] == 'access_detected', result
    assert any(match['line'] == 2 and match['marker'] == 'protected_path' for match in result['matches'])


@pytest.mark.parametrize('record', [1, 2])
def test_literal_call_is_audited_even_when_another_call_is_unresolved(tmp_path: Path,
                                                                   private: PrivateGraders, record: int) -> None:
    script = (FIXTURES / f'derived-record-{record}.js').read_text()
    script += '\nawait tools.exec_command({cmd:' + json.dumps('cat ' + str(private.root)) + '});'
    result = run_scripts(tmp_path, private, [(script, '')])
    assert result['status'] == 'access_detected', result
    assert any(error.startswith('unresolved_custom_input:') for error in result['errors'])


@pytest.mark.parametrize('output', ['', '{truncated', [{'type': 'text', 'text': '{}'}, {'type': 'text', 'text': '{}'}]])
def test_unobserved_tool_value_never_becomes_a_load_source(tmp_path: Path, private: PrivateGraders,
                                                        output: Any) -> None:
    bootstrap = ('const result = await tools.exec_command({cmd:"cat source-manifest.txt"});'
                 'store("original_sources",result.output); text(result);')
    source = (FIXTURES / 'derived-record-1.js').read_text()
    result = run_scripts(tmp_path, private, [(bootstrap, output), (source, '')])
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:4' in result['errors']


def test_unsupported_script_invalidates_previous_store(tmp_path: Path, private: PrivateGraders) -> None:
    source = (FIXTURES / 'derived-record-1.js').read_text()
    result = run_scripts(tmp_path, private, [(stored(), ''), ('store("original_sources", external);', ''), (source, '')])
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:6' in result['errors']


def test_store_does_not_cross_logs_or_session_identity(tmp_path: Path, private: PrivateGraders) -> None:
    result = run_scripts(tmp_path, private, [(stored(), '')])
    assert result['status'] == 'clean'
    first = tmp_path / 'first.jsonl'
    (tmp_path / 'synthetic.jsonl').rename(first)
    source = (FIXTURES / 'derived-record-1.js').read_text()
    run_scripts(tmp_path, private, [(source, '')], session='another')
    result = audit_logs([first, tmp_path / 'synthetic.jsonl'], private, workspace=tmp_path / 'workspace')
    assert result['status'] == 'inconclusive', result
    rows = [json.loads(line) for line in first.read_text().splitlines()]
    rows.extend(json.loads(line) for line in (tmp_path / 'synthetic.jsonl').read_text().splitlines())
    first.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result = audit_logs([first], private, workspace=tmp_path / 'workspace')
    assert result['status'] == 'inconclusive', result


def test_unpaired_or_overlapping_store_cannot_establish_provenance(tmp_path: Path, private: PrivateGraders) -> None:
    source = (FIXTURES / 'derived-record-1.js').read_text()
    run_scripts(tmp_path, private, [(stored(), ''), (source, '')])
    log = tmp_path / 'synthetic.jsonl'
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    rows[2], rows[3] = rows[3], rows[2]
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result = audit_logs([log], private, workspace=tmp_path / 'workspace')
    assert result['status'] == 'inconclusive', result
    assert 'overlapping_code_mode_scripts:synthetic.jsonl:3' in result['errors']


def test_unrelated_external_read_prevents_computed_call_exemption(tmp_path: Path, private: PrivateGraders) -> None:
    source = ('const unused = process.env.SECRET; '
              'await tools.exec_command({cmd:"cat " + load("original_sources")});')
    result = run_scripts(tmp_path, private, [(stored('solution.py'), ''), (source, '')])
    assert result['status'] == 'inconclusive', result
    assert not result['resolutions']


@pytest.mark.parametrize('failure', ['Script error: synthetic failure', 'Script running with cell ID synthetic', 'flag'])
def test_failed_or_yielded_script_cannot_confirm_a_store(tmp_path: Path, private: PrivateGraders,
                                                       failure: str) -> None:
    computed = 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    run_scripts(tmp_path, private, [(stored(), ''), (stored('other.py'), failure), (computed, '')])
    log = tmp_path / 'synthetic.jsonl'
    if failure == 'flag':
        rows = [json.loads(line) for line in log.read_text().splitlines()]
        rows[4]['payload']['is_error'] = True
        log.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    result = audit_logs([log], private, workspace=tmp_path / 'workspace')
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:6' in result['errors']


def test_transformed_display_cannot_substitute_for_raw_tool_output(tmp_path: Path, private: PrivateGraders) -> None:
    bootstrap = ('const result = await tools.exec_command({cmd:"cat source-manifest.txt"});'
                 'store("original_sources",result.output); text({...result,output:"safe"});')
    computed = 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    result = run_scripts(tmp_path, private, [(bootstrap, json.dumps({'output': 'safe'})), (computed, '')])
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:4' in result['errors']


def test_missing_result_overwrite_drops_old_key(tmp_path: Path, private: PrivateGraders) -> None:
    overwrite = ('const result = await tools.exec_command({cmd:"cat source-manifest.txt"});'
                 'store("original_sources",result.output);')
    computed = 'await tools.exec_command({cmd:"cat " + load("original_sources")});'
    result = run_scripts(tmp_path, private, [(stored('old.py'), ''), (overwrite, ''), (computed, '')])
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:6' in result['errors']


def test_regrade_pins_the_new_static_reducer() -> None:
    from eval.runner.regrade import audit_code_version
    from eval.runner.audit import digest
    path = Path(__file__).parents[2] / 'eval/runner/javascript_derived.py'
    assert audit_code_version()['javascript_derived.py'] == digest(path.read_bytes())


@pytest.mark.parametrize('pattern', sorted(PATTERNS))
@pytest.mark.parametrize('tail', ['hello\nworld\n', '\n\n', '   trailing', ' hello\r\n\tlast\n', 'x\nFILE invalid\ny'])
def test_manifest_reduction_preserves_measured_regexp_semantics(pattern: str, tail: str) -> None:
    source = 'FILE own.py SHA256 ' + 'a' * 64 + '\n' + tail + '\n' + SOURCES
    expected = [{**{i: group for i, group in enumerate((m[0], *m.groups()))}, 'index': m.start()}
                for m in re.finditer(pattern, source, re.MULTILINE)]
    assert manifest_matches(pattern, source) == expected


def test_expanding_shared_data_is_bounded_before_serialization() -> None:
    value: Any = 'synthetic'
    for _ in range(30):
        value = [value, value]
    with pytest.raises(ValueError, match='data_limit'):
        concrete(value)


def test_literal_patch_between_store_and_load_keeps_text_provenance(tmp_path: Path, private: PrivateGraders) -> None:
    patch = '*** Begin Patch\n*** Add File: own.py\n+synthetic\n*** End Patch\n'
    script = 'text(await tools.apply_patch(' + json.dumps(patch) + '));'
    source = (FIXTURES / 'derived-record-1.js').read_text()
    result = run_scripts(tmp_path, private, [(stored(), ''), (script, ''), (source, '')])
    assert result['status'] == 'clean', result


def test_both_retained_scripts_in_sequence(tmp_path: Path, private: PrivateGraders) -> None:
    scripts = [(stored(), '')] + [((FIXTURES / f'derived-record-{record}.js').read_text(), '') for record in (1, 2)]
    result = run_scripts(tmp_path, private, scripts)
    assert result['status'] == 'clean', result
    assert [resolution['line'] for resolution in result['resolutions']] == [4, 6]


@pytest.mark.parametrize('source', [
    'for(let i=0;i<100000;i++){ text(i); }',
    'const x = load("original_sources"); await tools.exec_command({cmd:x.constructor("opaque")()});',
    'const x = "\\u{1f600}"; await tools.exec_command({cmd:x.slice(1)});',
    'const x = true + true; await tools.exec_command({cmd:x});',
    'const x = load("original_sources"); x.matchAll(/(a+)+$/gm);',
    'const result = await tools.exec_command({cmd:"cat source.txt"}); '
    'await tools.exec_command({cmd:result ? "cat safe.py" : "cat other.py"});',
    'const a = 0 == "0"; await tools.exec_command({cmd:a ? "cat safe.py" : "cat other.py"});',
    'const a = 9007199254740992; await tools.exec_command({cmd:"cat " + a});',
    'const x = "safe"; x = "other"; store("original_sources",x);',
    'const x = "safe" store("original_sources",x);',
    'const x = store("key","value"); const target = x === null ? "safe" : "other"; '
    'await tools.exec_command({cmd:"cat " + target});',
    'const x = 010; await tools.exec_command({cmd:"cat " + x});',
    'const x = Object.fromEntries([[null,"other"],["null","safe"]]); '
    'await tools.exec_command({cmd:"cat " + x[null]});',
    'const x = Promise.all(["safe"]); const y = x.map(r => r); store("original_sources", y[0]);',
])
def test_bounded_reduction_rejects_semantic_uncertainty(source: str) -> None:
    assert reduce_script(source, {'original_sources': SOURCES}) is None
