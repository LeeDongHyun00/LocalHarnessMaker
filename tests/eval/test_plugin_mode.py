"""Offline installed-hook runner evidence, accounting and clarification regressions."""

import copy
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import pytest

from eval.runner import core, harness, plugin_mode as plugin
from eval.runner.audit import PrivateGraders, digest
from eval.runner.process import ProcessResult, run_process
from eval.runner.report import build_task

REPOSITORY = core.REPOSITORY
VERSION = 'codex-cli 0.163.0-alpha.11.1'
COUNTS = {'input_tokens': 22000, 'cached_input_tokens': 2000, 'output_tokens': 4000}


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + '\n')


def stream(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(e) + '\n' for e in events))


def ref(directory: Path, name: str, data: bytes) -> dict[str, str]:
    target = directory / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'path': name, 'sha256': digest(data)}


def applied(model: str = 'gpt-6-luna', effort: str = 'low', tier: str = 'priority') -> dict[str, Any]:
    fixture = REPOSITORY / 'tests/eval/fixtures/native-session-0.163.jsonl'
    event = next(json.loads(line) for line in fixture.read_text().splitlines()
                 if json.loads(line).get('payload', {}).get('type') == 'thread_settings_applied')
    event['payload']['thread_settings'].update(model=model, reasoning_effort=effort, service_tier=tier)
    return event


def hooks(workspace: Path, sid: str, prompt: bytes, *, pending: bool = False,
          question: str = 'Should the widget boundary be inclusive?', disabled: bool = False) -> Path:
    directory = workspace / '.localharness/v3/sessions' / digest(sid.encode())
    directory.mkdir(parents=True, exist_ok=True)
    book = (REPOSITORY / 'controller/prices.yaml').read_bytes()
    book_value = json.loads(book)
    pricing_ref = f'controller/prices.yaml@{book_value["checked_on"]}#gpt-6-luna:sha256:{digest(book)}'
    pin = json.loads((REPOSITORY / 'schemas/examples/pin-check.json').read_text())
    pin.update(session_id=sid, status='disabled' if disabled else 'enabled', codex_version=VERSION,
               pricing_ref=pricing_ref,
               model_list=ref(directory, 'evidence/models.json', b'["gpt-6-luna"]'),
               pricing_snapshot=ref(directory, 'evidence/prices.json', book))
    pin['model_evidence']['evidence_sha256'] = pin['model_list']['sha256']
    if disabled:
        pin['checks']['model_listed'] = False
        pin['reason_codes'] = ['model_missing']
    write(directory / 'pin-check.json', pin)
    old_table = json.loads((directory / 'requirements.json').read_text()) if (directory / 'requirements.json').exists() else None
    table = {'schema_version': 3, 'session_id': sid, 'prompt': ref(directory, 'evidence/prompt.txt', prompt),
             'state': 'pending_questions' if pending else 'ready',
             'requirements': [{'id': 'R-1', 'number': 1, 'text': 'Synthetic behavior', 'kind': 'behavior',
                               'source_excerpt': prompt.decode(), 'check': {'type': 'unavailable', 'reason': 'No oracle'}}],
             'open_questions': [{'id': 'Q-1', 'text': question, 'requirement_ids': ['R-1'], 'answer': None}] if pending else [],
             'luna_call': {'path': 'luna-calls.jsonl', 'call_id': 'req-1'}}
    if old_table and not pending:
        table['open_questions'] = [{**q, 'answer': 'Use the inclusive boundary.\n'} for q in old_table['open_questions']]
    write(directory / 'requirements.json', table)
    records = []
    for phase, call_id in [('requirements', 'req-1')] + ([] if pending else [('claim_audit', 'audit-1')]):
        record = {'schema_version': 3, 'session_id': sid, 'call_id': call_id, 'phase': phase, 'backend': 'codex_cli',
                  'requested_model': 'gpt-6-luna', 'model': 'gpt-6-luna', 'reasoning_effort': 'low',
                  'status': 'success', 'error': None, **COUNTS, 'latency_seconds': .5, 'usd': .00402,
                  'pricing_ref': pricing_ref, 'cost_basis': 'api_equivalent_usd'}
        records.append(record)
        write(directory / f'evidence/{phase}-allocation.json', {'session_id': sid, 'call_id': call_id})
        generated = {'requirements': [{k: r[k] for k in ('text', 'kind', 'source_excerpt')} for r in table['requirements']],
                     'open_questions': [{'text': q['text'], 'requirement_numbers': [1]} for q in table['open_questions']]}
        stream(directory / f'evidence/{phase}-native.jsonl', [
            {'type': 'thread.started', 'thread_id': sid + '-' + phase + '-child', 'model': 'gpt-6-luna'},
            {'type': 'turn.started'},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(generated if phase == 'requirements' else {'claims': []})}},
            {'type': 'turn.completed', 'usage': COUNTS}])
        setting = applied()
        setting['payload']['thread_id'] = sid + '-' + phase + '-child'
        stream(directory / f'evidence/{phase}-rollout.jsonl', [setting,
            {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
                'total_token_usage': COUNTS, 'last_token_usage': COUNTS}}}])
        home = workspace.parent / 'codex-home'
        if home.exists():
            child = sid + '-' + phase + '-child'
            stream(home / 'sessions' / f'rollout-{child}.jsonl', [
                {'type': 'session_meta', 'payload': {'id': child, 'cli_version': VERSION.removeprefix('codex-cli ')}},
                {'type': 'turn_context', 'payload': {'model': 'gpt-6-luna', 'effort': 'low'}}, setting,
                {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
                    'total_token_usage': COUNTS, 'last_token_usage': COUNTS}}}])
    stream(directory / 'luna-calls.jsonl', records)
    if not pending:
        final_ref = ref(directory, 'evidence/final.txt', b'Synthetic completed work')
        audit = {'status': 'complete', 'audited_final_message': final_ref, 'claims': [], 'reason': None,
                 'luna_call': {'path': 'luna-calls.jsonl', 'call_id': 'audit-1'}}
        requirements_ref = {'path': 'requirements.json', 'sha256': digest((directory / 'requirements.json').read_bytes())}
        report = {'schema_version': 3, 'session_id': sid, 'requirements': requirements_ref,
                  'current_final_message': final_ref, 'check_round': 1,
                  'items': [{'requirement_id': 'R-1', 'status': 'unverifiable', 'reason': 'No oracle', 'evidence': []}],
                  'claim_audit': audit, 'retry': {'used': 0, 'failed_requirement_ids': [], 'reason': None},
                  'escalation_advice': None}
        ledger = {'schema_version': 3, 'session_id': sid, 'requirements': requirements_ref,
                  'decisions': [], 'open_items': [], 'validation': {'validated_at': '2026-10-25T00:00:00Z',
                    'status': 'valid', 'reason': 'Synthetic validation', 'identifiers': [], 'files': []}}
        write(directory / 'claim-audit.json', audit)
        write(directory / 'completion-report.json', report)
        write(directory / 'ledger.json', ledger)
        write(workspace / '.localharness/v3/latest-ledger.json', ledger)
    return directory


