"""Verbatim retained inputs and accounting from the four reported defects."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core, regrade, continue_day2
from eval.runner.audit import custom_commands, patch_paths, digest, PrivateGraders
from eval.runner.control_accounting import control_calls, historical_control_cost, prelaunch_collision_cost
from eval.runner.pricing import (retained_provenance, preserve_provenance, recover_default_tiers,
                                 merge_regraded_accounting)
from eval.runner.report import artifact, usage, validate, build_task
from tests.eval.test_access_audit import audit_native, native_session, private  # noqa: F401
from tests.eval.test_runner import setup  # noqa: F401
from tests.eval.test_continue_day2 import make_stopped, continuation_executor, VERSION
from tests.eval.test_recovery_pricing import grade_only
from tests.eval.test_v2_metrics_pricing import make_v1_source

FIXTURES = Path(__file__).parent / 'fixtures/retained_defects'


def load(directory: str, name: str) -> Any:
    return json.loads((FIXTURES / directory / name).read_text())


def relocated(task: dict[str, Any], name: str, path: Path) -> dict[str, Any]:
    """Relocate a reference without changing its retained hash or evidence bytes."""
    task = copy.deepcopy(task)
    next(a for a in task['artifacts'] if Path(a['path']).name == name)['path'] = str(path)
    return task


def test_verbatim_1419_character_patch_and_loop(tmp_path: Path, private: PrivateGraders,
        native_session: list[dict[str, Any]]) -> None:
    source = (FIXTURES / 'custom-input-1.js').read_text()
    assert len(source) == 1419
    assert digest(source.encode()) == 'eb29f96ef486ad5911355010037c727bd83dcd33893f55e432c6771fbc445126'
    commands, patches, unknown = custom_commands({'name': 'exec', 'input': source})
    assert not unknown
    assert [c['cmd'] for c in commands] == [f'python -m py_compile {name}.py' for name in
                                          ('project', 'engine', 'validation', 'policy')] + ['python verify.py']
    assert len(patches) == 1
    assert '+"""Compatibility entry point for the project package\'s public APIs."""' in patches[0]
    assert [Path(p).name for p in patch_paths(patches[0])] == ['project.py', 'engine.py', 'validation.py', 'policy.py']
    native_session[22]['payload']['input'] = source
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'clean', result
    assert result['errors'] == [] and result['matches'] == []


def test_verbatim_two_session_interrupts(tmp_path: Path, private: PrivateGraders,
        native_session: list[dict[str, Any]]) -> None:
    source = (FIXTURES / 'custom-input-2.js').read_text()
    assert digest(source.encode()) == '823de55bc7485172cdf6ecca22e789444689a3d827cbf9525e86c4b5ac157de9'
    assert custom_commands({'name': 'exec', 'input': source}) == ([], [], False)
    native_session[22]['payload']['input'] = source
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'clean', result
    assert result['errors'] == [] and result['matches'] == []


@pytest.mark.parametrize('source', [
    'tools.session_control({session_id:1,terminate:true})',
    'tools.wait({cell_id:"abc",yield_time_ms:100})',
    'tools.session_control({session_id:1,options:{terminate:true},values:[1,2]})',
    'tools.session_control()',
])
def test_static_non_path_controls(source: str) -> None:
    assert custom_commands({'name': 'exec', 'input': source}) == ([], [], False)
    if 'session_id:1,terminate:true' in source:
        assert custom_commands({'name': 'session_control', 'input': '{"session_id":1,"terminate":true}'}) == ([], [], False)


@pytest.mark.parametrize('source', [
    'tools.session_control({command:"cat secret.py"})',
    'tools.session_control({options:{path:"secret.py"}})',
    'tools.session_control({target:"/secret"})',
    'tools.session_control({session_id:session})',
    'tools.session_control({...args})',
    'tools.session_control({options:[{workdir:"."}]})',
    'tools.session_control({options:{terminate:true})',
    'tools.read_file({target:"secret"})',
    'tools.session_control({value:"secret.py"})',
    'tools.shell_command("cat secret")',
    'tools.shell({script:"ls"})',
])
def test_non_path_controls_do_not_waive_operands(source: str) -> None:
    assert custom_commands({'name': 'exec', 'input': source})[2]


@pytest.mark.parametrize('mutation', [
    'text(cmd);', 'cmd = "cat secret.py";', 'const alias = cmd;',
    'text(await tools.exec_command({cmd:cmd + " --extra"}));',
])
def test_inline_loop_binding_must_remain_static(mutation: str) -> None:
    source = (FIXTURES / 'custom-input-1.js').read_text()
    source = source[:-2] + mutation + '\n}\n'
    assert custom_commands({'name': 'exec', 'input': source})[2]


