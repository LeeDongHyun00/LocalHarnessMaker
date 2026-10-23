"""Host-only exhaustion/stale handoff demonstrations, with a read-only offline checker."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from plugin import demo
from plugin.evidence_paths import recorded_path
from plugin.hooks._runtime import validate
from plugin.two_session_demo import capture, check_version, demo_metadata, records, visible

EXHAUST = (
    "This is an intentionally impossible verification demonstration. Make no task files. "
    "The sole success criterion must be a command check running exactly "
    "python -c 'raise SystemExit(1)' with expected exit_code 0. "
    "Run it once after approval, report its failure honestly, and leave it unmet. "
    "Do not repair or bypass the command, change PATH, create python wrappers, or add criteria. "
    "There is only one allowed verification attempt. Display the contract and wait for approval."
)
NEXT = "Show any injected handoff and the new contract, then wait for approval. Do not write task files."
SEED = {'done': [], 'remaining': [], 'decisions': [
    {'what': 'obsolete-release-context', 'why': 'Demo-only previous handoff; must be archived on failure.'}],
    'verify_commands': [], 'do_not_touch': []}


def shim(path: Path) -> None:
    """Intercept only the selected boundary; all other calls use the real interpreter."""
    path.write_text(f'''#!{sys.executable}
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
mode = os.environ.get("HANDOFF_DEMO_FAULT")
generation = args[:3] == ["-m", "controller", "handoff"]
validation = (args[:3] == ["-m", "verifier", "validate-handoff"]
              and any("handoff.pending." in a for a in args))
if (mode == "generation" and generation) or (mode == "validation" and validation):
    with Path(os.environ["HANDOFF_DEMO_FAULT_LOG"]).open("a") as stream:
        stream.write(json.dumps({{"mode": mode, "args": args, "exit_code": 2}}) + "\\n")
    print("injected handoff demo " + mode + " failure", file=sys.stderr)
    sys.exit(2)
os.execv({sys.executable!r}, [{sys.executable!r}, *args])
''')
    path.chmod(0o700)


def approve(metadata: dict[str, Any], scripted: bool, extra: dict[str, str]) -> None:
    out = Path(metadata['out'])
    print((out / 'request-reply.txt').read_text())
    if not scripted and input('Review contract. Type approve: ').strip() != 'approve':
        raise ValueError('approval not supplied; use a fresh evidence directory')
    demo.write_json(out / 'before-approval-workspace.json', {'files': demo.workspace_files(Path(metadata['workspace']))})
    demo.launch(metadata, 'approval', extra_env=extra)
    capture(metadata, 'approval', allow_stop_error=metadata['scenario'] != 'exhaustion')
    if metadata['scenario'] != 'exhaustion':
        shutil.copyfile(Path(metadata['workspace']) / 'result.txt', out / 'result.txt')
    check_version(metadata)


def day_one(root: Path, scenario: str, scripted: bool) -> None:
    metadata = demo.prepare(root / 'day1', mode='real')
    metadata.update(scenario=scenario, max_attempts=1, prompt=EXHAUST if scenario == 'exhaustion' else demo.REAL_PROMPT)
    out, workspace = Path(metadata['out']), Path(metadata['workspace'])
    extra = {'HARNESS_MAX_ATTEMPTS': '1'}
    if scenario != 'exhaustion':
        (workspace / '.harness').mkdir(exist_ok=True)
        demo.write_json(workspace / '.harness/handoff.json', SEED)
        demo.write_json(root / 'previous-handoff.json', SEED)
        wrapper = Path(metadata['codex_home']).parent / 'handoff-fault-python'
        shim(wrapper)
        extra.update(HARNESS_PYTHON=str(wrapper), HANDOFF_DEMO_FAULT=scenario,
                     HANDOFF_DEMO_FAULT_LOG=str(root / 'faults.jsonl'))
    demo.write_json(out / 'experiment.json', metadata)
    demo.launch(metadata, 'request', extra_env=extra)
    demo.collect(metadata, 'request')
    check_version(metadata)
    contract = validate(out / 'request-state/contract.json', 'contract.schema.json')
    if scenario == 'exhaustion':
        checks = [c['check'] for c in contract['success_criteria']]
        if checks != [{'type': 'command', 'command': "python -c 'raise SystemExit(1)'", 'expected': {'exit_code': 0}}]:
            raise ValueError('controller did not preserve impossible criterion; do not approve or repair')
    approve(metadata, scripted, extra)
    print('Day 1 retained. Review verdict, handoff/archive and hook errors before day 2.')


def day_two(root: Path) -> None:
    first = demo_metadata(root / 'day1')
    check_version(first)
    out = root / 'day2'
    out.mkdir()
    metadata = {k: v for k, v in first.items() if k != 'thread_id'}
    metadata.update(out=str(out), prompt=NEXT)
    demo.write_json(out / 'experiment.json', metadata)
    demo.write_json(out / 'initial-workspace.json', {'files': demo.workspace_files(Path(metadata['workspace']))})
    demo.launch(metadata, 'request', extra_env={'HARNESS_MAX_ATTEMPTS': '1'})
    capture(metadata, 'request')
    check_version(metadata)
    summary = audit(root)
    demo.write_json(root / 'audit.json', summary)
    print(json.dumps(summary, sort_keys=True))


def audit(root: Path) -> dict[str, Any]:
    """Require artifacts and hook/context evidence, never a saved success summary."""
    first, second = demo_metadata(root / 'day1'), demo_metadata(root / 'day2')
    scenario = first['scenario']
    if scenario not in {'exhaustion', 'generation', 'validation'} or second['scenario'] != scenario:
        raise ValueError('unknown or changed scenario')
    if (first['thread_id'] == second['thread_id'] or first['version'] != second['version']
            or any(recorded_path(first[k]) != recorded_path(second[k])
                   for k in ('workspace', 'codex_home'))):
        raise ValueError('day 2 must be a fresh session in the same environment')
    for day, meta, stages in [('day1', first, ('request', 'approval')), ('day2', second, ('request',))]:
        folder = root / day
        events = records(folder / 'hooks.jsonl')
        if not events or any(e['input']['session_id'] != meta['thread_id']
                             or recorded_path(e['input']['cwd']) != recorded_path(meta['workspace'])
                             for e in events):
            raise ValueError('missing or unrelated hooks')
        if any(e['error'] is not None for e in events if not (day == 'day1' and scenario != 'exhaustion' and e['event'] == 'Stop')):
            raise ValueError('unexpected hook error')
        submitted = [e for e in events if e['event'] == 'UserPromptSubmit']
        if [e['input']['prompt'] for e in submitted] != [meta['prompt'], *(['approve'] if day == 'day1' else [])]:
            raise ValueError('unexpected user turns')
        contract_path = folder / 'request-state/contract.json'
        validate(contract_path, 'contract.schema.json')
        context = submitted[0]['output']['hookSpecificOutput']['additionalContext']
        if contract_path.read_text() not in context or not visible(folder / 'request-transcript.jsonl', context):
            raise ValueError('contract absent from context')
        pending = json.loads((folder / 'request-state/session.json').read_text())
        if pending['phase'] != 'awaiting_approval' or json.loads((folder / 'request-state/state.json').read_text())['attempt'] != 0:
            raise ValueError('approval gate missing')
        baseline = json.loads((folder / 'initial-workspace.json').read_text())
        for snapshot in ['request-workspace.json', *(['before-approval-workspace.json'] if day == 'day1' else [])]:
            if json.loads((folder / snapshot).read_text()) != baseline:
                raise ValueError('preapproval task write')
        for stage in stages:
            result = json.loads((folder / f'{stage}-result.json').read_text())
            command = result['command']
            if result['exit_code'] != 0 or command.count('exec') != 1 or ('resume' in command) != (stage == 'approval'):
                raise ValueError('executor launch failed or wrong session routing')
            if stage == 'approval' and command[command.index('resume') + 1] != meta['thread_id']:
                raise ValueError('approval resumed wrong session')
    saved = root / 'day1/approval-state'
    verdict = validate(saved / 'verdict.json', 'verdict.schema.json')
    state = json.loads((saved / 'state.json').read_text())
    session = json.loads((saved / 'session.json').read_text())
    contract = validate(saved / 'contract.json', 'contract.schema.json')
    if (saved / 'contract.json').read_bytes() != (root / 'day1/request-state/contract.json').read_bytes():
        raise ValueError('approved contract changed')
    if session['session_id'] != first['thread_id']:
        raise ValueError('completed session changed')
    if state['attempt'] != 1 or verdict['attempt'] != 1 or first['max_attempts'] != 1:
        raise ValueError('unexpected attempt budget')
    if {i['id'] for i in verdict['items']} != {i['id'] for i in contract['success_criteria']}:
        raise ValueError('verdict criteria mismatch')
    stops = [e for e in records(root / 'day1/hooks.jsonl') if e['event'] == 'Stop']
    if any((e['output'] or {}).get('decision') == 'block' for e in stops):
        raise ValueError('unexpected re-instruction')
    start = records(root / 'day2/hooks.jsonl')[0]
    if start['event'] != 'SessionStart' or start['error'] is not None or second['prompt'] != NEXT:
        raise ValueError('day-2 SessionStart missing')
    if scenario == 'exhaustion':
        if first['prompt'] != EXHAUST or contract['success_criteria'][0]['check'] != {
            'type': 'command', 'command': "python -c 'raise SystemExit(1)'", 'expected': {'exit_code': 0}} or len(contract['success_criteria']) != 1:
            raise ValueError('impossible criterion changed')
        if verdict['overall'] != 'fail' or session['phase'] != 'exhausted':
            raise ValueError('verification did not exhaust')
        unmet = {i['id'] for i in verdict['items'] if i['status'] != 'pass'}
        handoff = validate(saved / 'handoff.json', 'handoff.schema.json')
        if not unmet or not unmet <= {i['criterion_id'] for i in handoff['remaining']}:
            raise ValueError('handoff lost remaining work')
        if not any(all(i in (e['output'] or {}).get('systemMessage', '') for i in unmet) for e in stops):
            raise ValueError('unmet items not shown')
        context = 'HARNESS_HANDOFF\n' + (saved / 'handoff.json').read_text()
        if start['output'] != {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}} or not visible(root / 'day2/request-transcript.jsonl', context):
            raise ValueError('remaining work not injected/visible')
    else:
        if verdict['overall'] != 'pass' or session['phase'] != 'complete':
            raise ValueError('task must pass before injected handoff failure')
        if (root / 'day1/result.txt').read_bytes() != b'ok\n':
            raise ValueError('day-1 task artifact changed')
        faults = records(root / 'faults.jsonl')
        expected = ['-m', 'controller', 'handoff'] if scenario == 'generation' else ['-m', 'verifier', 'validate-handoff']
        if len(faults) != 1 or faults[0]['mode'] != scenario or faults[0]['exit_code'] != 2 or faults[0]['args'][:3] != expected:
            raise ValueError('failure injection not observed')
        if scenario == 'validation' and not list(saved.glob('handoff.pending.*.json')):
            raise ValueError('no generated pending handoff')
        if not any(e['error'] is not None for e in stops):
            raise ValueError('Stop did not observe injected failure')
        for folder in (saved, root / 'day2/request-state'):
            archived = list(folder.glob('handoff.stale.*.json'))
            if (folder / 'handoff.json').exists() or len(archived) != 1 or archived[0].read_bytes() != (root / 'previous-handoff.json').read_bytes():
                raise ValueError('previous context not archived or current remains')
        if start['output'] is not None or any('HARNESS_HANDOFF' in json.dumps(r) for r in records(root / 'day2/request-transcript.jsonl')):
            raise ValueError('stale context injected')
    return {'scenario': scenario, 'new_session': True, 'approval_gates': True,
            'remaining_injected': scenario == 'exhaustion', 'stale_injected': False, 'overall': 'pass'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('day1', 'day2', 'check'))
    parser.add_argument('--scenario', choices=('exhaustion', 'generation', 'validation'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--scripted-approval', action='store_true')
    args = parser.parse_args()
    try:
        root = args.out.resolve()
        if args.stage == 'day1':
            if root.exists():
                raise ValueError('use a fresh evidence directory')
            day_one(root, args.scenario, args.scripted_approval)
        else:
            if demo_metadata(root / 'day1')['scenario'] != args.scenario:
                raise ValueError('scenario changed')
            if args.stage == 'day2':
                day_two(root)
            else:
                print(json.dumps(audit(root), sort_keys=True))
        return 0
    except Exception as exc:
        print(f'handoff demo failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
