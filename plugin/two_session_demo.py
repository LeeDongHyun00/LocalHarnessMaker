"""Host-only real two-session handoff capture; each day is invoked separately."""
from __future__ import annotations

import argparse
import hashlib
from datetime import date
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any
from uuid import uuid4

from plugin import demo
from plugin.check_demo_evidence import audit as audit_day_one
from plugin.hooks._runtime import validate

FOLLOWUP = (
    "Use the release label decided yesterday to create followup.txt containing that label "
    "and one newline. Verify the exact bytes with Python. Use the injected handoff; "
    "do not search prior transcripts or ask me to repeat the label. Leave result.txt unchanged. "
    "Display the injected contract and wait for approval before writing."
)


def records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def capture(metadata: dict[str, Any], stage: str, *, allow_stop_error: bool = False) -> None:
    """Retain state and the transcript named by this day's own hook events."""
    out, workspace = Path(metadata['out']), Path(metadata['workspace'])
    events = records(out / 'hooks.jsonl')
    if not events or any(e['error'] is not None and not (allow_stop_error and e['event'] == 'Stop') for e in events):
        raise ValueError('missing or failed hooks')
    transcript = Path(next(e['input']['transcript_path'] for e in events
                           if e['input'].get('transcript_path')))
    shutil.copyfile(transcript, out / f'{stage}-transcript.jsonl')
    shutil.copytree(workspace / '.harness', out / f'{stage}-state')
    demo.write_json(out / f'{stage}-workspace.json', {'files': demo.workspace_files(workspace)})


def visible(path: Path, context: str) -> bool:
    return any(row.get('type') == 'response_item' and row['payload'].get('role') == 'developer'
               and any(part.get('text') == context for part in row['payload'].get('content', []))
               for row in records(path))