def test_verbatim_loop_still_audits_private_operands(tmp_path: Path, private: PrivateGraders,
        native_session: list[dict[str, Any]]) -> None:
    source = (FIXTURES / 'custom-input-1.js').read_text()
    source = source.replace('"python verify.py"', json.dumps('cat ' + str(private.files[0])))
    native_session[22]['payload']['input'] = source
    result = audit_native(tmp_path, private, native_session)
    assert result['status'] == 'access_detected', result
    assert not result['errors']


def test_verbatim_stale_provenance_recovers_exact_historical_hash(tmp_path: Path) -> None:
    directory = 'feature-plus-test-interval-union'
    task = relocated(load(directory, 'task.json'), 'pricing-provenance.json',
                     FIXTURES / directory / 'pricing-provenance.json')
    ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    assert digest(Path(ref['path']).read_bytes()) != ref['sha256']
    rows = retained_provenance(task, load(directory, 'pricing.json'))
    assert digest((json.dumps(rows, indent=2) + '\n').encode()) == ref['sha256']
    assert rows[0]['pricing_ref'] == task['calls'][0]['usage']['pricing_ref']
    out = copy.deepcopy(task)
    out['artifacts'] = []
    preserve_provenance(out, tmp_path, prior=task, pricing=load(directory, 'pricing.json'))
    assert retained_provenance(out)[0]['basis'] == rows[0]['basis']
    changed = copy.deepcopy(task)
    changed['calls'][0]['call_id'] += '-changed'
    with pytest.raises(ValueError, match='Pricing provenance hash mismatch'):
        retained_provenance(changed)


@pytest.mark.parametrize('requested,observed', [(None, None), ('priority', None), (None, 'flex')])
def test_verbatim_unpriced_day2_default_tier(tmp_path: Path, requested: str | None,
                                           observed: str | None) -> None:
    directory = 'two-session-balanced-brackets'
    prior = load(directory, 'task.json')
    entry = load(directory, 'entry.json')
    entry['segments'][1]['pricing_evidence']['records'][0]['observed_service_tier'] = observed
    recover_default_tiers(entry, {'model': 'gpt-6.1-sol', 'service_tier': requested})
    segment = entry['segments'][1]
    events = tmp_path / 'exec-2.jsonl'
    events.write_text('')
    candidate = copy.deepcopy(prior)
    candidate['calls'][1]['usage'] = usage(events, segment['latency_seconds'], 'gpt-6.1-sol',
        load(directory, 'pricing.json'), tier=segment['pricing_evidence']['tier'], native_counts=segment['native_usage'])
    merge_regraded_accounting(candidate, prior)
    assert candidate['calls'][0] == prior['calls'][0]  # Keep the retained Standard price.
    if requested is None and observed is None:
        assert candidate['calls'][1]['usage']['usd'] == pytest.approx(.0331696)
        assert candidate['costs']['total_usd'] == pytest.approx(.0652044)
    else:
        assert candidate['costs']['total_usd'] is None


def test_verbatim_priced_controls_and_empty_collision_history(tmp_path: Path) -> None:
    directory = 'multiple-requirements-stable-unique'
    prior = relocated(load(directory, 'task.json'), 'rerun-provenance.json',
                      FIXTURES / directory / 'rerun-provenance.json')
    entry = load(directory, 'entry.json')
    entry['runtime'] = str(FIXTURES / directory)
    calls, cost = control_calls(entry, prior['task_id'], load(directory, 'pricing.json'))
    assert [c['usage']['usd'] for c in calls] == pytest.approx([.00135132, .0033324])
    assert cost == pytest.approx(.00468372)  # The logs/delegations were already complete.
    assert historical_control_cost(entry['rerun_history'], prior) == 0
    # Exercise the real report builder, including its rerun-history completeness
    # gate. No historical runtime or native source is opened.
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    for name in entry['control_files']:
        if (FIXTURES / directory / name).is_file():
            (runtime / name).write_bytes((FIXTURES / directory / name).read_bytes())
    entry['runtime'] = str(runtime)
    for s in entry['segments']:
        s['native_logs'] = []
        (runtime / s['events']).write_text(json.dumps({'type': 'thread.started', 'thread_id': 'fixture'}) + '\n')
    out = tmp_path / 'report'
    out.mkdir()
    meta = copy.deepcopy(prior)
    meta['artifacts'] = [a for a in prior['artifacts'] if Path(a['path']).name == 'rerun-provenance.json']
    result = {'task_id': prior['task_id'], 'task_type': prior['task_type'], 'session_id': 'fixture',
              'segments': entry['segments'], 'outcome': 'pass', 'attempts': 1, 'invalid_reasons': [],
              'grading': None, 'grader_access_audit': {'status': 'clean', 'errors': [],
                  'root_fingerprint': '0' * 64, 'matches': []}}
    candidate = build_task(result, entry, out, {'harness': True, 'model': 'gpt-6.1-sol'},
                           load(directory, 'pricing.json'), meta)
    assert candidate['costs']['control_usd'] == pytest.approx(cost)
    merge_regraded_accounting(candidate, prior)
    assert candidate['calls'] == prior['calls']
    assert candidate['costs']['control_usd'] == pytest.approx(.00468372)
    assert candidate['costs']['total_usd'] == pytest.approx(.03405012)


