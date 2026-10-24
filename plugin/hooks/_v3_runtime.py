"""Pinned-Luna lifecycle state machine; deterministic work belongs to verifier."""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

from plugin import pin_check
from plugin.artifacts import (atomic_bytes, confined, digest, locked, read, session_directory,
                              snapshot, validate, verify_reference, workspace_hash, write)
from plugin.v3_adapter import Adapter


class Runtime:
    def __init__(self, payload: dict[str, Any], *, adapter: Adapter | None = None) -> None:
        self.payload = payload
        self.workspace = Path(payload['cwd']).resolve(strict=True)
        self.session_id = payload['session_id']
        self.directory = session_directory(self.workspace, self.session_id)
        self.root = self.directory.parents[1]
        self.state_path = confined(self.directory, 'hook-state.json')
        event = payload['hook_event_name']
        self.adapter = adapter or Adapter(budget={'SessionStart': 5, 'UserPromptSubmit': 35, 'Stop': 650}[event])
        self.state: dict[str, Any] = {}

    @property
    def cli_seconds(self) -> float:
        return self.adapter.seconds

    def save(self) -> None:
        write(self.state_path, self.state)

    def context(self, text: str) -> dict[str, Any]:
        return {'hookSpecificOutput': {'hookEventName': self.payload['hook_event_name'],
                                       'additionalContext': text}}

    def advisory(self, text: str) -> None:
        print('LocalHarnessMaker advisory: ' + text, file=sys.stderr)

    def dispatch(self, event: str) -> dict[str, Any] | None:
        with locked(self.directory):
            self.state = read(self.state_path) if self.state_path.exists() else {'session_id': self.session_id}
            if self.state.get('session_id') != self.session_id:
                raise ValueError('hook state native session identity mismatch')
            return {'SessionStart': self.start, 'UserPromptSubmit': self.prompt, 'Stop': self.stop}[event]()

    def pin(self) -> dict[str, Any] | None:
        path = confined(self.directory, 'pin-check.json')
        if not path.exists():
            return None
        value = read(path)
        validate(value, 'pin-check.schema.json')
        if value['session_id'] != self.session_id:
            raise ValueError('pin session mismatch')
        for key in ('model_list', 'pricing_snapshot'):
            if value[key] is not None:
                verify_reference(self.directory, value[key])
        return value

    def enabled(self) -> bool:
        pin = self.pin()
        return bool(pin and pin['status'] == 'enabled')

    def start(self) -> dict[str, Any] | None:
        if self.state.get('started'):
            return None
        # Reserve before probes so interrupted/resumed starts cannot reset a pin.
        self.state['started'] = True
        self.save()
        pin = self.pin()
        if pin is None:
            from plugin.install import resolve_codex
            pin = pin_check.check(self.session_id, self.directory, resolve_codex() or 'codex',
                                  runner=self.adapter.runner)
        texts = [pin['advisory']]
        try:
            texts.append(self.prior_ledger())
        except Exception as exc:
            texts.append(f'Prior ledger not injected: {type(exc).__name__}: {exc}')
        return self.context('\n\n'.join(texts))

    def prior_ledger(self) -> str:
        candidates: list[tuple[datetime, Path, str]] = []
        sessions = confined(self.root, 'sessions')
        for directory in sessions.iterdir():
            if directory == self.directory:
                continue
            confined(sessions, directory.name)
            if not directory.is_dir():
                raise ValueError('invalid prior session entry')
            pin = read(confined(directory, 'pin-check.json'))
            validate(pin, 'pin-check.schema.json')
            if digest(pin['session_id'].encode()) != directory.name or pin['session_id'] == self.session_id:
                raise ValueError('prior session directory identity mismatch')
            candidates.append((datetime.fromisoformat(pin['checked_at'].replace('Z', '+00:00')),
                               directory, pin['session_id']))
        latest = confined(self.root, 'latest-ledger.json')
        if not candidates:
            if latest.exists():
                raise ValueError('latest ledger has no prior session')
            return 'No prior session ledger.'
        candidates.sort(key=lambda row: row[0], reverse=True)
        if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
            raise ValueError('prior pin timestamp tie')
        _, directory, session_id = candidates[0]
        source = confined(directory, 'ledger.json')
        value = read(source)
        validate(value, 'ledger.schema.json')
        if (value['session_id'] != session_id or read(latest) != value
                or value['validation'] is None or value['validation']['status'] != 'valid'):
            raise ValueError('latest ledger identity/content does not match most recent prior session')
        verify_reference(directory, value['requirements'])
        result = self.adapter.call('verifier', 'ledger-validate', session_id=session_id,
                                   directory=directory, workspace=self.workspace, ledger=source)
        checked = read(source)
        validate(checked, 'ledger.schema.json')
        if (result.returncode != 0 or checked['session_id'] != session_id
                or checked['validation'] is None or checked['validation']['status'] != 'valid'):
            raise ValueError('prior ledger no longer validates against workspace')
        self.check_ledger(checked, directory)
        atomic_bytes(latest, source.read_bytes())
        return 'HARNESS_LEDGER (validated against this workspace):\n' + json.dumps(checked, ensure_ascii=False)

    def check_ledger(self, value: dict[str, Any], directory: Path) -> None:
        """Check validation coverage/hashes after the trusted verifier remeasures."""
        if value['requirements']['path'] != 'requirements.json':
            raise ValueError('ledger requirements target mismatch')
        verify_reference(directory, value['requirements'])
        expected = [(d['id'], f['kind'], f['value'], f['path'])
                    for d in value['decisions'] for f in d['fixes']]
        observed = [(i['decision_id'], i['kind'], i['value'], i['path'])
                    for i in value['validation']['identifiers']]
        if sorted(expected) != sorted(observed) or len(set(expected)) != len(expected):
            raise ValueError('ledger identifier validation coverage mismatch')
        if len({d['id'] for d in value['decisions']}) != len(value['decisions']):
            raise ValueError('duplicate ledger decision IDs')
        files = value['validation']['files']
        if (sorted(f['path'] for f in files) != sorted({fix[3] for fix in expected})
                or any(not i['found'] for i in value['validation']['identifiers'])):
            raise ValueError('ledger validation missing files/identifiers')
        for reference in [*files, *value['validation']['identifiers']]:
            path = confined(self.workspace, reference['path'])
            if digest(path.read_bytes()) != reference['sha256']:
                raise ValueError('ledger workspace hash no longer matches')

    def unavailable(self, prompt_ref: dict[str, str]) -> None:
        write(confined(self.directory, 'requirements.json'), {
            'schema_version': 3, 'session_id': self.session_id, 'prompt': prompt_ref,
            'state': 'unavailable', 'requirements': [], 'open_questions': [], 'luna_call': None})

    def requirements(self) -> dict[str, Any]:
        value = read(confined(self.directory, 'requirements.json'))
        validate(value, 'requirements.schema.json')
        if value['session_id'] != self.session_id:
            raise ValueError('requirements session mismatch')
        prompt = verify_reference(self.directory, value['prompt']).read_text()
        for number, row in enumerate(value['requirements'], 1):
            if (row['number'] != number or row['id'] != f'R-{number}'
                    or row['source_excerpt'] not in prompt):
                raise ValueError('requirement numbering/source mismatch')
            check = row['check']
            for key in ('path', 'cwd'):
                if key in check and check[key] != '.':
                    confined(self.workspace, check[key])
        return value

    def accounting(self, phase: str) -> dict[str, Any]:
        path = confined(self.directory, 'luna-calls.jsonl')
        raw = path.read_bytes()
        if raw and not raw.endswith(b'\n'):
            raise ValueError('truncated accounting JSONL')
        prior = self.state.get('accounting_prefix')
        if prior and not raw.startswith(confined(self.directory, prior).read_bytes()):
            raise ValueError('accounting JSONL was rewritten instead of appended')
        rows = [json.loads(line) for line in raw.decode().splitlines()]
        if len(rows) > 2 or len({r['call_id'] for r in rows}) != len(rows):
            raise ValueError('Luna call budget/identity violated')
        for row in rows:
            validate(row, 'luna-call.schema.json')
            if row['session_id'] != self.session_id:
                raise ValueError('Luna call session mismatch')
            pin = self.pin()
            if row['pricing_ref'] != (pin or {}).get('pricing_ref'):
                raise ValueError('Luna accounting pricing snapshot mismatch')
            if (row['cached_input_tokens'] is not None and row['input_tokens'] is not None
                    and row['cached_input_tokens'] > row['input_tokens']):
                raise ValueError('cached tokens exceed input tokens')
            if row['model'] not in (None, pin_check.MODEL) or row['status'] == 'pin_mismatch':
                pin = self.pin()
                if pin:
                    pin.update(status='disabled', advisory='Luna hooks disabled: provider model identity mismatch. Not H3.')
                    pin['reason_codes'] = list(dict.fromkeys([*pin['reason_codes'], 'model_identity_mismatch']))
                    write(confined(self.directory, 'pin-check.json'), pin)
                raise ValueError('provider model identity mismatch; Luna disabled')
        if any(sum(r['phase'] == p for r in rows) > 1 for p in ('requirements', 'claim_audit')):
            raise ValueError('duplicate phase calls')
        matches = [r for r in rows if r['phase'] == phase]
        if len(matches) != 1 or matches[0]['status'] != 'success' or matches[0]['model'] != pin_check.MODEL:
            raise ValueError('missing/unsuccessful observed Luna call')
        prefix = snapshot(self.directory, f'accounting-{phase}.jsonl', raw)
        self.state['accounting_prefix'] = prefix['path']
        self.save()
        return matches[0]

    def table(self, requirements: dict[str, Any]) -> str:
        def cell(text: str) -> str:
            return text.replace('|', '\\|').replace('\n', ' ')
        lines = ['HARNESS_REQUIREMENTS — show this table before work.',
                 '| ID | Requirement | Kind | Check |', '| --- | --- | --- | --- |']
        for row in requirements['requirements']:
            lines.append(f'| {row["id"]} | {cell(row["text"])} | {row["kind"]} | {row["check"]["type"]} |')
        unanswered = [q for q in requirements['open_questions'] if q['answer'] is None]
        if unanswered:
            lines += ['', 'Open questions:', *(f'{q["id"]}: {q["text"]}' for q in unanswered),
                      'Ask these questions and END THIS TURN before changing any file. Never assume an answer.',
                      'Record explicit answers by having the user send JSON: {"answers":{"QUESTION_ID":"answer"}}.']
        return '\n'.join(lines)

    def prompt(self) -> dict[str, Any] | None:
        text = self.payload.get('prompt')
        if not isinstance(text, str):
            raise ValueError('prompt text missing')
        if self.state.get('requirements_reserved'):
            requirements = self.requirements()
            if requirements['state'] == 'pending_questions':
                # The only automatic mapping is an explicit user-authored ID/value object.
                try:
                    answers = json.loads(text)['answers']
                    if not isinstance(answers, dict) or any(not isinstance(v, str) or not v.strip() for v in answers.values()):
                        raise ValueError('answers must be nonempty strings')
                    questions = {q['id']: q for q in requirements['open_questions']}
                    if not answers or not answers.keys() <= questions.keys():
                        raise ValueError('unknown question IDs')
                    snapshot(self.directory, f'answers-{digest(text.encode())}.json', text.encode())
                    for key, answer in answers.items():
                        if questions[key]['answer'] is not None and questions[key]['answer'] != answer:
                            raise ValueError('answer already recorded')
                        questions[key]['answer'] = answer
                    if all(q['answer'] is not None for q in questions.values()):
                        requirements['state'] = 'ready'
                    validate(requirements, 'requirements.schema.json')
                    write(confined(self.directory, 'requirements.json'), requirements)
                except (ValueError, KeyError, TypeError):
                    return self.context(self.table(requirements))
                return self.context(self.table(requirements))
            return None
        self.state.update(requirements_reserved=True, pre_edit_hash=workspace_hash(self.workspace))
        self.save()
        reference = snapshot(self.directory, 'prompt.txt', text.encode())
        self.unavailable(reference)
        if not self.enabled():
            return self.context('Luna requirements skipped: pin disabled or missing. Ordinary session; not H3.')
        try:
            self.adapter.call('controller', 'requirements', session_id=self.session_id,
                              directory=self.directory, prompt=confined(self.directory, reference['path']))
            call = self.accounting('requirements')
            requirements = self.requirements()
            if requirements['luna_call'] is None or requirements['luna_call']['call_id'] != call['call_id']:
                raise ValueError('requirements call reference mismatch')
            return self.context(self.table(requirements))
        except Exception as exc:
            self.unavailable(reference)
            return self.context(f'Luna requirements unavailable: {type(exc).__name__}: {exc}. Not H3; no retry.')

    def final_message(self) -> dict[str, str] | None:
        transcript = self.payload.get('transcript_path')
        if not transcript:
            return None
        from verifier.claims import last_report
        message = last_report(Path(transcript))
        if not message:
            return None
        return snapshot(self.directory, f'final-{digest(message.encode())}.txt', message.encode())

    def load_report(self, requirements: dict[str, Any]) -> dict[str, Any]:
        report = read(confined(self.directory, 'completion-report.json'))
        validate(report, 'completion-report.schema.json')
        if report['session_id'] != self.session_id:
            raise ValueError('report session mismatch')
        verify_reference(self.directory, report['requirements'])
        if report['requirements']['path'] != 'requirements.json':
            raise ValueError('report requirements target mismatch')
        ids = [i['requirement_id'] for i in report['items']]
        if sorted(ids) != sorted(r['id'] for r in requirements['requirements']):
            raise ValueError('report rows do not match requirements')
        for item in report['items']:
            for evidence in item['evidence']:
                verify_reference(self.directory, evidence)
            if item['status'] in ('pass', 'fail') and not item['evidence']:
                raise ValueError('executed verdict lacks evidence')
        return report

    def audit(self, requirements_path: Path, final: dict[str, str] | None) -> Path | None:
        if self.state.get('audit_reserved') or not self.enabled():
            return None
        self.state['audit_reserved'] = True
        self.save()
        if final is None:
            self.advisory('Claim audit unavailable: no retained final message; audit slot closed.')
            return None
        try:
            result = self.adapter.call('controller', 'claim-audit', session_id=self.session_id,
                                       directory=self.directory, requirements=requirements_path,
                                       final=confined(self.directory, final['path']))
            call = self.accounting('claim_audit')
            # Controller stdout is one output path, confined even if absolute.
            output = Path(result.stdout.strip())
            relative = str(output.relative_to(self.directory)) if output.is_absolute() else str(output)
            path = confined(self.directory, relative)
            audit = read(path)
            audit = audit.get('claim_audit', audit)
            if (audit['audited_final_message'] != final or audit['luna_call'] is None
                    or audit['luna_call']['call_id'] != call['call_id']):
                raise ValueError('claim audit source/call mismatch')
            verify_reference(self.directory, audit['audited_final_message'])
            ids = {r['id'] for r in self.requirements()['requirements']}
            for claim in audit['claims']:
                if claim['requirement_id'] not in ids:
                    raise ValueError('audit cites unknown requirement')
                retained = []
                for reference in claim['cited_evidence']:
                    try:
                        verify_reference(self.directory, reference)
                        retained.append(reference)
                    except (ValueError, OSError):
                        claim['assessment'] = 'unsupported'
                claim['cited_evidence'] = retained
            probe = read(confined(self.directory, 'completion-report.json'))
            probe['claim_audit'] = audit
            validate(probe, 'completion-report.schema.json')
            self.state['claim_audit'] = audit
            self.state['audit_path'] = relative
            self.save()
            return path
        except Exception as exc:
            self.advisory(f'Claim audit unavailable (no retry): {type(exc).__name__}: {exc}')
            return None

    def finish_report(self, report: dict[str, Any], final: dict[str, str] | None) -> None:
        report['current_final_message'] = final
        if self.state.get('claim_audit'):
            audit = dict(self.state['claim_audit'])
            if audit['audited_final_message'] != final and audit['status'] == 'complete':
                audit['status'] = 'stale'
                audit['reason'] = 'Final message changed after the single claim audit.'
            report['claim_audit'] = audit
        if self.state.get('repair_used'):
            report['retry'] = {'used': 1, 'failed_requirement_ids': self.state['repair_rows'],
                               'reason': 'Single repair requested for executed deterministic failures.'}
        if report['check_round'] == 2 and any(i['status'] == 'fail' for i in report['items']):
            report['escalation_advice'] = {'recommendation': 'human_review', 'text':
                'Executed checks still fail. Consider higher reasoning effort or human review; no configuration was changed.'}
            self.advisory(report['escalation_advice']['text'])
        validate(report, 'completion-report.schema.json')
        write(confined(self.directory, 'completion-report.json'), report)
        self.advisory('Completion report: ' + str(self.directory / 'completion-report.json') + '\n' +
                      '\n'.join(f'{r["requirement_id"]}: {r["status"]}: {r["reason"]}' for r in report['items']))

    def stop(self) -> dict[str, Any] | None:
        if not self.state.get('requirements_reserved') or self.state.get('finished'):
            return None
        requirements = self.requirements()
        current_hash = workspace_hash(self.workspace)
        if requirements['state'] == 'pending_questions' and current_hash == self.state['pre_edit_hash']:
            return None
        final = self.final_message()
        # Count assistant final records, not arbitrary hook/tool log additions.
        # An unchanged repeated final after an actual continuation still advances.
        transcript = self.payload.get('transcript_path')
        final_count = 0
        if transcript:
            for line in Path(transcript).read_text().splitlines():
                record = json.loads(line)
                payload = record.get('payload', {})
                if (record.get('type') == 'response_item' and payload.get('type') == 'message'
                        and payload.get('role') == 'assistant' and payload.get('phase') == 'final_answer'):
                    final_count += 1
        fingerprint = digest(json.dumps([current_hash, final, final_count], sort_keys=True).encode())
        if fingerprint in self.state.get('stop_events', []):
            return None
        self.state.setdefault('stop_events', []).append(fingerprint)
        self.save()
        requirements_path = confined(self.directory, 'requirements.json')
        if not self.state.get('checks_settled'):
            round_number = 2 if self.state.get('repair_used') else 1
            # Reservation prevents a crashed check/audit hook from reusing round 1.
            if self.state.get(f'round_{round_number}_reserved'):
                self.advisory('Interrupted completion phase; no automatic retry. Not a valid H3 completion.')
                self.state['checks_settled'] = True
                self.save()
                return None
            self.state[f'round_{round_number}_reserved'] = True
            self.save()
            result = self.adapter.call('verifier', 'check', session_id=self.session_id,
                                       directory=self.directory, workspace=self.workspace,
                                       requirements=requirements_path, round_number=round_number,
                                       final=confined(self.directory, final['path']) if final else None,
                                       audit=confined(self.directory, self.state['audit_path']) if self.state.get('audit_path') else None)
            summary = json.loads(result.stdout)
            if (set(summary) != {'overall', 'failed_rows', 'unverifiable_rows', 'retry_warranted'}
                    or type(summary['retry_warranted']) is not bool):
                raise ValueError('unsupported verifier summary')
            report = self.load_report(requirements)
            if report['check_round'] != round_number:
                raise ValueError('verifier check round mismatch')
            failed = [r['requirement_id'] for r in report['items'] if r['status'] == 'fail']
            if sorted(summary['failed_rows']) != sorted(failed):
                raise ValueError('verifier failed rows mismatch')
            if round_number == 1:
                self.audit(requirements_path, final)
            if summary['retry_warranted'] and failed and not self.state.get('repair_used'):
                message = self.adapter.repair_text(requirements, report, failed)
                self.state.update(repair_used=True, repair_rows=failed)
                self.save()
                self.finish_report(report, final)
                return {'decision': 'block', 'reason': message}
            self.state['checks_settled'] = True
            self.save()
            self.finish_report(report, final)
        else:
            self.finish_report(self.load_report(requirements), final)
        if not self.state.get('ledger_requested'):
            # One bookkeeping reservation, even when the formatter is unavailable.
            self.state['ledger_requested'] = True
            self.save()
            message = self.adapter.ledger_text(self.directory, self.session_id)
            return {'decision': 'block', 'reason': message}
        self.state['finished'] = True
        self.save()
        ledger = confined(self.directory, 'ledger.json')
        try:
            result = self.adapter.call('verifier', 'ledger-validate', session_id=self.session_id,
                                       directory=self.directory, workspace=self.workspace, ledger=ledger)
            value = read(ledger)
            validate(value, 'ledger.schema.json')
            verify_reference(self.directory, value['requirements'])
            if (result.returncode != 0 or value['session_id'] != self.session_id
                    or value['validation'] is None or value['validation']['status'] != 'valid'):
                raise ValueError('ledger invalid')
            self.check_ledger(value, self.directory)
            atomic_bytes(confined(self.root, 'latest-ledger.json'), ledger.read_bytes())
        except Exception as exc:
            self.advisory(f'Ledger not published or injected: {type(exc).__name__}: {exc}')
        return None
