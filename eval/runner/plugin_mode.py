"""Observe installed v3 hooks; never orchestrate their controller or verifier."""

from datetime import datetime, timezone
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Callable
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from eval.metrics import total
from eval.runner.audit import digest, executor_environment, PrivateGraders
from eval.runner.pricing import price_usage
from eval.runner.telemetry import records, session_id, native_request_usage, native_token_totals

TRUST_FLAG = '--dangerously-bypass-hook-trust'
MODEL = 'gpt-6-luna'
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens')
SCHEMAS = {'pin-check.json': 'pin-check.schema.json', 'requirements.json': 'requirements.schema.json',
           'completion-report.json': 'completion-report.schema.json', 'ledger.json': 'ledger.schema.json'}


def enabled(config: dict[str, Any]) -> bool:
    """Keep historical harness configurations on their original path."""
    return config.get('mode') == 'plugin' or (config.get('harness') is True and
            config.get('control_backend') == 'codex_cli' and isinstance(config.get('plugin'), dict))


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def confined(root: Path, name: str) -> Path:
    """Reject traversal, noncanonical spelling, hard links and symlink aliases."""
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name:
        raise ValueError('noncanonical artifact path')
    target = root / name
    for path in (target, *target.parents):
        if path.is_symlink():
            raise ValueError('symlink artifact')
        if path == root:
            break
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('artifact escape')
    if target.is_file() and target.stat().st_nlink != 1:
        raise ValueError('hard-linked artifact')
    return target


def source_inventory(repository: Path) -> dict[str, str]:
    """Pin precisely the runtime source trees copied by the supported installer."""
    files: dict[str, str] = {}
    for directory in ('controller', 'verifier', 'schemas', 'plugin'):
        for path in sorted((repository / directory).rglob('*')):
            relative = path.relative_to(repository)
            if '__pycache__' in relative.parts or path.suffix in {'.pyc', '.pyo'}:
                continue
            # Plugin evidence is calibration history, not executable installation input.
            if directory == 'plugin' and relative.parts[1] in {'evidence', '.pytest_cache'}:
                continue
            if path.is_symlink():
                raise ValueError('runtime source alias')
            if path.is_file():
                files[relative.as_posix()] = digest(path.read_bytes())
    return files


def inventory_hash(files: dict[str, str]) -> str:
    return digest(json.dumps(files, sort_keys=True).encode())


def validate_config(config: dict[str, Any]) -> None:
    if config.get('mode') not in (None, 'plugin'):
        raise ValueError('Unsupported runner mode')
    if not enabled(config):
        return
    plugin = config.get('plugin', {})
    if (not config['harness'] or config['control_backend'] != 'codex_cli' or
            config['retry_limit'] != 0 or config['reinstruction_limit'] != 1):
        raise ValueError('Plugin mode requires codex_cli, one hook repair and no runner retries')
    allowed = {'source_sha256', 'contract_sha256', 'pricing_catalog_sha256', 'responders'}
    if not isinstance(plugin, dict) or set(plugin) - allowed:
        raise ValueError('Unsupported plugin configuration')
    for key in allowed - {'responders'}:
        if not re.fullmatch('[0-9a-f]{64}', plugin.get(key, '')):
            raise ValueError(f'Plugin {key} must be pinned')
    if not isinstance(plugin.get('responders', {}), dict):
        raise ValueError('Plugin responders must map task IDs to frozen responder files')


def environment(private: PrivateGraders, home: Path) -> dict[str, str]:
    env = executor_environment(private, home)
    env.pop('HARNESS_NESTED', None)
    env['HARNESS_PYTHON'] = sys.executable
    return env