@pytest.fixture
def retained(tmp_path: Path) -> tuple[Path, Path, str]:
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    sid = 'synthetic-thread'
    directory = hooks(workspace, sid, b'Synthetic request')
    return workspace, directory, sid


def test_collection_hashes_every_artifact_and_references(retained: tuple[Path, Path, str], tmp_path: Path) -> None:
    workspace, directory, sid = retained
    pins = plugin.capture(workspace, tmp_path / 'retained')
    assert pins['sessions/' + digest(sid.encode()) + '/requirements.json'] == digest((directory / 'requirements.json').read_bytes())
    docs = plugin.validate_session(tmp_path / 'retained', sid, b'Synthetic request', REPOSITORY, version=VERSION)
    assert docs['completion-report.json']['session_id'] == sid
    (directory / 'evidence/prompt.txt').write_text('tampered')
    with pytest.raises(ValueError, match='changed'):
        plugin.capture(workspace, tmp_path / 'retained')
    with pytest.raises(ValueError, match='hash mismatch'):
        plugin.validate_session(workspace / '.localharness/v3', sid, b'Synthetic request', REPOSITORY)


def test_collection_rejects_aliases(retained: tuple[Path, Path, str], tmp_path: Path) -> None:
    workspace, directory, _ = retained
    (directory / 'evidence/alias').symlink_to(directory / 'requirements.json')
    with pytest.raises(ValueError, match='symlink'):
        plugin.capture(workspace, tmp_path / 'retained')


