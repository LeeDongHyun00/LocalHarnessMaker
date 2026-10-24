"""Verbatim runtime scripts, paired outputs and synthetic STOP-E4 boundaries."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, command_operands, digest
from eval.runner.javascript_derived import reduce_script, regex_matches
from tests.eval.test_access_audit import private, audit_loop_record, LOOP_RECORDS
from tests.eval.test_derived_inputs import run_scripts

FIXTURES = Path(__file__).parent / 'fixtures/runtime-records'
B_RECORDS = [
    'v2-rate-budgets-bug-fix', 'v2-layered-settings-multiple-requirements',
    'v2-workflow-state-feature-plus-test', 'v2-routing-bug-fix',
    'v2-workflow-state-constrained-refactoring',
]

FIXTURE_HASHES = {
    'v2-layered-settings-multiple-requirements': 'e0a2436c20b1a44db4edfc522b2dfd39f1f40acab6ede3d1aa685179a3b4e417',
    'v2-rate-budgets-bug-fix': '16173bd84ad872e89ac970b3584f039f5405dba895458ad1203b2758e81047a4',
    'v2-rate-budgets-two-session': 'ce86cbbb23e15921bd297501e83d237014bb9b01bd056e7992db8de4553cf8a7',
    'v2-routing-bug-fix': '7057c12eb9991de9949c533aa597ea17d4ad07d3d6cccf51ff423b038ecd3929',
    'v2-workflow-state-constrained-refactoring': 'ec16ec434fa935a8534a231ec1cd105ea0d295311967ea7257d3162807b95ba9',
    'v2-workflow-state-feature-plus-test': '6a56ea6776d90c7727fbf9e5a04b4f0470164b5401549befd6bf2a8f426f6cac',
}



def records(name: str) -> list[dict[str, Any]]:
    assert digest((FIXTURES / (name + '.jsonl')).read_bytes()) == FIXTURE_HASHES[name]
    return [json.loads(row) for row in (FIXTURES / (name + '.jsonl')).read_text().splitlines()]


@pytest.mark.parametrize('name', B_RECORDS)
def test_complete_verbatim_sequences_resolve(tmp_path: Path, private: PrivateGraders, name: str) -> None:
    rows = [{'type': 'session_meta', 'payload': {'id': 'synthetic-runtime'}}] + records(name)
    log = tmp_path / 'session.jsonl'
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    result = audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository')
    assert result['errors'] == [], result['errors']
    assert result['status'] == 'clean', result
    assert result['matches'] == []
    targets = [i for i, row in enumerate(rows, 1) if row.get('payload', {}).get('type') == 'custom_tool_call'
               and ('load(' in row['payload']['input'] or '.map(async' in row['payload']['input'])]
    assert targets
    # Routing has entirely literal operands; it need not receive a derived resolution.
    if name != 'v2-routing-bug-fix':
        assert set(targets) <= {entry['line'] for entry in result['resolutions']}


def test_exact_shell_records_resolve(tmp_path: Path, private: PrivateGraders) -> None:
    rows = records('v2-rate-budgets-two-session')[:2]
    log = tmp_path / 'shell.jsonl'
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows + [{'type': 'turn.completed'}]))
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    result = audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository')
    assert result['status'] == 'clean', result
    operands, unresolved = command_operands(rows[0]['item']['command'], workspace, workspace=workspace)
    assert not unresolved
    expected = [Path(value) for value in re.findall(r'/[^\s;]*AGENTS\.md', rows[0]['item']['command'])]
    assert len(expected) == 8
    assert all(operands.count((path, False)) == 2 for path in expected)
    assert len(operands) >= 16


@pytest.mark.parametrize('form', LOOP_RECORDS)
@pytest.mark.parametrize('case', ['own', 'private', 'sibling', 'variable', 'dynamic_body', 'inside_heredoc'])
def test_loop_test_builtin_and_suffix_heredoc_boundaries(
        tmp_path: Path, private: PrivateGraders, form: str, case: str) -> None:
    workspace = tmp_path / 'runtime/workspace'
    workspace.mkdir(parents=True)
    target = str(workspace.parent / 'AGENTS.md')
    if case == 'private':
        target = str(private.root / 'probe')
    if case == 'sibling':
        target = str(tmp_path / 'sibling-runtime/AGENTS.md')
    if case == 'variable':
        target = '$UNKNOWN'
    body = f'for p in /AGENTS.md {target}; do if test -f "$p"; then cat "$p"; fi; done\n'
    body += "python - <<'PY'\nfrom pathlib import Path\nPath('README.md').read_text()\nPY"
    if case == 'dynamic_body':
        body = body.replace('cat "$p"', 'eval "cat $p"')
    if case == 'inside_heredoc':
        body = "for p in own.py; do python - <<'PY'\nprint('synthetic')\nPY\ndone"
    result = audit_loop_record(tmp_path, private, body, workspace, form)
    if case == 'sibling':
        log = tmp_path / ('exec.jsonl' if form == 'json' else 'native-loop.jsonl')
        if not log.exists():
            log = next(tmp_path.glob('*.jsonl'))
        result = audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository',
                            grading_roots=(tmp_path / 'sibling-runtime',))
        assert any(match['marker'] == 'protected_path' for match in result['matches'])
    expected = 'clean' if case == 'own' else 'access_detected' if case in {'private', 'sibling'} else 'inconclusive'
    assert result['status'] == expected, result


@pytest.mark.parametrize('wrapper', ['{index:i,...results[i]}', '{index:i,result:results[i]}'])
@pytest.mark.parametrize('loop', [True, False])
def test_paired_indexed_displays_establish_correct_result(
        tmp_path: Path, private: PrivateGraders, wrapper: str, loop: bool) -> None:
    source = 'const results = await Promise.allSettled(['
    source += 'tools.exec_command({cmd:"cat one.txt"}),tools.exec_command({cmd:"cat two.txt"})]);'
    source += ('for(let i=0;i<results.length;i++) text(' + wrapper + ');' if loop else
               'const i=1; text(' + wrapper + ');')
    source += 'if(results[1].status==="fulfilled") store("source",results[1].value.output);'
    indices = [0, 1] if loop else [1]
    outputs = []
    for i in indices:
        result = {'status': 'fulfilled', 'value': {'output': 'one.py' if i == 0 else 'two.py'}}
        block = {'index': i, **result} if '...results' in wrapper else {'index': i, 'result': result}
        outputs.append({'type': 'input_text', 'text': json.dumps(block)})
    computed = 'await tools.exec_command({cmd:"cat " + load("source")});'
    result = run_scripts(tmp_path, private, [(source, outputs), (computed, '')])
    assert result['status'] == 'clean', result
    reduced = reduce_script(source, {})
    assert reduced is not None
    assert reduced.completed(outputs)['source'] == 'two.py'


@pytest.mark.parametrize('mutation', ['store("source", external);', 'save("source", external);'])
def test_unsupported_storage_writer_invalidates_key(tmp_path: Path, private: PrivateGraders, mutation: str) -> None:
    scripts = [('store("source","own.py");', ''), (mutation, ''),
               ('await tools.exec_command({cmd:"cat " + load("source")});', '')]
    result = run_scripts(tmp_path, private, scripts)
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:6' in result['errors']


@pytest.mark.parametrize('source', [
    'text(await tools.apply_patch(String.raw`*** Begin Patch\n*** Add File: own.py\n+x\n*** End Patch`));',
    'const ignored = process.env.VALUE; text(await tools.exec_command({cmd:"cat own.py"}));',
    'const ignored = "store save"; text(await tools.exec_command({cmd:"cat own.py"}));',
])
def test_nonwriting_scripts_keep_stores(tmp_path: Path, private: PrivateGraders, source: str) -> None:
    scripts = [('store("source","own.py");', ''), (source, ''),
               ('await tools.exec_command({cmd:"cat " + load("source")});', '')]
    result = run_scripts(tmp_path, private, scripts)
    assert result['status'] == 'clean', result


@pytest.mark.parametrize('pattern', [r'(a+)+$', r'(?<=x)y', r'(a)\1', r'(?P<x>a)', r'a|b', r'\p{L}', r'a++', r'[^]', r'a+a+a+b', r'a+b'])
def test_unsupported_regex_in_argument_flow_is_inconclusive(
        tmp_path: Path, private: PrivateGraders, pattern: str) -> None:
    source = ('const s="aa"; const matches=[...s.matchAll(/' + pattern + '/gm)];'
              'await tools.exec_command({cmd:"echo " + JSON.stringify(matches.map(m=>m[0]))});')
    result = run_scripts(tmp_path, private, [(source, '')])
    assert result['status'] == 'inconclusive', result


@pytest.mark.parametrize('style', ['template', 'concatenation', 'destructure'])
def test_reduced_private_operand_always_wins(tmp_path: Path, private: PrivateGraders, style: str) -> None:
    path = str(private.root / 'probe.py')
    if style == 'destructure':
        source = 'const pairs=[["probe",{cmd:' + json.dumps('cat ' + path) + '}]];'
        source += 'await Promise.allSettled(pairs.map(async ([label,args])=>tools.exec_command(args)));'
    else:
        # Neither fragment alone is a private marker; the reduced value is.
        middle = len(path) // 2
        source = 'const s=' + json.dumps('X' + path[:middle] + '\n' + path[middle:]) + ';'
        source += r'const pairs=[...s.matchAll(/^X([^\n]+)\n([^\n]+)/g)];'
        source += 'const target=pairs.map(m=>m[1]+m[2])[0];'
        source += ('await tools.exec_command({cmd:`cat ${target}`});' if style == 'template' else
                   'await tools.exec_command({cmd:"cat " + target});')
    result = run_scripts(tmp_path, private, [(source, '')])
    assert result['status'] == 'access_detected', result
    assert result['resolutions']
    assert any(entry['marker'] == 'protected_path' for entry in result['matches'])


@pytest.mark.parametrize(('pattern', 'flags', 'value', 'expected'), [
    (r'^([a-z]+)=(\d+)$', 'gm', 'one=12\ntwo=3\n', [('one', '12'), ('two', '3')]),
    (r'^(a.+b)', 'gs', 'a\nx\nb', [('a\nx\nb',)]),
    (r'^([a-z]+)$', 'g', 'abc\n', []),
    (r'^\[([^\]]+)\]', 'g', '[hello]', [('hello',)]),
])
def test_safe_regex_translation(pattern: str, flags: str, value: str, expected: list[tuple[str, ...]]) -> None:
    matches = regex_matches(pattern, flags, value)
    assert [tuple(match[i] for i in range(1, len(match) - 1)) for match in matches] == expected


@pytest.mark.parametrize('variant', ['confirmed_prefix', 'before_write', 'missing_output', 'yielded'])
def test_failed_script_requires_postwrite_execution_witness(
        tmp_path: Path, private: PrivateGraders, variant: str) -> None:
    store = 'store("hashes",{"own.py":"synthetic"});'
    call = 'text(await tools.exec_command({cmd:"cat own.py"}));'
    patch = 'text(await tools.apply_patch("*** Begin Patch\n*** End Patch"));'.replace('\n', '\\n')
    source = (call + store if variant == 'before_write' else store + call) + patch
    output = [{'type': 'input_text', 'text': json.dumps({'output': 'synthetic'})}]
    output.append({'type': 'input_text', 'text': 'Script running with cell ID pending' if variant == 'yielded'
                   else 'Script error: synthetic later failure'})
    if variant == 'missing_output':
        output = output[1:]
    computed = 'await tools.exec_command({cmd:"cat " + Object.keys(load("hashes"))[0]});'
    result = run_scripts(tmp_path, private, [(source, output), (computed, '')])
    assert result['status'] == ('clean' if variant == 'confirmed_prefix' else 'inconclusive'), result


@pytest.mark.parametrize('mutation', [
    'const arg={cmd:"cat own.py"}; if(external) arg.cmd="cat changed.py"; await tools.exec_command(arg);',
    'const result=await tools.exec_command({cmd:"cat own.py"}); '
    'if(result.status==="fulfilled") text(result); else store("source","changed.py");',
    'const result=await tools.exec_command({cmd:"cat own.py"}); '
    'if(result.status==="fulfilled") store("source","changed.py"); '
    'await tools.exec_command({cmd:load("source")});',
    'const arg={cmd:"cat own.py"}; unknown(arg); await tools.exec_command(arg);',
    'const arg={cmd:"cat own.py"}; arg.update("changed"); await tools.exec_command(arg);',
    'new Function("opaque")();',
])
def test_operand_mutations_and_unknown_effects_remain_unsupported(mutation: str) -> None:
    assert reduce_script(mutation, {'source': 'own.py'}) is None


@pytest.mark.parametrize('variant', ['overridden', 'wrong_index', 'missing', 'duplicate'])
def test_ambiguous_or_transformed_displays_do_not_export_store(variant: str) -> None:
    source = ('const r=await tools.exec_command({cmd:"cat own.py"});'
              'text({index:1,...r' + ',output:"masked"' * (variant == 'overridden') + '});'
              'store("source",r.output);')
    reduction = reduce_script(source, {})
    assert reduction is not None
    output = {'index': 0 if variant == 'wrong_index' else 1, 'output': 'masked' if variant == 'overridden' else 'own.py'}
    blocks = [{'type': 'input_text', 'text': json.dumps(output)}]
    if variant == 'missing':
        blocks = []
    if variant == 'duplicate':
        blocks *= 2
    assert 'source' not in reduction.completed(blocks)


def test_embedded_storage_write_invalidates_previous_key(tmp_path: Path, private: PrivateGraders) -> None:
    scripts = [('store("source","own.py");', ''),
               ('text(`${store("source", external)}`);', ''),
               ('await tools.exec_command({cmd:"cat " + load("source")});', '')]
    result = run_scripts(tmp_path, private, scripts)
    assert result['status'] == 'inconclusive', result
    assert 'unresolved_custom_input:synthetic.jsonl:6' in result['errors']



def test_multiple_unknown_result_spreads_cannot_export_wrong_call(tmp_path: Path, private: PrivateGraders) -> None:
    source = ('const a=await tools.exec_command({cmd:"cat one.py"});'
              'const b=await tools.exec_command({cmd:"cat two.py"});'
              'text({...a,...b}); store("source",a.output);')
    result = run_scripts(tmp_path, private, [(source, json.dumps({'output': 'two.py'})),
                          ('await tools.exec_command({cmd:"cat "+load("source")});', '')])
    assert result['status'] == 'inconclusive', result


@pytest.mark.parametrize(('name', 'call_index', 'key', 'nested'), [
    ('v2-rate-budgets-bug-fix', 2, 'original_sources', False),
    ('v2-workflow-state-feature-plus-test', 2, 'baseline_inspection', True),
])
def test_real_bootstrap_exports_exact_displayed_source(name: str, call_index: int, key: str, nested: bool) -> None:
    rows = records(name)
    source, output = rows[call_index]['payload']['input'], rows[call_index + 1]['payload']['output']
    reduction = reduce_script(source, {})
    assert reduction is not None
    shown = json.loads(output[-1]['text'])
    result = shown['result'] if nested else shown
    assert reduction.completed(output)[key] == result['value']['output']


def test_real_literal_hash_write_is_confirmed_before_failed_patch() -> None:
    rows = records('v2-workflow-state-constrained-refactoring')
    reduction = reduce_script(rows[4]['payload']['input'], {})
    assert reduction is not None
    saved = reduction.completed(rows[5]['payload']['output'], failed=True)
    assert saved['protected_sha256'] == {
        'README.md': '3940c95abb93b87227532b41e980cb9d3510a9269b9fd3e218180e94fb6cf43a',
        'verify.py': '4dfdf99e793b0da8eef7a849ad80e237cf393e35870c42fdeac69d167a032b8a',
        'test_public.py': '1161d0da1d029c8f2b6793b52ec6d1373e82d84428e3a5895aed10c1b998d758',
        'project/compat.py': 'bef387eee4b7a3e2b9a9df698ebd2e74157766c85e746adad16971085a87030b',
    }



def test_nonwriter_output_detection_keeps_state_and_detected_status(tmp_path: Path, private: PrivateGraders) -> None:
    scripts = [('store("source","own.py");', ''),
               ('text(await tools.exec_command({cmd:"cat own.py"}));',
                json.dumps({'output': str(private.root / 'probe')})),
               ('await tools.exec_command({cmd:"cat "+load("source")});', '')]
    result = run_scripts(tmp_path, private, scripts)
    assert result['status'] == 'access_detected', result
    assert any(item['line'] == 6 for item in result['resolutions'])