@pytest.mark.parametrize('case', ['unpriced_call', 'launched_failure', 'segments', 'manifest_hash', 'extra_stream'])
def test_collision_recovery_keeps_genuinely_unknown_spending(case: str) -> None:
    source = load('multiple-requirements-stable-unique', 'rerun-provenance.json')
    task = {'calls': source['source_calls'], 'executor_segments': source['source_executor_segments'],
            'invalid_reasons': source['invalid_reasons'], 'artifacts': source['source_artifacts']}
    if case == 'unpriced_call':
        task['calls'] = [{'purpose': 'contract', 'usage': {'usd': None}}]
    elif case == 'launched_failure':
        task['invalid_reasons'] = ['control_cli_error']
    elif case == 'segments':
        task['executor_segments'] = [{}]
    elif case == 'manifest_hash':
        task['artifacts'][-1]['sha256'] = '0' * 64
    else:
        task['artifacts'].append({'path': 'contract.stderr', 'sha256': digest(b'')})
    assert prelaunch_collision_cost(task) is None


def test_v1_continuation_then_legacy_regrade_preserves_prices(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=False, include_other=True)
    make_v1_source(source)
    original = (source / 'report.json').read_bytes()
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    continued = tmp_path / 'continued'
    continued_executor = continuation_executor(executor, Path(entry['runtime']))
    def execute(argv: list[str], **kwargs: Any) -> Any:
        if argv[0] == 'codex' or '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            return continued_executor(argv, **kwargs)
        return grade_only(argv, **kwargs)
    report = json.loads(continue_day2.continue_day2(root, source, continued,
        execute=execute, version=VERSION).read_text())
    assert (source / 'report.json').read_bytes() == original
    validate(report, core.REPOSITORY)
    # Reproduce the old continuation's stale unselected provenance and unknown
    # day-2 tier, using the exact envelopes and basis strings from the fixtures.
    other = next(t for t in report['tasks'] if t['task_id'] == 'second-task')
    ref = next(a for a in other['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    fallback = [{'call_id': c['call_id'], 'observed_service_tier': None,
                 'basis': 'Retained original accounting; no per-call tier observation available.',
                 'pricing_ref': c['usage']['pricing_ref']} for c in other['calls']]
    ref['sha256'] = digest((json.dumps(fallback, indent=2) + '\n').encode())
    Path(ref['path']).write_text('[]\n')
    task = next(t for t in report['tasks'] if t['task_id'] == 'bug-chunk-tail')
    known = copy.deepcopy(task['calls'][0])
    state = json.loads((continued / 'checkpoint.json').read_text())
    e = state['tasks']['bug-chunk-tail']
    s = e['segments'][-1]
    s['pricing_evidence'] = copy.deepcopy(load('two-session-balanced-brackets', 'entry.json')['segments'][1]['pricing_evidence'])
    s['settings_verified'] = True
    e['result']['segments'] = copy.deepcopy(e['segments'])
    task['calls'][-1]['usage'].update(usd=None, pricing_ref=None)
    task['costs'].update(executor_usd=None, total_usd=None)
    rows = retained_provenance(task)
    rows[-1].update(pricing_ref=None, pricing_snapshot_sha256=None)
    price_path = next(Path(a['path']) for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    core.write_json(price_path, rows)
    next(a for a in task['artifacts'] if Path(a['path']).name == price_path.name).update(artifact(price_path))
    report['accounting']['total_cost_usd'] = None
    core.write_json(continued / 'report.json', report)
    core.write_json(continued / 'checkpoint.json', state)
    before = {p.relative_to(continued): p.read_bytes() for p in continued.rglob('*') if p.is_file()}
    for i in range(2):
        out = tmp_path / f'legacy-regrade-{i}'
        repaired = json.loads(regrade.regrade(root, continued, out, execute=grade_only).read_text())
        t = next(t for t in repaired['tasks'] if t['task_id'] == task['task_id'])
        assert t['calls'][0] == known
        assert all(t['costs'][k] is not None for k in t['costs'])
        assert repaired['accounting']['total_cost_usd'] is not None
        validate(repaired, core.REPOSITORY)
        if i == 0:
            assert before == {p.relative_to(continued): p.read_bytes() for p in continued.rglob('*') if p.is_file()}
        continued = out