def install(repository: Path, config: dict[str, Any], runtime: Path, workspace: Path,
            home: Path, private: PrivateGraders, execute: Callable[..., Any]) -> dict[str, Any]:
    files = source_inventory(repository)
    pins = config['plugin']
    contract = digest((repository / 'docs/interfaces-v3.md').read_bytes())
    pricing = digest((repository / 'eval/prices.yaml').read_bytes())
    if (inventory_hash(files) != pins['source_sha256'] or contract != pins['contract_sha256'] or
            pricing != pins['pricing_catalog_sha256']):
        raise ValueError('Plugin runtime/contract/pricing pin mismatch')
    argv = [sys.executable, str(repository / 'plugin/install.py'), '--codex-home', str(home),
            '--project', str(workspace)]
    result = execute(argv, cwd=repository, env=environment(private, home), stdin='',
                     stdout=runtime / 'plugin-install.stdout', stderr=runtime / 'plugin-install.stderr', timeout=30)
    if result.returncode or result.timed_out:
        raise ValueError('Plugin installation failed')
    installed = {path.relative_to(home).as_posix(): digest(path.read_bytes())
                 for path in sorted(home.rglob('*')) if path.is_file() and not path.is_symlink()
                 and 'sessions' not in path.relative_to(home).parts}
    for name in ('hooks.json', 'config.toml'):
        if name not in installed:
            raise ValueError('Plugin installation missing configuration')
    if not confined(workspace, '.local-harness-maker').is_file():
        raise ValueError('Plugin opt-in marker missing')
    for name, expected in files.items():
        target = home / 'local-harness-maker' / name
        # Installer intentionally copies a subset of plugin/ (no tests/probes/docs).
        if (target.exists() or name.startswith(('controller/', 'verifier/', 'schemas/'))) and (
                not target.is_file() or target.is_symlink() or digest(target.read_bytes()) != expected):
            raise ValueError('Installed runtime differs from pinned source')
    return {'installed_at': stamp(), 'argv': argv, 'source': files, 'installed': installed,
            'source_sha256': inventory_hash(files), 'contract_sha256': contract,
            'pricing_catalog_sha256': pricing, 'trust_flag': TRUST_FLAG,
            'environment': {'HARNESS_NESTED': 'unset', 'HARNESS_PYTHON': sys.executable},
            'marker_sha256': digest((workspace / '.local-harness-maker').read_bytes())}


def validator(repository: Path, name: str, fragment: str | None = None) -> Draft202012Validator:
    resources = {p.name: json.loads(p.read_text()) for p in (repository / 'schemas').glob('*.schema.json')}
    registry = Registry().with_resources((k, Resource.from_contents(v)) for k, v in resources.items())
    schema = resources[name] if fragment is None else {'$ref': name + fragment}
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def references(value: Any, directory: Path) -> None:
    """Check all artifact references, including nested check and claim evidence."""
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            target = confined(directory, value['path'])
            if not target.is_file() or digest(target.read_bytes()) != value['sha256']:
                raise ValueError('artifact reference hash mismatch')
        for child in value.values():
            references(child, directory)
    elif isinstance(value, list):
        for child in value:
            references(child, directory)


def capture(workspace: Path, destination: Path, *, pins: dict[str, str] | None = None) -> dict[str, str]:
    """Take an immutable post-exit copy of the entire hook root, without aliases."""
    root = confined(workspace, '.localharness/v3')
    if not root.is_dir():
        raise ValueError('missing plugin artifact root')
    pins = pins if pins is not None else {}
    for source in sorted(root.rglob('*')):
        name = source.relative_to(root).as_posix()
        source = confined(root, name)
        if source.is_dir():
            continue
        if not source.is_file():
            raise ValueError('unsupported plugin artifact')
        data = source.read_bytes()
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise ValueError('collected artifact changed')
        target.write_bytes(data)
        if source.read_bytes() != data:
            raise ValueError('artifact changed during collection')
        pins[name] = digest(data)
    return pins


