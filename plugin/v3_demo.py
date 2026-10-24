"""Prepare two interactive host sessions and audit their retained v3 evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
from typing import Any, Callable

from plugin.artifacts import ROOT, confined, digest, read, validate, verify_reference, write
from plugin.hooks._process import run_group
from plugin.install import resolve_codex

FIRST = ('Create result.txt containing the release label and a newline. The release label is unspecified; '
         'ask me which label before changing any file. Show the numbered requirements table first. '
         'After my explicit answer, implement the file and report evidence. Record the exact label '
         'as a fixed constant in your final decision ledger. Do not create other application files.')
SECOND = ('Use the previous validated decision ledger to create followup.txt containing the exact same '
          'release label and a newline. Do not ask me to repeat the label. Show the requirements table '
          'and report evidence for followup.txt.')


def scripts(metadata: dict[str, Any]) -> dict[str, str]:
    """No secrets are serialized; login remains a symlink to the user's existing auth."""
    out = Path(metadata['out'])
    environment = ['env', '-u', 'HARNESS_NESTED', '-u', 'HARNESS_STUB',
                   'HARNESS_INTERFACE_VERSION=3', f'HOME={metadata["home"]}',
                   f'CODEX_HOME={metadata["codex_home"]}', f'HARNESS_PYTHON={metadata["python"]}',
                   f'HARNESS_CODEX={metadata["codex"]}', f'HARNESS_EVENT_LOG={out / "hooks.jsonl"}']
    result = {}
    for number, prompt in ((1, FIRST), (2, SECOND)):
        command = [*environment, metadata['codex'], '--no-daemon', '--no-alt-screen',
                   '-s', 'workspace-write', '-C', metadata['workspace'], '-m', 'gpt-6.1-sol',
                   '-c', 'model_reasoning_effort="medium"', prompt]
        # script retains actual interactive trust, questions, answers and output.
        result[f'session{number}.sh'] = '#!/bin/sh\nexec ' + shlex.join(
            ['/usr/bin/script', '-q', str(out / f'session{number}.terminal'), *command]) + '\n'
    return result


def prepare(out: Path, *, runner: Callable[..., Any] = run_group) -> None:
    if out.exists():
        raise ValueError('use a fresh output directory outside the repository')
    if out.is_relative_to(ROOT):
        raise ValueError('host captures must be outside the repository and evaluation sets')
    executable = resolve_codex()
    if not executable:
        raise ValueError('installed Codex not found')
    # Help-only checks catch missing concurrent-role operations without model calls.
    for module, operations in (('controller', ('requirements', 'claim-audit')),
                               ('verifier', ('ledger-validate',))):
        result = runner([sys.executable, '-m', module, '--help'], cwd=ROOT, shell=False,
                        capture_output=True, text=True, check=False, timeout=5,
                        env={**os.environ, 'HARNESS_NESTED': '1'})
        if result.returncode or any(operation not in result.stdout for operation in operations):
            raise ValueError(f'{module} v3 operations not integrated; merge Roles 3/4 before live demo')
    out.mkdir(parents=True)
    temporary = Path(tempfile.mkdtemp(prefix='lhm-v3-host-'))
    home, codex_home, workspace = temporary / 'home', temporary / 'codex-home', temporary / 'project'
    for directory in (home, codex_home, workspace):
        directory.mkdir()
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if auth.is_file():
        (codex_home / 'auth.json').symlink_to(auth)
    env = {**os.environ, 'HARNESS_CODEX': executable, 'HARNESS_PYTHON': sys.executable}
    result = runner([sys.executable, '-m', 'plugin.install', '--codex-home', str(codex_home),
                     '--project', str(workspace)], cwd=ROOT, env=env, shell=False,
                    capture_output=True, text=True, check=False, timeout=30)
    (out / 'install.stdout').write_text(result.stdout)
    (out / 'install.stderr').write_text(result.stderr)
    if result.returncode:
        raise ValueError('isolated installation failed; inspect retained streams')
    metadata = {'out': str(out), 'home': str(home), 'codex_home': str(codex_home),
                'workspace': str(workspace), 'codex': executable, 'python': sys.executable}
    write(out / 'experiment.json', metadata)
    for name, content in scripts(metadata).items():
        (out / name).write_text(content)
    print(f'bash {shlex.quote(str(out / "session1.sh"))}')
    print('Accept hook trust interactively. At the question pause, answer using the exact question ID:')
    print('{"answers":{"Q-1":"choose-a-unique-release-label"}}')
    print('Wait for the completion report and ledger continuation to finish, then exit Codex.')
    print(f'bash {shlex.quote(str(out / "session2.sh"))}')
    print('Verify SessionStart shows HARNESS_LEDGER without repeating the label, then complete and exit.')
    print(f'{shlex.quote(sys.executable)} -m plugin.host_checks v3-check --out {shlex.quote(str(out))}')