def test_accounting_reprices_actual_tier_and_reconciles_tokens(retained: tuple[Path, Path, str]) -> None:
    _, directory, sid = retained
    result = plugin.accounting(directory, sid, REPOSITORY, json.loads((REPOSITORY / 'eval/prices.yaml').read_text()))
    assert result['invalid_reasons'] == []
    assert result['cost_usd'] == pytest.approx(.01608)
    assert len(result['calls']) == 2
    assert result['provenance'][0]['recorded_usd'] == .00402
    assert result['calls'][0]['usage']['pricing_ref'] == 'openai-fast-short-2026-10-23-v1'


@pytest.mark.parametrize('defect,reason', [('usage', 'plugin_native_usage_mismatch'), ('budget', 'plugin_call_budget_mismatch'),
    ('model', 'plugin_native_model_mismatch'), ('long', 'plugin_cost_unknown'), ('missing', 'plugin_native_usage_missing')])
def test_accounting_invalidity_and_unknown_cost(retained: tuple[Path, Path, str], defect: str, reason: str) -> None:
    _, directory, sid = retained
    path = directory / 'luna-calls.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if defect == 'usage':
        rows[0]['input_tokens'] += 1
    elif defect == 'budget':
        rows.append(dict(rows[0], call_id='duplicate-phase'))
    elif defect == 'model':
        native = directory / 'evidence/requirements-native.jsonl'
        native.write_text(native.read_text().replace('gpt-6-luna', 'other-model'))
    elif defect == 'long':
        large = dict(COUNTS, input_tokens=300000)
        rows[0].update(large)
        native = directory / 'evidence/requirements-native.jsonl'
        native.write_text(native.read_text().replace(json.dumps(COUNTS), json.dumps(large)))
        rollout = directory / 'evidence/requirements-rollout.jsonl'
        rollout.write_text(rollout.read_text().replace(json.dumps(COUNTS), json.dumps(large)))
    else:
        stream(directory / 'evidence/requirements-native.jsonl', [{'type': 'thread.started', 'thread_id': 'child', 'model': 'gpt-6-luna'}])
        stream(directory / 'evidence/requirements-rollout.jsonl', [applied()])
    stream(path, rows)
    result = plugin.accounting(directory, sid, REPOSITORY, json.loads((REPOSITORY / 'eval/prices.yaml').read_text()))
    assert reason in result['invalid_reasons']
    if defect in {'usage', 'long', 'missing'}:
        assert result['cost_usd'] is None