def audit(root: Path) -> dict[str, Any]:
    """Audit retained evidence only; never launch Codex or trust success summaries."""
    root = root.resolve()
    audit_day_one(root / 'day1')
    first = demo_metadata(root / 'day1')
    second = demo_metadata(root / 'day2')
    day2 = root / 'day2'
    label = first['release_label']
    validation = json.loads((root / 'handoff-validation.json').read_text())
    command = validation['command']
    if (validation['exit_code'] != 0 or not command or not command[0]
            or command[1:-1] != ['-m', 'verifier', 'validate-handoff', '--handoff']
            or Path(command[-1]).parts[-3:] != ('day1', 'approval-state', 'handoff.json')
            or validation['stdout'] != command[-1] + '\n'
            or validation['sha256'] != hashlib.sha256((root / 'day1/approval-state/handoff.json').read_bytes()).hexdigest()):
        raise ValueError('saved handoff CLI validation failed')
    if second['prompt'] != FOLLOWUP or label in FOLLOWUP:
        raise ValueError('follow-up restated context')
    if first['version'] != second['version'] or first['workspace'] != second['workspace'] or first['codex_home'] != second['codex_home']:
        raise ValueError('version/home/workspace changed')
    if first['thread_id'] == second['thread_id']:
        raise ValueError('day 2 must be a new session')
    handoff_path = root / 'day1/approval-state/handoff.json'
    handoff = validate(handoff_path, 'handoff.schema.json')
    if label not in json.dumps(handoff['decisions']):
        raise ValueError('day-1 decision missing from validated handoff')
    if (day2 / 'incoming-handoff.json').read_bytes() != handoff_path.read_bytes():
        raise ValueError('incoming handoff changed')
    events = records(day2 / 'hooks.jsonl')
    if not events or any(e['error'] is not None or e['input']['session_id'] != second['thread_id']
                         or Path(e['input']['cwd']).resolve() != Path(second['workspace']).resolve() for e in events):
        raise ValueError('missing, failed or unrelated hooks')
    context = 'HARNESS_HANDOFF\n' + handoff_path.read_text()
    if not (events[0]['event'] == 'SessionStart'
            and events[0]['output']['hookSpecificOutput'] == {
                'hookEventName': 'SessionStart', 'additionalContext': context}):
        raise ValueError('SessionStart did not inject the saved handoff')
    if not visible(day2 / 'request-transcript.jsonl', context):
        raise ValueError('handoff absent from session-2 model context')
    submitted = [e for e in events if e['event'] == 'UserPromptSubmit']
    if [e['input']['prompt'] for e in submitted] != [FOLLOWUP, 'approve']:
        raise ValueError('user restated context or unexpected user turn')
    pending = json.loads((day2 / 'request-state/session.json').read_text())
    completed = json.loads((day2 / 'approval-state/session.json').read_text())
    if (pending['session_id'] != second['thread_id'] or completed['session_id'] != pending['session_id']
            or pending['phase'] != 'awaiting_approval' or completed['phase'] != 'complete'
            or json.loads((day2 / 'request-state/state.json').read_text())['attempt'] != 0):
        raise ValueError('session-2 approval gate failed')
    # Old day-1 verdict can persist before day-2 approval; compare the saved
    # baseline rather than treating its mere presence as a verifier call.
    initial = json.loads((day2 / 'initial-workspace.json').read_text())
    if (root / 'day1-artifact/result.txt').read_bytes() != b'ok\n' or sorted(p.name for p in (root / 'day1-artifact').iterdir()) != ['result.txt']:
        raise ValueError('unexpected day-1 task artifact')
    expected_inventory = demo.workspace_files(root / 'day1-artifact')
    if initial != {'files': expected_inventory}:
        raise ValueError('unexpected day-2 baseline')
    for name in ('request-workspace.json', 'before-approval-workspace.json'):
        if json.loads((day2 / name).read_text()) != initial:
            raise ValueError('task changed before day-2 approval')
    contract = validate(day2 / 'approval-state/contract.json', 'contract.schema.json')
    if (day2 / 'request-state/contract.json').read_bytes() != (day2 / 'approval-state/contract.json').read_bytes():
        raise ValueError('approved contract changed')
    contract_context = submitted[0]['output']['hookSpecificOutput']['additionalContext']
    if (day2 / 'request-state/contract.json').read_text() not in contract_context or not visible(day2 / 'approval-transcript.jsonl', contract_context):
        raise ValueError('day-2 contract absent from context')
    verdict = validate(day2 / 'approval-state/verdict.json', 'verdict.schema.json')
    attempt = json.loads((day2 / 'approval-state/state.json').read_text())['attempt']
    if (verdict['overall'] != 'pass' or verdict['attempt'] != attempt
            or not 1 <= attempt <= second['max_attempts']
            or any(i['status'] != 'pass' for i in verdict['items'])
            or {i['id'] for i in verdict['items']} != {i['id'] for i in contract['success_criteria']}):
        raise ValueError('day-2 verdict did not pass')
    for stage in ('request', 'approval'):
        result = json.loads((day2 / f'{stage}-result.json').read_text())
        command = result['command']
        if result['exit_code'] != 0 or command.count('exec') != 1 or ('resume' in command) != (stage == 'approval'):
            raise ValueError('invalid day-2 executor command/result')
        if stage == 'approval' and command[command.index('resume') + 1] != second['thread_id']:
            raise ValueError('approval resumed wrong session')
    if (day2 / 'followup.txt').read_bytes() != (label + '\n').encode() or (day2 / 'result.txt').read_bytes() != b'ok\n':
        raise ValueError('follow-up did not recover day-1 decision')
    return {'saved_handoff_validated': True, 'session_start_injected': True,
            'context_visible': True, 'new_session': True, 'user_restatement_needed': False,
            'approval_gates': True, 'overall': 'pass'}


def demo_metadata(out: Path) -> dict[str, Any]:
    return json.loads((out / 'experiment.json').read_text())


def check_version(metadata: dict[str, Any]) -> None:
    """Bound the host identity probe and bypass nested harness hooks."""
    result = demo.run_group([metadata['codex'], '--version'], env={**os.environ, 'HARNESS_NESTED': '1'},
                            capture_output=True, text=True, shell=False, check=False, timeout=5)
    if result.returncode != 0 or result.stdout.strip() != metadata['version']:
        raise ValueError('Codex version changed; stop and collect a new compatibility probe')