def validate_session(root: Path, sid: str, prompt: bytes, repository: Path, *,
                     paused: bool = False, version: str | None = None) -> dict[str, Any]:
    directory = confined(root, 'sessions/' + digest(sid.encode('utf-8')))
    docs: dict[str, Any] = {}
    required = {'pin-check.json', 'requirements.json'} if paused else set(SCHEMAS)
    for name in required:
        value = json.loads(confined(directory, name).read_text())
        validator(repository, SCHEMAS[name]).validate(value)
        if value['session_id'] != sid:
            raise ValueError('plugin session identity mismatch')
        if name == 'requirements.json':
            references(value['prompt'], directory)
        elif name == 'ledger.json':
            references(value['requirements'], directory)
        else:
            references(value, directory)
        docs[name] = value
    pin, table = docs['pin-check.json'], docs['requirements.json']
    if pin['status'] != 'enabled' or not all(pin['checks'].values()):
        raise ValueError('plugin pin disabled')
    if pin['requested_model'] != MODEL or pin['model_evidence']['observed_model'] != MODEL:
        raise ValueError('plugin model pin mismatch')
    evidence = pin['model_evidence']
    if evidence['source'] == 'listing':
        if evidence['evidence_sha256'] != pin['model_list']['sha256']:
            raise ValueError('plugin model listing evidence mismatch')
    else:
        observation = json.loads(confined(directory, pin['model_list']['path']).read_text())
        if observation.get('model') != MODEL or any(observation.get(k) != evidence[k] for k in
                ('service_tier', 'observed_at', 'thread_id', 'evidence_sha256')):
            raise ValueError('plugin model probe observation mismatch')
    if version is not None and pin['codex_version'] != version:
        raise ValueError('plugin Codex version mismatch')
    if any(row['source_excerpt'] not in prompt.decode('utf-8') for row in table['requirements']):
        raise ValueError('plugin source excerpt not in request')
    if table['prompt']['sha256'] != digest(prompt):
        raise ValueError('plugin prompt mismatch')
    rows = table['requirements']
    if [r['number'] for r in rows] != list(range(1, len(rows) + 1)) or (
            [r['id'] for r in rows] != [f'R-{n}' for n in range(1, len(rows) + 1)]):
        raise ValueError('plugin requirement identifiers mismatch')
    if any(not set(q['requirement_ids']).issubset({r['id'] for r in rows}) for q in table['open_questions']):
        raise ValueError('plugin question identifiers mismatch')
    expected_hash = digest((directory / 'requirements.json').read_bytes())
    if paused and any((directory / name).exists() for name in ('completion-report.json', 'claim-audit.json', 'ledger.json')):
        raise ValueError('plugin question pause ran completion phases')
    if not paused:
        report, ledger = docs['completion-report.json'], docs['ledger.json']
        if table['state'] != 'ready':
            raise ValueError('plugin requirements not ready')
        for value in (report, ledger):
            if value['requirements'] != {'path': 'requirements.json', 'sha256': expected_hash}:
                raise ValueError('plugin requirements binding mismatch')
        if [r['requirement_id'] for r in report['items']] != [r['id'] for r in rows]:
            raise ValueError('plugin completion coverage mismatch')
        sidecar = json.loads(confined(directory, 'claim-audit.json').read_text())
        validator(repository, 'completion-report.schema.json', '#/properties/claim_audit').validate(sidecar)
        references(sidecar, directory)
        # Staleness is represented in the merged report; preserve the original audit.
        if report['current_final_message'] is None:
            raise ValueError('plugin final message missing')
        if sidecar['claims'] != report['claim_audit']['claims']:
            raise ValueError('plugin audit claims changed during merge')
        stale = sidecar['audited_final_message'] != report['current_final_message']
        if report['claim_audit']['status'] != ('stale' if stale else 'complete'):
            raise ValueError('plugin audit staleness mismatch')
        if sidecar['luna_call'] != report['claim_audit']['luna_call']:
            raise ValueError('plugin audit call mismatch')
        if sidecar['status'] != 'complete' or report['claim_audit']['status'] == 'unavailable':
            raise ValueError('plugin audit unavailable')
        if report['claim_audit']['audited_final_message'] != sidecar['audited_final_message']:
            raise ValueError('plugin audited message mismatch')
        if not ledger['validation'] or ledger['validation']['status'] != 'valid':
            raise ValueError('plugin ledger invalid')
        latest = json.loads(confined(root, 'latest-ledger.json').read_text())
        if latest != ledger:
            raise ValueError('plugin latest ledger mismatch')
        docs['claim-audit.json'] = sidecar
    return docs