@pytest.fixture
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path]:
    repository = tmp_path / 'repository'
    public = repository / 'eval/tasks-v3/v3-synthetic'
    (public / 'workspace').mkdir(parents=True)
    (public / 'workspace/answer.py').write_text('answer = 1\n')
    (public / 'prompt.md').write_text('Implement synthetic behavior.\n')
    write(public / 'meta.json', {'id': 'v3-synthetic', 'type': 'ambiguous_requirement', 'two_session': False, 'frozen': True})
    write(public / 'expected.json', {'expected_test_count': 1})
    shutil.copy(REPOSITORY / 'eval/prices.yaml', repository / 'eval/prices.yaml')
    for name in ('schemas', 'docs'):
        (repository / name).symlink_to(REPOSITORY / name, target_is_directory=True)
    auth = tmp_path / 'auth'
    auth.mkdir()
    (auth / 'auth.json').write_text('{}')
    monkeypatch.setenv('CODEX_HOME', str(auth))
    monkeypatch.setenv('HARNESS_NESTED', '1')
    private = tmp_path / 'trusted'
    (private / 'v3-synthetic').mkdir(parents=True)
    (private / 'v3-synthetic/test_synthetic.py').write_text('import unittest\nclass Checks(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
    write(private / 'responder-data/v3-synthetic/matcher.json', {'version': 'v1', 'phrase_pairs': [['widget', 'boundary']]})
    (private / 'responder-data/v3-synthetic/reply.md').write_text('Use the inclusive boundary.\n')
    config = json.loads((REPOSITORY / 'eval/configs/pilot.yaml').read_text())
    config.update(name='synthetic-plugin', task_root='eval/tasks-v3', tasks=['v3-synthetic'], codex_version=VERSION,
                  harness=True, control_backend='codex_cli', reinstruction_limit=1, mode='plugin',
                  plugin={'source_sha256': 'a'*64, 'contract_sha256': 'b'*64, 'pricing_catalog_sha256': 'c'*64,
                          'responders': {'v3-synthetic': {'matcher': 'responder-data/v3-synthetic/matcher.json',
                                                       'reply': 'responder-data/v3-synthetic/reply.md'}}})
    config_path = tmp_path / 'config.yaml'
    write(config_path, config)
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    monkeypatch.setattr(core, 'configured_digest', lambda *args: 'd'*64)
    monkeypatch.setattr(core, 'current_commit', lambda *args: 'e'*40)
    monkeypatch.setattr('eval.runner.report.current_commit', lambda *args: 'e'*40)
    # Installer behavior itself has a separate subprocess-boundary test below.
    def install(*args: Any) -> dict[str, Any]:
        workspace, home = args[3], args[4]
        (workspace / '.local-harness-maker').write_text('opt in')
        (home / 'hooks.json').write_text('{}')
        return {'source_sha256': 'a'*64, 'trust_flag': plugin.TRUST_FLAG}
    monkeypatch.setattr(plugin, 'install', install)
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError('Runner must never orchestrate controller/verifier')
    for name in ('contract', 'verify', 'handoff'):
        monkeypatch.setattr(harness, name, forbidden)
    return public, private, config_path, tmp_path / 'out'


class FakeCodex:
    def __init__(self, *, question: str | None = None, missing: bool = False, disabled: bool = False,
                 baseline: bool = False, leak: str | None = None, inject_ledger: bool = False) -> None:
        self.question, self.missing, self.disabled, self.baseline, self.leak = question, missing, disabled, baseline, leak
        self.inject_ledger = inject_ledger
        self.argv: list[list[str]] = []
        self.prompts: list[str] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            return run_process(argv, **kwargs)
        self.argv.append(argv)
        self.prompts.append(kwargs['stdin'])
        env, workspace = kwargs['env'], kwargs['cwd']
        if self.baseline:
            assert env['HARNESS_NESTED'] == '1' and plugin.TRUST_FLAG not in argv
        else:
            assert 'HARNESS_NESTED' not in env and env['HARNESS_PYTHON'] == sys.executable
            assert plugin.TRUST_FLAG in argv and 'features.hooks=true' in argv
            assert '--ignore-user-config' not in argv
            assert (workspace / '.local-harness-maker').is_file()
        sid = 'synthetic-session'
        if (workspace.parent / 'day-2').exists():
            sid = 'synthetic-day2'
        if 'resume' in argv:
            assert argv[-2] == sid
        stream(kwargs['stdout'], [{'type': 'thread.started', 'thread_id': sid},
                                 {'type': 'turn.completed', 'usage': COUNTS}])
        kwargs['stderr'].write_text('')
        Path(argv[argv.index('-o') + 1]).write_text('Synthetic completed work')
        native = Path(env['CODEX_HOME']) / 'sessions' / f'rollout-{sid}.jsonl'
        setting = applied('gpt-6.1-sol', 'medium', 'standard')
        setting['payload']['thread_id'] = sid
        events = [{'type': 'session_meta', 'payload': {'id': sid, 'cli_version': VERSION.removeprefix('codex-cli ')}},
                  {'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol', 'effort': 'medium'}}, setting]
        if sid == 'synthetic-day2' and self.inject_ledger:
            ledger = json.loads((workspace / '.localharness/v3/latest-ledger.json').read_text())
            events.append({'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [
                {'type': 'input_text', 'text': 'HARNESS_LEDGER (validated against this workspace):\n' + json.dumps(ledger)}]}})
        if native.exists():
            events = [json.loads(line) for line in native.read_text().splitlines()] + events[1:]
        stream(native, events)
        if not self.missing:
            prompt = (workspace.parent / f'original-{sid}-prompt.txt')
            if not prompt.exists():
                prompt.write_text(kwargs['stdin'])
            pending = self.question is not None and len(self.argv) == 1
            directory = hooks(workspace, sid, prompt.read_bytes(), pending=pending,
                              question=self.question or '', disabled=self.disabled)
            if self.leak:
                (directory / 'evidence/leak.txt').write_text(self.leak)
        return ProcessResult(0)