def day_one(root: Path, scripted: bool) -> None:
    metadata = demo.prepare(root / 'day1', mode='real')
    label = 'release-' + uuid4().hex[:12]
    metadata['release_label'] = label
    metadata['prompt'] = demo.REAL_PROMPT + (
        f' Also record this decision in your final report for the next session: the release label is {label}. '
        'Explain that it was chosen by the user for the next-day follow-up. '
        'Do not store the label in a task file; result.txt must still contain only ok and a newline.'
    )
    demo.write_json(Path(metadata['out']) / 'experiment.json', metadata)
    demo.launch(metadata, 'request')
    demo.collect(metadata, 'request')
    check_version(metadata)
    demo.finish(metadata, scripted)
    check_version(metadata)
    audit_day_one(root / 'day1')
    handoff = validate(root / 'day1/approval-state/handoff.json', 'handoff.schema.json')
    if label not in json.dumps(handoff['decisions']):
        raise ValueError('handoff lost the decision; retain failure evidence and use a fresh run')
    command = [sys.executable, '-m', 'verifier', 'validate-handoff', '--handoff', str(root / 'day1/approval-state/handoff.json')]
    result = demo.run_group(command, cwd=demo.ROOT, env={**os.environ, 'HARNESS_NESTED': '1'},
                            capture_output=True, text=True, shell=False, check=False, timeout=5)
    demo.write_json(root / 'handoff-validation.json', {'command': command, 'exit_code': result.returncode,
                                                     'stdout': result.stdout, 'stderr': result.stderr,
                                                     'sha256': hashlib.sha256(Path(command[-1]).read_bytes()).hexdigest()})
    if result.returncode != 0 or result.stdout != command[-1] + '\n':
        raise ValueError('saved handoff CLI validation failed')
    (root / 'day1-artifact').mkdir()
    shutil.copyfile(root / 'day1/result.txt', root / 'day1-artifact/result.txt')


def day_two(root: Path, scripted: bool) -> None:
    audit_day_one(root / 'day1')
    first = demo_metadata(root / 'day1')
    check_version(first)
    out = root / 'day2'
    out.mkdir()  # Never overwrite or retry an attempted day 2.
    metadata = {k: v for k, v in first.items() if k not in {'thread_id', 'release_label'}}
    metadata.update(out=str(out), prompt=FOLLOWUP, approval='pending')
    workspace = Path(metadata['workspace'])
    if (workspace / '.harness/handoff.json').read_bytes() != (root / 'day1/approval-state/handoff.json').read_bytes():
        raise ValueError('live handoff differs from saved day-1 handoff')
    shutil.copyfile(workspace / '.harness/handoff.json', out / 'incoming-handoff.json')
    demo.write_json(out / 'initial-workspace.json', {'files': demo.workspace_files(workspace)})
    demo.write_json(out / 'experiment.json', metadata)
    demo.launch(metadata, 'request')  # No resume: new thread, same home/project.
    capture(metadata, 'request')
    check_version(metadata)
    print((out / 'request-reply.txt').read_text())
    pending = json.loads((out / 'request-state/session.json').read_text())
    if pending['phase'] != 'awaiting_approval':
        raise ValueError('day 2 did not wait for approval')
    approval = 'approve' if scripted else input('Review day-2 contract. Type approve: ').strip()
    if approval != 'approve':
        raise ValueError('approval not supplied; retain evidence and use a fresh run')
    demo.write_json(out / 'before-approval-workspace.json', {'files': demo.workspace_files(workspace)})
    initial = json.loads((out / 'initial-workspace.json').read_text())
    if any(json.loads((out / name).read_text()) != initial for name in ('request-workspace.json', 'before-approval-workspace.json')):
        raise ValueError('task changed before approval')
    demo.launch(metadata, 'approval')
    capture(metadata, 'approval')
    check_version(metadata)
    for name in ('result.txt', 'followup.txt'):
        shutil.copyfile(workspace / name, out / name)
    summary = audit(root)
    demo.write_json(root / 'audit.json', summary)
    print(json.dumps(summary, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('day1', 'day2', 'check'))
    parser.add_argument('--out', type=Path, default=demo.PLUGIN / 'evidence' / f'{date.today()}-two-session')
    parser.add_argument('--scripted-approval', action='store_true')
    args = parser.parse_args()
    try:
        root = args.out.resolve()
        if args.stage == 'check':
            print(json.dumps(audit(root), sort_keys=True))
        elif args.stage == 'day1':
            if root.exists():
                raise ValueError('use a new evidence directory')
            day_one(root, args.scripted_approval)
        else:
            day_two(root, args.scripted_approval)
        return 0
    except Exception as exc:
        print(f'two-session demo failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