def accounting(directory: Path, sid: str, repository: Path, pricing: dict[str, Any],
               *, paused: bool = False) -> dict[str, Any]:
    """Price actual records once, including deviations; unknown remains unknown."""
    calls: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    reasons: list[str] = []
    phases: list[str] = []
    seen: set[str] = set()
    try:
        raw = (directory / 'luna-calls.jsonl').read_bytes()
        if not raw.endswith(b'\n'):
            reasons.append('plugin_accounting_truncated')
        lines = raw.decode('utf-8').splitlines()
    except (OSError, UnicodeError):
        lines = []
        reasons.append('plugin_accounting_missing')
    for number, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
            validator(repository, 'luna-call.schema.json').validate(record)
        except Exception:
            reasons.append('plugin_accounting_malformed')
            continue
        phase = record['phase']
        phases.append(phase)
        if (record['session_id'] != sid or record['call_id'] in seen or record['backend'] != 'codex_cli' or
                record['model'] != MODEL or record['status'] != 'success'):
            reasons.append('plugin_accounting_identity_or_protocol')
        seen.add(record['call_id'])
        if not all(record[k] is None or math.isfinite(record[k]) for k in ('usd', 'latency_seconds')):
            reasons.append('plugin_accounting_nonfinite')
            continue
        served_model = record['model'] or 'unknown'
        counts = {k: record[k] for k in TOKEN_KEYS}
        details: dict[str, Any] = {}
        tier: str | None = None
        requests = None
        native_path = directory / f'evidence/{phase}-native.jsonl'
        rollout_path = directory / f'evidence/{phase}-rollout.jsonl'
        try:
            events = records(native_path)
            native = records(rollout_path) if rollout_path.exists() else []
            models = [e.get('model') for e in events if e.get('model')]
            models += [e.get('payload', {}).get('model') for e in native
                       if e.get('payload', {}).get('model')]
            for event in [*events, *native]:
                payload = event.get('payload', {})
                if payload.get('type') == 'thread_settings_applied':
                    settings = payload.get('thread_settings', {})
                    if settings.get('model'):
                        models.append(settings['model'])
                    tier = settings.get('service_tier')
            if not models or set(models) != {record['model']}:
                reasons.append('plugin_native_model_mismatch')
                served_model = models[0] if models and len(set(models)) == 1 else 'unknown'
            turns = [e['usage'] for e in events if e.get('type') == 'turn.completed']
            if turns and all(all(type(t.get(k)) is int for k in TOKEN_KEYS) for t in turns):
                observed = {k: sum(t[k] for t in turns) for k in TOKEN_KEYS}
                if counts != observed:
                    reasons.append('plugin_native_usage_mismatch')
                    counts = dict.fromkeys(TOKEN_KEYS)
            elif counts not in [v[1] for v in native_token_totals([rollout_path]).values()]:
                reasons.append('plugin_native_usage_missing')
                counts = dict.fromkeys(TOKEN_KEYS)
            requests = native_request_usage([rollout_path], counts) if rollout_path.exists() else None
            # A CLI call can include several provider requests. Sum only reconciled deltas.
            if requests is None and len(turns) == 1 and len([e for e in events if e.get('type') == 'turn.started']) == 1:
                requests = turns
            allocation = json.loads((directory / f'evidence/{phase}-allocation.json').read_text())
            if allocation != {'call_id': record['call_id'], 'session_id': sid}:
                reasons.append('plugin_call_allocation_mismatch')
        except (OSError, ValueError, KeyError, TypeError):
            reasons.append('plugin_native_accounting_missing')
            counts = dict.fromkeys(TOKEN_KEYS)
        usd, reference = price_usage(counts, pricing, served_model, tier,
                                     requests=requests, evidence=details)
        if requests is None:
            # Per-request bounds are required even when the cumulative total is small.
            usd = None
            reasons.append('plugin_request_usage_missing')
        try:
            pin = json.loads((directory / 'pin-check.json').read_text())
            book_ref = pin['pricing_snapshot']
            book = json.loads(confined(directory, book_ref['path']).read_text())
            raw_book = confined(directory, book_ref['path']).read_bytes()
            expected_ref = f'controller/prices.yaml@{book["checked_on"]}#{MODEL}:sha256:{digest(raw_book)}'
            if record['pricing_ref'] != pin['pricing_ref'] or record['pricing_ref'] != expected_ref:
                reasons.append('plugin_pricing_reference_mismatch')
            recorded_counts = [record[k] for k in TOKEN_KEYS]
            if all(v is not None for v in recorded_counts):
                i, c, o = recorded_counts
                rates = book['models'][MODEL]
                calculated = ((i-c)*float(rates['input_per_million']) + c*float(rates['cached_input_per_million']) +
                              o*float(rates['output_per_million'])) / 1_000_000
                if record['usd'] is None or not math.isclose(record['usd'], calculated, rel_tol=1e-9, abs_tol=1e-12):
                    reasons.append('plugin_recorded_cost_mismatch')
        except (OSError, ValueError, KeyError, TypeError):
            reasons.append('plugin_pricing_reference_missing')
        if usd is None:
            reasons.append('plugin_cost_unknown')
        call_id = f'{digest(sid.encode())}-{number}-{record["call_id"]}'
        # The frozen report uses generic historical purpose labels. Exact v3 phases live here.
        calls.append({'call_id': call_id, 'purpose': 'contract' if phase == 'requirements' else 'judge',
                      'backend': record['backend'], 'model': served_model,
                      'status': 'completed' if record['status'] == 'success' else
                                'timeout' if record['status'] == 'timeout' else 'failed',
                      'usage': {**counts, 'usd': usd, 'latency_seconds': record['latency_seconds'],
                                'cost_basis': 'api_equivalent_usd', 'pricing_ref': reference}})
        provenance.append({'call_id': call_id, 'phase': phase, 'session_id': sid,
                           'accounting_record': number, 'accounting_pricing_ref': record['pricing_ref'],
                           'recorded_usd': record['usd'], 'observed_service_tier': tier,
                           'pricing_ref': reference, 'pricing_evidence': details,
                           'basis': 'Repriced hook accounting reconciled with retained native control evidence'})
    expected = ['requirements'] if paused else ['requirements', 'claim_audit']
    if sorted(phases) != sorted(expected):
        reasons.append('plugin_call_budget_mismatch')
    return {'calls': calls, 'provenance': provenance, 'invalid_reasons': list(dict.fromkeys(reasons)),
            'cost_usd': total([c['usage']['usd'] for c in calls]) if calls and not any(
                r in reasons for r in ('plugin_accounting_missing', 'plugin_accounting_malformed',
                                      'plugin_accounting_truncated', 'plugin_accounting_nonfinite')) and all(p in phases for p in expected) else None}