def test_plugin_run_collects_prices_and_does_not_orchestrate(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    executor = FakeCodex()
    report = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'pass', (task['invalid_reasons'], task['grader_access_audit'])
    assert task['costs']['control_usd'] == pytest.approx(.01608)
    assert len(task['calls']) == 3 and task['attempts'] == 1
    refs = task['artifacts']
    assert any(r['path'].endswith('/requirements.json') for r in refs)
    assert all(digest(Path(r['path']).read_bytes()) == r['sha256'] for r in refs if Path(r['path']).is_absolute())
    assert len(executor.argv) == 1


@pytest.mark.parametrize('options', [{'missing': True}, {'disabled': True}])
def test_missing_artifacts_or_disabled_pin_invalid(runtime: tuple[Path, Path, Path, Path], options: dict[str, bool]) -> None:
    _, private, config, out = runtime
    report = json.loads(core.run(config, out, private, execute=FakeCodex(**options), version=VERSION).read_text())
    task = report['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None
    assert 'plugin_required_artifacts_invalid' in task['invalid_reasons']
    if options.get('missing'):
        assert task['costs']['control_usd'] is None


@pytest.mark.parametrize('question,delivered', [('Should the widget boundary be inclusive?', True),
    ('Can you clarify the task?', False), ('I assume the widget boundary is inclusive.', False),
    ('ＳＨＯＵＬＤ the WIDGET   boundary be inclusive？', True)])
def test_clarification_only_eligible_hook_questions(runtime: tuple[Path, Path, Path, Path], question: str, delivered: bool) -> None:
    _, private, config, out = runtime
    executor = FakeCodex(question=question)
    report = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())
    assert len(executor.argv) == (2 if delivered else 1)
    task = report['tasks'][0]
    assert task['outcome'] == ('pass' if delivered else 'invalid'), task['invalid_reasons']
    if delivered:
        assert executor.prompts[1] == 'Use the inclusive boundary.\n'
        assert 'resume' in executor.argv[1] and plugin.TRUST_FLAG in executor.argv[1]
        assert task['attempts'] == 1 and len(task['calls']) == 4
        assert task['costs']['control_usd'] == pytest.approx(.01608)
        evidence = json.loads((out / 'v3-synthetic/plugin-index.json').read_text())['clarification']
        assert evidence['delivered_at'] and evidence['questions'][0]['matched']
        assert evidence['reply_sha256'] == digest(executor.prompts[1].encode())


def test_baseline_gets_no_note_even_with_lookalike(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    value = json.loads(config.read_text())
    for key in ('mode', 'plugin'):
        value.pop(key)
    value.update(harness=False, control_backend='none', reinstruction_limit=0)
    write(config, value)
    executor = FakeCodex(question='Should the widget boundary be inclusive?', baseline=True)
    task = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())['tasks'][0]
    assert len(executor.argv) == 1 and len(task['calls']) == 1
    assert task['costs']['control_usd'] == 0


def test_artifact_private_access_is_audited_before_grading(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    task = json.loads(core.run(config, out, private, execute=FakeCodex(leak=str(private)), version=VERSION).read_text())['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None
    assert task['grader_access_audit']['status'] == 'access_detected'
    assert task['costs']['control_usd'] == pytest.approx(.01608)


@pytest.mark.parametrize('receipt', [True, False])
def test_day2_is_a_fresh_session_with_only_public_prompt_and_observed_ledger(
        runtime: tuple[Path, Path, Path, Path], receipt: bool) -> None:
    public, private, config, out = runtime
    metadata = json.loads((public / 'meta.json').read_text())
    metadata.update(type='two_session', two_session=True)
    write(public / 'meta.json', metadata)
    (public / 'day2.md').write_text('Implement only the synthetic second-day request.\n')
    executor = FakeCodex(inject_ledger=receipt)
    task = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())['tasks'][0]
    assert len(executor.argv) == 2 and all('resume' not in argv for argv in executor.argv)
    assert executor.prompts[1] == (public / 'day2.md').read_text()
    assert task['outcome'] == ('pass' if receipt else 'invalid'), task['invalid_reasons']
    assert task['costs']['control_usd'] == pytest.approx(.03216)
    assert task['attempts'] == 2
    index = json.loads((out / 'v3-synthetic/plugin-index.json').read_text())
    assert len({o['session_id'] for o in index['observations']}) == 2
    assert all(o['ledger_sha256'] and o['requirements_sha256'] for o in index['observations'])
    if receipt:
        assert task['handoff']['day2_pass'] is True
        assert index['day2_observation']['plugin_ledger_injection']['source_ledger_sha256']
    else:
        assert 'plugin_ledger_injection_unobserved' in task['invalid_reasons']


def test_lookalike_table_without_native_generation_never_delivers(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    class Lookalike(FakeCodex):
        def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
            result = super().__call__(argv, **kwargs)
            if argv[0] == 'codex':
                native = kwargs['cwd'] / '.localharness/v3/sessions' / digest(b'synthetic-session') / 'evidence/requirements-native.jsonl'
                stream(native, [{'type': 'thread.started', 'thread_id': 'forged', 'model': 'gpt-6-luna'},
                                {'type': 'turn.started'}, {'type': 'turn.completed', 'usage': COUNTS}])
            return result
    executor = Lookalike(question='Should the widget boundary be inclusive?')
    task = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())['tasks'][0]
    assert task['outcome'] == 'invalid' and len(executor.argv) == 1
    assert 'plugin_required_artifacts_invalid' in task['invalid_reasons']


def test_question_pause_with_file_changes_never_delivers(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    class Changed(FakeCodex):
        def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
            result = super().__call__(argv, **kwargs)
            if argv[0] == 'codex':
                (kwargs['cwd'] / 'answer.py').write_text('changed during question pause')
            return result
    executor = Changed(question='Should the widget boundary be inclusive?')
    task = json.loads(core.run(config, out, private, execute=executor, version=VERSION).read_text())['tasks'][0]
    assert task['outcome'] == 'invalid' and len(executor.argv) == 1


def test_installation_uses_supported_installer_and_preserves_auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = tmp_path / 'source'
    (repository / 'controller').mkdir(parents=True)
    (repository / 'controller/synthetic.py').write_text('runtime source')
    (repository / 'docs').mkdir()
    (repository / 'docs/interfaces-v3.md').write_text('contract')
    (repository / 'eval').mkdir()
    (repository / 'eval/prices.yaml').write_text('prices')
    sources = {'controller/synthetic.py': digest(b'runtime source')}
    monkeypatch.setattr(plugin, 'source_inventory', lambda *args: sources)
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    home, workspace = runtime / 'codex-home', runtime / 'workspace'
    home.mkdir()
    workspace.mkdir()
    auth = tmp_path / 'auth.json'
    auth.write_text('{}')
    (home / 'auth.json').symlink_to(auth)
    private_root = tmp_path / 'trusted'
    private_root.mkdir()
    private = PrivateGraders(private_root, ())
    config = {'plugin': {'source_sha256': plugin.inventory_hash(sources), 'contract_sha256': digest(b'contract'),
                         'pricing_catalog_sha256': digest(b'prices')}}
    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        assert argv == [sys.executable, str(repository / 'plugin/install.py'), '--codex-home', str(home), '--project', str(workspace)]
        assert kwargs['env']['HARNESS_PYTHON'] == sys.executable and 'HARNESS_NESTED' not in kwargs['env']
        assert (home / 'auth.json').is_symlink()
        target = home / 'local-harness-maker/controller'
        target.mkdir(parents=True)
        shutil.copy(repository / 'controller/synthetic.py', target / 'synthetic.py')
        (home / 'hooks.json').write_text('{}')
        (home / 'config.toml').write_text('[features]\nhooks=true\n')
        (workspace / '.local-harness-maker').write_text('opt in')
        kwargs['stdout'].write_text('installed')
        kwargs['stderr'].write_text('')
        return ProcessResult(0)
    installed = plugin.install(repository, config, runtime, workspace, home, private, execute)
    assert installed['source_sha256'] == config['plugin']['source_sha256']
    assert installed['marker_sha256'] == digest(b'opt in')
    plugin.verify_installation(home, installed)
    (home / 'hooks.json').write_text('tampered')
    with pytest.raises(ValueError, match='changed'):
        plugin.verify_installation(home, installed)


def test_failed_call_retains_actual_cost(retained: tuple[Path, Path, str]) -> None:
    _, directory, sid = retained
    path = directory / 'luna-calls.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[-1].update(status='timeout', error='deadline')
    stream(path, rows)
    result = plugin.accounting(directory, sid, REPOSITORY, json.loads((REPOSITORY / 'eval/prices.yaml').read_text()))
    assert result['calls'][-1]['status'] == 'timeout'
    assert result['cost_usd'] == pytest.approx(.01608)
    assert 'plugin_accounting_identity_or_protocol' in result['invalid_reasons']


def test_context_limit_applies_per_request_not_cumulative_session(retained: tuple[Path, Path, str]) -> None:
    _, directory, sid = retained
    path = directory / 'luna-calls.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    cumulative = dict(COUNTS, input_tokens=320000)
    rows[0].update(cumulative, usd=.03382)
    stream(path, rows)
    native = directory / 'evidence/requirements-native.jsonl'
    native.write_text(native.read_text().replace(json.dumps(COUNTS), json.dumps(cumulative)))
    first = {k: v//2 for k, v in cumulative.items()}
    stream(directory / 'evidence/requirements-rollout.jsonl', [applied(),
        {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': first, 'last_token_usage': first}}},
        {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {
            'total_token_usage': cumulative, 'last_token_usage': first}}}])
    result = plugin.accounting(directory, sid, REPOSITORY, json.loads((REPOSITORY / 'eval/prices.yaml').read_text()))
    assert result['invalid_reasons'] == []
    assert result['cost_usd'] == pytest.approx(.07568)
    assert result['provenance'][0]['pricing_evidence']['max_input_tokens'] == 160000


def test_grader_source_cannot_be_selected_as_author_note(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    value = json.loads(config.read_text())
    value['plugin']['responders']['v3-synthetic']['reply'] = 'v3-synthetic/test_synthetic.py'
    write(config, value)
    executor = FakeCodex(question='Should the widget boundary be inclusive?')
    with pytest.raises(ValueError, match='private grader marker'):
        core.run(config, out, private, execute=executor, version=VERSION)
    assert executor.argv == []


@pytest.mark.parametrize('defect', ['prompt', 'session', 'audit_claims', 'staleness', 'model_evidence'])
def test_cross_artifact_bindings_fail_closed(retained: tuple[Path, Path, str], defect: str) -> None:
    workspace, directory, sid = retained
    name = 'requirements.json' if defect in {'prompt', 'session'} else 'completion-report.json'
    if defect == 'model_evidence':
        name = 'pin-check.json'
    value = json.loads((directory / name).read_text())
    if defect == 'prompt':
        value['prompt'] = ref(directory, 'evidence/other-prompt.txt', b'Other prompt')
    elif defect == 'session':
        value['session_id'] = 'stale-session'
    elif defect == 'audit_claims':
        value['claim_audit']['claims'] = [{'requirement_id': None, 'claim_excerpt': 'invented',
                                          'cited_evidence': [], 'assessment': 'unverifiable'}]
    elif defect == 'staleness':
        value['current_final_message'] = ref(directory, 'evidence/changed-final.txt', b'Changed final')
    else:
        value['model_evidence']['evidence_sha256'] = 'b'*64
    write(directory / name, value)
    with pytest.raises(Exception):
        plugin.validate_session(workspace / '.localharness/v3', sid, b'Synthetic request', REPOSITORY, version=VERSION)


def test_truncated_control_stream_is_inconclusive_not_normalized(runtime: tuple[Path, Path, Path, Path]) -> None:
    _, private, config, out = runtime
    class Truncated(FakeCodex):
        def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
            result = super().__call__(argv, **kwargs)
            if argv[0] == 'codex':
                path = kwargs['cwd'] / '.localharness/v3/sessions' / digest(b'synthetic-session') / 'evidence/requirements-native.jsonl'
                path.write_bytes(path.read_bytes().rstrip(b'\n'))
            return result
    task = json.loads(core.run(config, out, private, execute=Truncated(), version=VERSION).read_text())['tasks'][0]
    assert task['outcome'] == 'invalid' and task['grading'] is None
    assert task['grader_access_audit']['status'] == 'inconclusive'
    assert 'incomplete_access_audit' in task['invalid_reasons']