def check(out: Path) -> dict[str, Any]:
    """Read-only capture audit. It never invokes Codex, controllers or validators."""
    metadata = read(out / 'experiment.json')
    workspace = Path(metadata['workspace'])
    root = confined(workspace, '.localharness/v3')
    directories = sorted(confined(root, 'sessions').iterdir(),
                         key=lambda p: read(confined(p, 'pin-check.json'))['checked_at'])
    if len(directories) != 2:
        raise ValueError('expected exactly two distinct native sessions')
    first_id = None
    for directory in directories:
        pin = read(confined(directory, 'pin-check.json'))
        validate(pin, 'pin-check.schema.json')
        if pin['status'] != 'enabled' or digest(pin['session_id'].encode()) != directory.name:
            raise ValueError('disabled pin or invalid native session directory')
        for key in ('model_list', 'pricing_snapshot'):
            verify_reference(directory, pin[key])
        if first_id is None:
            first_id = pin['session_id']
        for name, schema in (('requirements', 'requirements'), ('completion-report', 'completion-report'), ('ledger', 'ledger')):
            value = read(confined(directory, name + '.json'))
            validate(value, schema + '.schema.json')
            if value['session_id'] != pin['session_id']:
                raise ValueError('artifact session identity mismatch')
        requirements = read(directory / 'requirements.json')
        verify_reference(directory, requirements['prompt'])
        if requirements['state'] != 'ready':
            raise ValueError('requirements never became ready')
        report = read(directory / 'completion-report.json')
        verify_reference(directory, report['requirements'])
        if not report['current_final_message']:
            raise ValueError('missing retained final message')
        verify_reference(directory, report['current_final_message'])
        if any(row['status'] == 'fail' for row in report['items']):
            raise ValueError('demo retains a deterministic failure')
        for row in report['items']:
            for evidence in row['evidence']:
                verify_reference(directory, evidence)
        ledger = read(directory / 'ledger.json')
        verify_reference(directory, ledger['requirements'])
        if not ledger['validation'] or ledger['validation']['status'] != 'valid':
            raise ValueError('ledger was not mechanically validated')
        calls = [json.loads(line) for line in confined(directory, 'luna-calls.jsonl').read_text().splitlines()]
        if len(calls) != 2 or {c['phase'] for c in calls} != {'requirements', 'claim_audit'}:
            raise ValueError('missing/duplicate Luna calls')
        for call in calls:
            validate(call, 'luna-call.schema.json')
            if (call['session_id'] != pin['session_id'] or call['model'] != 'gpt-6-luna'
                    or call['status'] != 'success' or call['pricing_ref'] != pin['pricing_ref']):
                raise ValueError('invalid Luna identity/accounting')
    first = read(directories[0] / 'requirements.json')
    if not first['open_questions'] or any(q['answer'] is None for q in first['open_questions']):
        raise ValueError('missing question/explicit-answer demonstration')
    latest = read(confined(root, 'latest-ledger.json'))
    if latest != read(directories[1] / 'ledger.json'):
        raise ValueError('latest ledger does not match second session')
    events = [json.loads(line) for line in (out / 'hooks.jsonl').read_text().splitlines()]
    contexts = [(e, e.get('output', {}).get('hookSpecificOutput', {}).get('additionalContext', ''))
                for e in events if isinstance(e.get('output'), dict)]
    if not any(e['input']['session_id'] == first_id and 'END THIS TURN' in text for e, text in contexts):
        raise ValueError('question-pause context not observed')
    if not any(e['input']['session_id'] != first_id and 'HARNESS_LEDGER' in text
               and first_id in text for e, text in contexts):
        raise ValueError('second SessionStart ledger injection not observed')
    label = confined(workspace, 'result.txt').read_bytes()
    if not label.strip() or label != confined(workspace, 'followup.txt').read_bytes():
        raise ValueError('release label not preserved across sessions')
    for name in ('session1.terminal', 'session2.terminal'):
        if not (out / name).is_file() or not (out / name).stat().st_size:
            raise ValueError('missing terminal capture')
    return {'overall': 'pass', 'native_sessions': 2, 'question_pause_observed': True,
            'ledger_injection_observed': True, 'live_timing_acceptance': 'separate host measurement required'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check'))
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.out.resolve())
        else:
            print(json.dumps(check(args.out.resolve())))
        return 0
    except Exception as exc:
        print(f'V3 demo unavailable: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