def normalize(text: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def clarification(docs: dict[str, Any], directory: Path, task: str, sid: str,
                  private: PrivateGraders, config: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Read only explicitly selected frozen responder data, never grader source."""
    table = docs['requirements.json']
    observation: dict[str, Any] = {'session_id': sid, 'table_sha256': digest((directory / 'requirements.json').read_bytes()),
                                  'observed_at': stamp(), 'questions': [], 'delivered_at': None, 'reply_sha256': None}
    if table['state'] != 'pending_questions':
        return observation, None
    spec = config['plugin'].get('responders', {}).get(task)
    if not spec:
        observation['reason'] = 'frozen_responder_not_configured'
        return observation, None
    matcher_path = confined(private.root, spec['matcher'])
    reply_path = confined(private.root, spec['reply'])
    if (matcher_path in private.files or reply_path in private.files or
            matcher_path.suffix != '.json' or reply_path.suffix not in {'.md', '.txt', '.json'} or
            any(part in {'.references', '.mutants'} for path in (matcher_path, reply_path)
                for part in path.relative_to(private.root).parts)):
        raise ValueError('responder data must be separate from graders and references')
    matcher = json.loads(matcher_path.read_text())
    pairs = matcher['phrase_pairs']
    if (not isinstance(matcher['version'], (str, int)) or not isinstance(pairs, list) or
            not 1 <= len(pairs) <= 128 or any(not isinstance(p, list) or len(p) != 2 or
            any(not isinstance(v, str) or not normalize(v) for v in p) for p in pairs)):
        raise ValueError('invalid frozen question matcher')
    reply = reply_path.read_bytes().decode('utf-8')
    if not reply.strip() or any(marker in reply for marker in private.markers()):
        raise ValueError('invalid author reply')
    observation.update(matcher_sha256=digest(matcher_path.read_bytes()), matcher_version=matcher['version'],
                       reply_sha256=digest(reply.encode('utf-8')))
    for index, question in enumerate(table['open_questions']):
        text = normalize(question['text'])
        interrogative = '?' in text or bool(re.match(r'^(should|what|which|how|does|do|is|are|can|when|whether)\b', text))
        matched = question['answer'] is None and interrogative and any(
            normalize(subject) in text and normalize(axis) in text for subject, axis in pairs)
        observation['questions'].append({'locator': f'/open_questions/{index}', 'id': question['id'],
                                         'text': question['text'], 'matched': matched})
    return observation, reply if any(q['matched'] for q in observation['questions']) else None


def observe(workspace: Path, runtime: Path, out: Path, entry: dict[str, Any], segment: dict[str, Any],
            prompt: bytes, repository: Path, pricing: dict[str, Any]) -> dict[str, Any]:
    """Retain each exit independently, including question pauses and failures."""
    sid = session_id([runtime / segment['events']])
    destination = runtime / 'plugin' / f'segment-{segment["attempt"]}'
    observation: dict[str, Any] = {'session_id': sid, 'day': segment['day'], 'captured_at': stamp(),
                                  'snapshot': str(destination), 'invalid_reasons': [], 'paused': False,
                                  'calls': [], 'provenance': [], 'cost_usd': None, 'files': {}}
    try:
        capture(workspace, destination, pins=observation['files'])
        if not sid:
            raise ValueError('plugin native session ID missing')
        directory = destination / 'sessions' / digest(sid.encode())
        table = json.loads(confined(directory, 'requirements.json').read_text())
        paused = table.get('state') == 'pending_questions'
        observation['paused'] = paused
        for name in ({'pin-check.json', 'requirements.json'} if paused else {*SCHEMAS, 'claim-audit.json', 'luna-calls.jsonl'}):
            if not (directory / name).is_file():
                raise ValueError('missing plugin artifact ' + name)
        raw_pin = json.loads((directory / 'pin-check.json').read_text())
        if raw_pin.get('status') == 'disabled':
            observation['invalid_reasons'].append('plugin_pin_disabled')
        docs = validate_session(destination, sid, prompt, repository, paused=paused, version=segment['cli_version'])
        previous = next((o for o in reversed(entry.get('plugin_observations', [])) if o['session_id'] == sid), None)
        if previous:
            prefix = 'sessions/' + digest(sid.encode()) + '/evidence/'
            if any(observation['files'].get(name) != sha for name, sha in previous['files'].items()
                   if name.startswith(prefix)):
                raise ValueError('plugin immutable evidence changed after resume')
            old_directory = Path(previous['snapshot']) / 'sessions' / digest(sid.encode())
            old_accounting = (old_directory / 'luna-calls.jsonl').read_bytes()
            if not (directory / 'luna-calls.jsonl').read_bytes().startswith(old_accounting):
                raise ValueError('plugin accounting prefix changed after resume')
            old_table = json.loads((old_directory / 'requirements.json').read_text())
            def unanswered(value: dict[str, Any]) -> dict[str, Any]:
                return {**value, 'state': 'pending_questions', 'open_questions':
                        [{**q, 'answer': None} for q in value['open_questions']]}
            if unanswered(old_table) != unanswered(docs['requirements.json']):
                raise ValueError('plugin requirements changed after resume')
        observation['requirements_sha256'] = digest((directory / 'requirements.json').read_bytes())
        if not paused:
            observation['completion_report_sha256'] = digest((directory / 'completion-report.json').read_bytes())
            observation['ledger_sha256'] = digest((directory / 'ledger.json').read_bytes())
            observation['repair_used'] = docs['completion-report.json']['retry']['used']
        if paused and segment.get('application_start_sha256') != application_digest(workspace):
            raise ValueError('plugin question pause changed workspace')
        if not paused:
            ledger = docs['ledger.json']
            for item in ledger['validation']['files']:
                target = confined(workspace, item['path'])
                if not target.is_file() or digest(target.read_bytes()) != item['sha256']:
                    raise ValueError('plugin ledger workspace hash mismatch')
        trusted_native = dict(segment.get('hook_native_sources', {}))
        if previous:
            trusted_native.update(previous.get('control_native_sources', {}))
        verify_native_origin(directory, docs['requirements.json'], runtime / 'codex-home', segment['cli_version'],
                             trusted_sources=trusted_native)
        observation['control_native_sources'] = trusted_native
        observation['valid_documents'] = True
    except Exception as exc:
        # Do not leak private/root text from exceptions into task evidence.
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        observation['invalid_reasons'].append('plugin_artifact_invalid:' + reason[:160])
    if sid:
        directory = destination / 'sessions' / digest(sid.encode())
        checks = accounting(directory, sid, repository, pricing, paused=observation['paused'])
        artifact_reasons = observation['invalid_reasons']
        observation.update(checks)
        observation['invalid_reasons'] = artifact_reasons + checks['invalid_reasons']
        # accounting() must not discard artifact validation failures.
        if not observation.get('valid_documents'):
            observation['invalid_reasons'].append('plugin_required_artifacts_invalid')
        if observation.get('valid_documents'):
            try:
                documents = ['requirements.json'] + ([] if observation['paused'] else ['claim-audit.json'])
                records_by_id = {json.loads(line)['call_id']: json.loads(line)
                                 for line in (directory / 'luna-calls.jsonl').read_text().splitlines()}
                for name in documents:
                    value = json.loads((directory / name).read_text())
                    ref = value['luna_call']
                    phase = 'requirements' if name == 'requirements.json' else 'claim_audit'
                    if ref is None or records_by_id[ref['call_id']]['phase'] != phase:
                        raise ValueError('call reference mismatch')
            except (OSError, ValueError, KeyError, TypeError):
                observation['invalid_reasons'].append('plugin_call_reference_mismatch')
    # Audit every byte as a captured output, in addition to parsing native tool streams.
    outputs = [{'type': 'thread.started', 'thread_id': sid or 'unknown'}]
    for name, sha in observation['files'].items():
        path = destination / name
        outputs.append({'type': 'item.completed', 'item': {'type': 'command_execution',
                        'command': 'cat ' + json.dumps('.localharness/v3/' + name),
                        'aggregated_output': path.read_text(errors='replace'), 'exit_code': 0}})
    outputs.append({'type': 'turn.completed', 'usage': dict.fromkeys(TOKEN_KEYS, 0)})
    audit_file = destination / 'artifact-outputs.jsonl'
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text(''.join(json.dumps(v) + '\n' for v in outputs))
    audit_paths = [audit_file]
    for name in observation['files']:
        if name.endswith(('-native.jsonl', '-rollout.jsonl')):
            source = destination / name
            if name.endswith('-rollout.jsonl'):
                # Only this code-owned metadata fragment intentionally lacks a final newline.
                target = destination / 'audit-streams' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes().rstrip(b'\n') + b'\n')
                audit_paths.append(target)
            else:
                # Provider event streams retain their exact bytes and truncation checks.
                audit_paths.append(source)
    observation['audit_paths'] = [str(p) for p in audit_paths]
    entry.setdefault('plugin_observations', []).append(observation)
    # Publish redacted copies later through core.publish; raw evidence remains hash-pinned.
    return observation


def latest_observations(entry: dict[str, Any]) -> list[dict[str, Any]]:
    latest: dict[str, Any] = {}
    for observation in entry.get('plugin_observations', []):
        latest[observation['session_id']] = observation
    return list(latest.values())


def task_accounting(entry: dict[str, Any], provenance: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float | None]:
    observations = latest_observations(entry)
    calls = [call for observation in observations for call in observation['calls']]
    provenance.extend(row for observation in observations for row in observation['provenance'])
    return calls, total([o['cost_usd'] for o in observations]) if observations else None


def executor_native(paths: list[Path], ids: set[str | None]) -> list[Path]:
    """Exclude nested Luna threads from Sol settings, usage and version checks."""
    return [path for path in paths if any(e.get('type') == 'session_meta' and
            e.get('payload', {}).get('id') in ids for e in records(path))]


def injection_receipt(native_paths: list[Path], prior: dict[str, Any]) -> dict[str, Any] | None:
    """Observe the real SessionStart context before tools; never inject a ledger."""
    prior_path = Path(prior['snapshot']) / 'sessions' / digest(prior['session_id'].encode()) / 'ledger.json'
    expected = json.loads(prior_path.read_text())
    marker = 'HARNESS_LEDGER (validated against this workspace):\n'
    for path in native_paths:
        for line, event in enumerate(records(path), 1):
            item = event.get('payload', event.get('item', {}))
            tool_item = item.get('item', item) if isinstance(item, dict) else {}
            if isinstance(tool_item, dict) and tool_item.get('type') in {
                    'function_call', 'custom_tool_call', 'command_execution', 'file_change',
                    'CommandExecution', 'FileChange', 'McpToolCall', 'WebSearch'}:
                return None
            strings: list[str] = []

            def leaves(value: Any) -> None:
                if isinstance(value, str):
                    strings.append(value)
                elif isinstance(value, dict):
                    for v in value.values():
                        leaves(v)
                elif isinstance(value, list):
                    for v in value:
                        leaves(v)

            # Only native user/developer context can attest injection; assistant prose cannot.
            if (event.get('type') == 'response_item' and isinstance(item, dict) and
                    item.get('type') == 'message' and item.get('role') in {'user', 'developer'}):
                leaves(item)
            for text in strings:
                if marker not in text:
                    continue
                try:
                    injected, _ = json.JSONDecoder().raw_decode(text.split(marker, 1)[1])
                    # Revalidation changes hook-owned timestamps/hashes; decisions must remain identical.
                    if ({k: v for k, v in injected.items() if k != 'validation'} !=
                            {k: v for k, v in expected.items() if k != 'validation'} or
                            injected['validation']['status'] != 'valid'):
                        continue
                    return {'source_ledger_sha256': prior['ledger_sha256'],
                            'injected_ledger_sha256': digest(json.dumps(injected, sort_keys=True).encode()),
                            'native_log_sha256': digest(path.read_bytes()), 'line': line,
                            'revalidated': True, 'observed_at': stamp()}
                except (ValueError, KeyError, TypeError):
                    continue
    return None


def application_digest(workspace: Path) -> str:
    """Pin a question-only pause independently of hook-owned artifact writes."""
    rows = []
    for path in sorted(workspace.rglob('*')):
        relative = path.relative_to(workspace)
        if relative.parts[0] in {'.localharness', '.git'}:
            continue
        if path.is_symlink():
            rows.append([relative.as_posix(), 'symlink', str(path.readlink())])
        elif path.is_file():
            rows.append([relative.as_posix(), digest(path.read_bytes())])
    return digest(json.dumps(rows).encode())


def verify_native_origin(directory: Path, table: dict[str, Any], home: Path, version: str, *,
                         trusted_sources: dict[str, str]) -> None:
    """Bind the hook table to retained Luna output and its independent native thread."""
    path = directory / 'evidence/requirements-native.jsonl'
    events = records(path)
    matches = []
    for event in events:
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and item.get('type') == 'agent_message':
            try:
                value = json.loads(item['text'])
                rows = [{k: row[k] for k in ('text', 'kind', 'source_excerpt')} for row in table['requirements']]
                questions = [{'text': q['text'], 'requirement_numbers':
                              [int(r.removeprefix('R-')) for r in q['requirement_ids']]}
                             for q in table['open_questions']]
                matches.append(value == {'requirements': rows, 'open_questions': questions})
            except (ValueError, KeyError, TypeError):
                continue
    if not any(matches):
        raise ValueError('plugin table lacks native generation provenance')
    for phase in ('requirements', 'claim_audit'):
        capture_path = directory / f'evidence/{phase}-native.jsonl'
        if not capture_path.exists():
            continue
        sid = session_id([capture_path])
        native = executor_native(sorted((home / 'sessions').rglob('*.jsonl')), {sid}) if sid else []
        if len(native) != 1:
            raise ValueError('plugin child native thread missing or ambiguous')
        if trusted_sources.get(str(native[0])) != digest(native[0].read_bytes()):
            raise ValueError('plugin child thread not captured during this session invocation')
        metadata = [e['payload'] for e in records(native[0]) if e.get('type') == 'session_meta']
        native_events = records(native[0])
        if any(m.get('cli_version') != version.removeprefix('codex-cli ') for m in metadata):
            raise ValueError('plugin child version mismatch')
        contexts = [e['payload'] for e in native_events if e.get('type') == 'turn_context']
        if not contexts or any(c.get('model') != MODEL or c.get('effort', c.get('reasoning_effort')) != 'low'
                               for c in contexts):
            raise ValueError('plugin child model/effort mismatch')
        recorded = [json.dumps(e, sort_keys=True) for e in native_events]
        captured = records(directory / f'evidence/{phase}-rollout.jsonl')
        if not captured or any(json.dumps(e, sort_keys=True) not in recorded for e in captured):
            raise ValueError('plugin native accounting fragment differs from child thread')


def verify_installation(home: Path, installation: dict[str, Any]) -> None:
    """Detect modification of installed hooks/configuration across executor turns."""
    for name, sha in installation.get('installed', {}).items():
        path = confined(home, name)
        if not path.is_file() or digest(path.read_bytes()) != sha:
            raise ValueError('plugin installed runtime changed')
