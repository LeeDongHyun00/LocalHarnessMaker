"""Synthetic-path versions of retained listings, outages and code-mode chains."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.audit import PrivateGraders, audit_logs, digest
from eval.runner.protected_listing import listing_spec
from eval.runner.javascript_derived import concrete, reduce_script, storage_identifiers, Unsupported
from tests.eval.test_access_audit import private
from tests.eval.test_derived_inputs import run_scripts


FIXTURES = Path(__file__).parent / 'fixtures/audit-records-3'
WORKSPACE = Path('/synthetic/audit/lhm-eval-current/workspace')
LISTINGS = [
    'v2-access-policy-bug-fix', 'v2-search-facets-feature-plus-test',
    'v2-filesystem-manifests-bug-fix', 'v2-layered-settings-constrained-refactoring',
    'v2-ledger-multiple-requirements', 'v2-schema-migration-constrained-refactoring',
]
CHAINS = ['v2-rate-budgets-feature-plus-test', 'v2-inventory-bug-fix']
FIXTURE_HASHES = {
    'transport-errors': '78dfbab91ed6f9fcdada88706b64aaad4b053b3c00603ce3af8bb2fbd2704897',
    'v2-access-policy-bug-fix': '4c0842f0f0934d1fbb1b19cc720c4cf0f8e3c98bdfc11fd996e65238c2b7b6d9',
    'v2-filesystem-manifests-bug-fix': '8d94e557f89f4b4d71d59ad5eb99e50d01749d21bfcf71136dd5f0308ed36dee',
    'v2-inventory-bug-fix': 'a2b84f70eb730ff37674c51763680d0d27448ce82ebb4d68321c7e17296ca4f9',
    'v2-layered-settings-constrained-refactoring': '6363327d985f8927fc850093e2409074429b7c14f30fc4b15eac5064d3168d39',
    'v2-ledger-multiple-requirements': '53f14861b8ee6cbfafe572abc5507ebadb6f1eb05a40715597daecde279f5958',
    'v2-rate-budgets-feature-plus-test': '2f4e3723419f8bb8d7081b6e8f72eabbfdf52c49bdbdf7b0a08b3c99587f2b78',
    'v2-schema-migration-constrained-refactoring': 'fdb37d986f217266c8015002f1ff8b746452124f96feb438732bc48f0f7d3d97',
    'v2-search-facets-feature-plus-test': '48564d8a76973076118a64f85e45e260f195dd2be1dcb70f345c5a4140d9b4e5',
}


def records(name: str) -> list[dict[str, Any]]:
    assert digest((FIXTURES / (name + '.jsonl')).read_bytes()) == FIXTURE_HASHES[name]
    return [json.loads(line) for line in (FIXTURES / (name + '.jsonl')).read_text().splitlines()]


def audit(tmp_path: Path, private: PrivateGraders, rows: list[dict[str, Any]], *,
          workspace: Path = WORKSPACE) -> dict[str, Any]:
    log = tmp_path / 'records.jsonl'
    rows = [{'type': 'session_meta', 'payload': {'id': 'synthetic-records-3'}}, *rows,
            {'type': 'turn.completed'}]
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    return audit_logs([log], private, workspace=workspace, repository=tmp_path / 'repository',
                      grading_roots=(Path('/synthetic/audit/lhm-retained-grading'),
                                     Path('/synthetic/audit/lhm-eval-sibling')))


@pytest.mark.parametrize('name', LISTINGS)
def test_six_captured_exec_listings_with_synthetic_paths(tmp_path: Path, private: PrivateGraders, name: str) -> None:
    result = audit(tmp_path, private, records(name)[:2])
    assert result['status'] == 'clean', result
    assert [r['reason'] for r in result['resolutions']] == ['protected_listing_without_exposure'] * 2
    assert all(r['completion_line'] == 3 for r in result['resolutions'])


@pytest.mark.parametrize('name', LISTINGS)
def test_native_command_evidence_is_paired_and_complete(tmp_path: Path, private: PrivateGraders, name: str) -> None:
    rows = records(name)[2:]
    call_id = rows[0]['payload']['call_id']
    rows.append({'type': 'response_item', 'payload': {
        'type': 'custom_tool_call_output', 'call_id': call_id, 'output': ''}})
    result = audit(tmp_path, private, rows)
    if name == LISTINGS[0]:
        # The actual native record contains a persistence truncation marker.
        assert result['status'] == 'access_detected', result
        assert not result['resolutions']
    else:
        assert result['status'] == 'clean', result
        assert len(result['resolutions']) == 2


def listing(command: str = 'rg --files -g AGENTS.md /synthetic/audit 2>/dev/null',
            output: str = '/synthetic/audit/public/AGENTS.md\n') -> list[dict[str, Any]]:
    item = {'type': 'command_execution', 'id': 'listing', 'command': command,
            'aggregated_output': '', 'status': 'in_progress', 'exit_code': None}
    completed = dict(item, aggregated_output=output, status='completed', exit_code=0)
    return [{'type': 'item.started', 'item': item}, {'type': 'item.completed', 'item': completed}]


@pytest.mark.parametrize('case', [
    'wildcard', 'python', 'hidden', 'reference', 'grader_alias', 'grading_output', 'sibling_output',
    'own_output', 'unknown_runtime_output', 'private_output', 'truncated', 'truncated_flag',
    'unterminated', 'missing_output', 'missing_completion', 'wrong_id', 'wrong_command',
    'duplicate_completion', 'second_operand', 'second_read', 'unsafe_redirection', 'unknown_option',
    'mixed_positive', 'incomplete_status', 'output_error', 'null_exit', 'wrong_cwd', 'session_boundary',
])
def test_listing_exception_fails_closed(tmp_path: Path, private: PrivateGraders, case: str) -> None:
    rows = listing()
    start, end = rows[0]['item'], rows[1]['item']
    substitutions = {
        'wildcard': '*.md', 'python': 'test_any.py', 'hidden': 'hidden-tests.md',
        'reference': 'reference.json', 'grader_alias': private.files[0].name,
    }
    if case in substitutions:
        for item in [start, end]:
            item['command'] = item['command'].replace('AGENTS.md', substitutions[case])
    outputs = {
        'grading_output': '/synthetic/audit/lhm-retained-grading/copy/AGENTS.md\n',
        'sibling_output': '/synthetic/audit/lhm-eval-sibling/AGENTS.md\n',
        'own_output': str(WORKSPACE / 'AGENTS.md') + '\n',
        'unknown_runtime_output': '/synthetic/audit/lhm-eval-unregistered/AGENTS.md\n',
        'private_output': str(private.root / 'AGENTS.md') + '\n',
        'truncated': '/synthetic/audit/public/AGENTS.md\n... command output truncated for persistence ...\n',
        'unterminated': '/synthetic/audit/public/AGENTS.md',
        'output_error': 'permission denied\n',
    }
    if case in outputs:
        end['aggregated_output'] = outputs[case]
    if case == 'truncated_flag':
        end['output_truncated'] = True
    if case == 'missing_output':
        end.pop('aggregated_output')
    if case == 'missing_completion':
        rows.pop()
    if case == 'wrong_id':
        end['id'] = 'unrelated'
    if case == 'wrong_command':
        end['command'] += ' /other'
    if case == 'duplicate_completion':
        rows.append(copy.deepcopy(rows[-1]))
    suffixes = {
        'second_operand': ' /synthetic/audit/lhm-eval-sibling',
        'second_read': ' && cat /synthetic/audit/lhm-eval-sibling/secret.txt',
        'unsafe_redirection': ' > /synthetic/audit/lhm-eval-sibling/dump',
        'unknown_option': ' --pre=reader', 'mixed_positive': " -g '*'",
    }
    if case in suffixes:
        for item in [start, end]:
            item['command'] += suffixes[case]
    if case == 'incomplete_status':
        end['status'] = 'in_progress'
    if case == 'null_exit':
        end['exit_code'] = None
    if case == 'wrong_cwd':
        end['cwd'] = '/synthetic/other'
    if case == 'session_boundary':
        rows.insert(1, {'type': 'session_meta', 'payload': {'id': 'other'}})
    result = audit(tmp_path, private, rows)
    assert result['status'] == 'access_detected', result
    assert any(match['marker'] == 'protected_path' for match in result['matches'])


@pytest.mark.parametrize('command', [
    'find /synthetic/audit -name AGENTS.md',
    "find /synthetic/audit -type f -name AGENTS.md ! -path '*/.git/*' -print",
    'find /synthetic/audit \\( -name AGENTS.md -o -name README.md \\)',
    "rg --files --glob=AGENTS.md -g '!*.py' /synthetic/audit",
])
def test_safe_find_and_rg_names(tmp_path: Path, private: PrivateGraders, command: str) -> None:
    result = audit(tmp_path, private, listing(command))
    assert result['status'] == 'clean', result


@pytest.mark.parametrize('command', [
    "find /synthetic/audit -name '*.md'", 'find /synthetic/audit -type f -o -name AGENTS.md',
    'find /synthetic/audit -print -name AGENTS.md',
    'find /synthetic/audit -name AGENTS.md -exec cat {} \\;',
    'find /synthetic/audit ! -name AGENTS.md', 'find /synthetic/audit -name AGENTS.md -o -type f',
    'find /synthetic/audit -name AGENTS.md -o -print',
    'find /synthetic/audit -path AGENTS.md',
])
def test_unsafe_find_syntax_has_no_exception(command: str) -> None:
    assert listing_spec(command) is None


def test_transport_items_are_visible_metadata(tmp_path: Path, private: PrivateGraders) -> None:
    result = audit(tmp_path, private, records('transport-errors'))
    assert result['status'] == 'clean', result
    assert len(result['diagnostics']) == 2
    assert all(d['type'] == 'transport_error' and d['message'].startswith('Falling back')
               and len(d['evidence_sha256']) == 64 for d in result['diagnostics'])


@pytest.mark.parametrize('extra', [{'command': 'cat private'}, {'path': 'private'}, {'message': None}])
def test_error_items_cannot_hide_effects(tmp_path: Path, private: PrivateGraders, extra: dict[str, Any]) -> None:
    row = records('transport-errors')[0]
    row['item'].update(extra)
    result = audit(tmp_path, private, [row])
    assert result['status'] == 'inconclusive'
    assert not result['diagnostics']


@pytest.mark.parametrize('name', CHAINS)
def test_complete_code_mode_chains_now_resolve(tmp_path: Path, private: PrivateGraders, name: str) -> None:
    rows = records(name)
    result = audit(tmp_path, private, rows)
    assert result['status'] == 'clean', result
    assert any(r['line'] == 12 and r['reason'] == 'derived_from_audited_outputs' for r in result['resolutions'])
    saved: dict[str, Any] = {}
    for call, output in zip(rows[::2], rows[1::2]):
        source = call['payload']['input']
        reduction = reduce_script(source, saved)
        if reduction is not None:
            saved = reduction.completed(output['payload']['output'])
        elif storage_identifiers(source):
            saved = {}
    assert reduction is not None
    if name == 'v2-rate-budgets-feature-plus-test':
        assert set(saved['protected_baseline']) == {'README.md', 'verify.py', 'test_public.py', 'project/compat.py'}
        expected = json.dumps(saved['protected_baseline'], indent=4)
        assert 'expected = ' + expected + '\n' in reduction.commands[0]['cmd']
    else:
        # The variable-length changed-file display tail cannot establish a
        # stored report. It does not feed a tool operand in this call chain.
        assert 'inventory_verification' not in saved
        assert reduction.commands[0]['cmd'].startswith("python - <<'PY'\n")


@pytest.mark.parametrize('case', ['complete', 'missing_projection', 'ambiguous_projection', 'private_projection'])
def test_projected_fields_require_unique_paired_display(tmp_path: Path, private: PrivateGraders, case: str) -> None:
    source = ('const r = await tools.exec_command({cmd:"cat manifest.json"});'
              'const obj = JSON.parse(r.output); text({path:obj.path}); store("candidate",obj.path);')
    output = [{'type': 'input_text', 'text': json.dumps({'path': 'solution.py'})}]
    if case == 'missing_projection':
        output = [{'type': 'input_text', 'text': '{"other":"solution.py"}'}]
    if case == 'ambiguous_projection':
        source += 'text({path:obj.path});'
        output *= 2
    if case == 'private_projection':
        output = [{'type': 'input_text', 'text': json.dumps({'path': str(private.root / 'secret')})}]
    result = run_scripts(tmp_path, private, [(source, output),
        ('await tools.exec_command({cmd:"cat " + load("candidate")});', '')])
    assert result['status'] == ('clean' if case == 'complete' else
                                'access_detected' if case == 'private_projection' else 'inconclusive'), result


def test_repeated_custom_commands_cannot_share_one_completion(tmp_path: Path, private: PrivateGraders) -> None:
    rows = records(LISTINGS[1])[2:]
    command = rows[1]['payload']['item']['command'][2]
    rows[0]['payload']['input'] += 'await tools.exec_command({cmd:' + json.dumps(command) + '});'
    rows.append({'type': 'response_item', 'payload': {'type': 'custom_tool_call_output',
                 'call_id': rows[0]['payload']['call_id'], 'output': ''}})
    result = audit(tmp_path, private, rows)
    assert result['status'] == 'access_detected', result


@pytest.mark.parametrize('name', CHAINS)
@pytest.mark.parametrize('case', ['missing_store', 'missing_paired_output', 'private_source', 'unsupported_method'])
def test_code_chain_unknown_sources_stay_refused(tmp_path: Path, private: PrivateGraders, name: str, case: str) -> None:
    rows = records(name)
    if case == 'missing_store':
        rows = rows[-2:]
    if case == 'missing_paired_output':
        rows.pop(3)
    if case == 'private_source':
        rows[3]['payload']['output'].append({'type': 'input_text', 'text': str(private.root / 'secret')})
    if case == 'unsupported_method':
        rows[-2]['payload']['input'] += ' const x = load("unknown").replaceAll("a","b");'
    result = audit(tmp_path, private, rows)
    if name == 'v2-inventory-bug-fix' and case == 'missing_store':
        # The absent original is comparison-only; no tool operand depends on it.
        assert result['status'] == 'clean', result
        return
    assert result['status'] != 'clean', result
    if case == 'private_source':
        assert result['status'] == 'access_detected'
    elif case != 'missing_paired_output':
        assert any('unresolved_' in error for error in result['errors'])


@pytest.mark.parametrize('source', [
    'for(let i=0;i<2;i+=unknown) {text(i);}',
    'let i=0; i+=2; await tools.exec_command({cmd:"pwd"});',
    'store("x", JSON.stringify(load("data"), null, 11));',
    'store("x", JSON.stringify(load("data"), null, 4));',
    'store("x", load("text").split(/(a+)+/));',
    'store("x", load("text").match(/a/g));',
])
def test_reducer_extensions_retain_bounds(source: str) -> None:
    assert reduce_script(source, {'data': {'timing': 0.1}, 'text': 'aaa'}) is None


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf'), 2.0 ** 54])
def test_observed_float_metadata_is_finite_and_bounded(value: float) -> None:
    with pytest.raises(Unsupported):
        concrete(value)
