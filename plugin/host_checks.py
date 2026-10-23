"""Isolated host captures and offline audits for installation lifecycle checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile
from typing import Any, Callable

from plugin import install
from plugin.hooks._process import run_group
from plugin.versions import validate_version

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ('trust', 'bundle', 'silence')
PROMPT = 'Reply HOST_CHECK_OK. Do not use tools or change files. If a harness contract appears, summarize it and wait for approval.'


def write(path: Path, value: Any) -> None:
    """Write evidence as UTF-8 JSON."""
    path.write_text(json.dumps(value, indent=2) + '\n')


def read(path: Path) -> Any:
    """Read retained JSON evidence."""
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    """Hash exact file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment(metadata: dict[str, Any]) -> dict[str, str]:
    """Keep credentials in their existing login, clearing inherited harness overrides."""
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('HARNESS_', 'CODEX_'))}
    env.update(HOME=metadata['home'], CODEX_HOME=metadata['codex_home'],
               HARNESS_CODEX=metadata['codex'], HARNESS_STUB='1',
               PYTHONDONTWRITEBYTECODE='1')
    return env


def capture(command: list[str], out: Path, name: str, *, env: dict[str, str],
            runner: Callable[..., Any] = run_group, timeout: int = 180) -> Any:
    """Retain command, exit status and unmodified streams; never use a shell."""
    result = runner(command, env=env, cwd=ROOT, shell=False, text=True,
                    capture_output=True, timeout=timeout, check=False)
    (out / f'{name}.stdout').write_text(result.stdout)
    (out / f'{name}.stderr').write_text(result.stderr)
    write(out / f'{name}.json', {'command': command, 'returncode': result.returncode,
                               'path': env.get('PATH'), 'codex_override': env.get('HARNESS_CODEX')})
    if result.returncode != 0:
        raise ValueError(f'{name} failed; inspect retained streams')
    return result


def prepare(out: Path, scenario: str, *, runner: Callable[..., Any] = run_group) -> None:
    """Prepare temporary installation and explicit host commands, never real config."""
    if out.exists():
        raise ValueError('use a fresh evidence directory')
    executable = install.APP_CODEX if scenario == 'bundle' else install.resolve_codex()
    if executable is None:
        raise ValueError('Codex not found')
    out.mkdir(parents=True)
    temporary = Path(tempfile.mkdtemp(prefix='lhm-host-check-'))
    home, codex_home, project = temporary / 'home', temporary / 'codex-home', temporary / 'project'
    home.mkdir()
    codex_home.mkdir()
    project.mkdir()
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if auth.is_file():
        (codex_home / 'auth.json').symlink_to(auth)
    metadata = {'scenario': scenario, 'home': str(home), 'codex_home': str(codex_home),
                'project': str(project), 'codex': executable, 'out': str(out), 'python': sys.executable}
    write(out / 'experiment.json', metadata)
    env = environment(metadata)
    result = capture([executable, '--version'], out, 'version-before', env=env, runner=runner)
    validate_version(result.stdout.strip())
    if scenario == 'bundle':
        # No PATH entries and no explicit override: only the real app bundle can resolve.
        env['PATH'] = ''
        env.pop('HARNESS_CODEX')
        capture([sys.executable, '-c', 'from plugin.install import resolve_codex; print(resolve_codex())'],
                out, 'discovery', env=env, runner=runner)
    capture([sys.executable, '-m', 'plugin.install', '--codex-home', str(codex_home),
             '--project', str(project)], out, 'install', env=env, runner=runner)
    if scenario == 'bundle':
        write(out / 'installed.json', {'hooks': read(codex_home / 'hooks.json'),
                                      'manifest': read(codex_home / 'local-harness-maker/install.json'),
                                      'marker': (project / '.local-harness-maker').is_file(),
                                      'skill': (codex_home / 'skills/harness/SKILL.md').is_file()})
        return
    # Wrappers preserve each production hook's exact stdout/stderr, including silence.
    records = out / 'hooks'
    records.mkdir()
    (out / 'wrappers').mkdir()
    hooks = read(codex_home / 'hooks.json')
    for event, filename in install.EVENTS.items():
        wrapper = out / 'wrappers' / f'record-{event}.py'
        target = codex_home / 'local-harness-maker/plugin/hooks' / filename
        wrapper.write_text(
            'import json, pathlib, subprocess, sys, uuid\n'
            'data = sys.stdin.buffer.read()\n'
            f'p = subprocess.run([{sys.executable!r}, {str(target)!r}], input=data, capture_output=True, timeout=675)\n'
            f'root = pathlib.Path({str(records)!r})\n'
            'record = {"input": json.loads(data), "stdout": p.stdout.decode(), "stderr": p.stderr.decode(), "returncode": p.returncode}\n'
            '(root / (uuid.uuid4().hex + ".json")).write_text(json.dumps(record))\n'
            'sys.stdout.buffer.write(p.stdout)\nsys.stderr.buffer.write(p.stderr)\nsys.exit(p.returncode)\n')
        hooks['hooks'][event][0]['hooks'][0]['command'] = shlex.join([sys.executable, str(wrapper)])
    write(codex_home / 'hooks.json', hooks)
    write(out / 'hooks.json', hooks)
    # Installation opts in project; silence uses a fresh sibling, never removes a marker.
    workspace = project if scenario == 'trust' else temporary / 'unrelated-project'
    workspace.mkdir(exist_ok=True)
    metadata['workspace'] = str(workspace)
    write(out / 'experiment.json', metadata)
    config = codex_home / 'config.toml'
    with config.open('a') as stream:
        stream.write('\n[projects.' + json.dumps(str(workspace)) + ']\ntrust_level = "trusted"\n')
    # Only project trust is seeded. Hook trust must be accepted in this interactive run.
    base = [executable, '--no-daemon', '--no-alt-screen', '-s', 'read-only', '-C', str(workspace),
            '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="low"', PROMPT]
    launch = ['env', '-i', *[f'{key}={value}' for key, value in env.items()
              if key in {'HOME', 'CODEX_HOME', 'HARNESS_CODEX', 'HARNESS_STUB', 'PYTHONDONTWRITEBYTECODE',
                         'PATH', 'TERM', 'LANG', 'TMPDIR'}], *base]
    # macOS script records the real trust interaction; no hook-trust bypass is used.
    (out / 'first-session.sh').write_text('#!/bin/sh\nexec /usr/bin/script -q '
                                         + shlex.join([str(out / 'first-session.terminal'), *launch]) + '\n')
    write(out / 'first-command.json', base)
    write(out / 'before.json', workspace_snapshot(workspace))
    print(f'bash {shlex.quote(str(out / "first-session.sh"))}')


def workspace_snapshot(workspace: Path) -> dict[str, Any]:
    """Record marker ancestry and all harness paths; no private files are read."""
    return {'markers': [str(parent / '.local-harness-maker') for parent in (workspace, *workspace.parents)
                        if (parent / '.local-harness-maker').exists()],
            'harness_paths': sorted(str(path.relative_to(workspace)) for path in workspace.rglob('*')
                                    if '.harness' in path.relative_to(workspace).parts)}


def run_second(out: Path, *, runner: Callable[..., Any] = run_group) -> None:
    """Launch a fresh exec session using only persisted trust from the interactive run."""
    metadata = read(out / 'experiment.json')
    if metadata['scenario'] == 'bundle' or (out / 'second.json').exists():
        raise ValueError('second session requires trust/silence and fresh evidence')
    if not (out / 'first-session.terminal').is_file() or not list((out / 'hooks').glob('*.json')):
        raise ValueError('complete the interactive first session before continuing')
    home = Path(metadata['codex_home'])
    if (home / 'hooks.json').read_bytes() != (out / 'hooks.json').read_bytes():
        raise ValueError('hook commands changed after trust establishment')
    first_records = {path.name: digest(path) for path in (out / 'hooks').glob('*.json')}
    write(out / 'first-records.json', first_records)
    write(out / 'wrapper-hashes.json', {path.name: digest(path) for path in (out / 'wrappers').glob('*.py')})
    # Retain only trust/settings, never auth.json.
    shutil.copyfile(home / 'config.toml', out / 'config-after-first.toml')
    command = [metadata['codex'], '--no-daemon', 'exec', '-s', 'read-only', '--skip-git-repo-check', '--json',
               '--color', 'never', '-C', metadata['workspace'], '-m', 'gpt-6.1-sol',
               '-c', 'model_reasoning_effort="low"', PROMPT]
    env = environment(metadata)
    capture(command, out, 'second', env=env, runner=runner)
    shutil.copyfile(home / 'hooks.json', out / 'hooks-after-second.json')
    if (home / 'hooks.json').read_bytes() != (out / 'hooks.json').read_bytes():
        raise ValueError('hook commands changed during second session')
    shutil.copyfile(home / 'config.toml', out / 'config-after-second.toml')
    write(out / 'after.json', workspace_snapshot(Path(metadata['workspace'])))
    capture([metadata['codex'], '--version'], out, 'version-after', env=env, runner=runner)


def check(out: Path) -> dict[str, Any]:
    """Reject incomplete/contradictory captures without launching any executable."""
    metadata = read(out / 'experiment.json')
    scenario = metadata['scenario']
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
    version = validate_version((out / 'version-before.stdout').read_text().strip())
    require(read(out / 'version-before.json')['returncode'] == 0, 'version probe failed')
    require(read(out / 'install.json')['returncode'] == 0, 'installation failed')
    if scenario == 'bundle':
        launch = read(out / 'install.json')
        require(launch['path'] == '' and launch['codex_override'] is None, 'discovery was overridden')
        discovery = read(out / 'discovery.json')
        require(discovery['returncode'] == 0 and discovery['path'] == ''
                and discovery['codex_override'] is None, 'invalid discovery environment')
        require((out / 'discovery.stdout').read_text().strip() == install.APP_CODEX, 'bundle not discovered')
        require(metadata['codex'] == install.APP_CODEX, 'capture was not made on a bundle-only host')
        installed = read(out / 'installed.json')
        require(installed['marker'] and installed['skill'], 'installation incomplete')
        require(set(installed['manifest']['timeouts']) == set(install.EVENTS), 'missing manifest events')
        require(set(installed['hooks']['hooks']) >= set(install.EVENTS), 'missing registered hooks')
    else:
        require(read(out / 'second.json')['returncode'] == 0, 'second session failed')
        require((out / 'first-session.terminal').stat().st_size > 0, 'missing interactive transcript')
        require((out / 'version-after.stdout').read_text().strip() == version, 'CLI version drift')
        require(read(out / 'version-after.json')['returncode'] == 0, 'final version probe failed')
        first_command = read(out / 'first-command.json')
        second_command = read(out / 'second.json')['command']
        suffix = ['-C', metadata['workspace'], '-m', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="low"', PROMPT]
        require(first_command == [metadata['codex'], '--no-daemon', '--no-alt-screen', '-s', 'read-only', *suffix],
                'unexpected first launch or trust bypass')
        require(second_command == [metadata['codex'], '--no-daemon', 'exec', '-s', 'read-only',
                                   '--skip-git-repo-check', '--json', '--color', 'never', *suffix],
                'unexpected second launch, resume or trust bypass')
        require((out / 'hooks-after-second.json').read_bytes() == (out / 'hooks.json').read_bytes(),
                'hook commands changed')
        wrappers = read(out / 'wrapper-hashes.json')
        require(set(wrappers) == {f'record-{event}.py' for event in install.EVENTS}, 'missing wrapper source')
        for name, expected in wrappers.items():
            require(digest(out / 'wrappers' / name) == expected, 'wrapper source changed')
        require((out / 'config-after-first.toml').read_bytes() == (out / 'config-after-second.toml').read_bytes(),
                'configuration changed in second session')
        first = read(out / 'first-records.json')
        require(bool(first), 'missing first hook captures')
        for name, expected in first.items():
            require(digest(out / 'hooks' / name) == expected, 'first hook capture changed')
        records = [(path.name, read(path)) for path in (out / 'hooks').glob('*.json')]
        groups = [[record for name, record in records if (name in first) == is_first] for is_first in (True, False)]
        sessions = []
        for group in groups:
            require({record['input']['hook_event_name'] for record in group} >= set(install.EVENTS),
                    'missing lifecycle hook invocation')
            ids = {record['input']['session_id'] for record in group}
            require(len(ids) == 1, 'capture must contain exactly one session per stage')
            sessions.append(ids)
            for record in group:
                require(record['returncode'] == 0 and record['input']['cwd'] == metadata['workspace'],
                        'hook failed or wrong workspace')
                if scenario == 'silence':
                    require(record['stdout'] == record['stderr'] == '', 'unrelated hook was not silent')
                elif record['input']['hook_event_name'] == 'UserPromptSubmit':
                    require('HARNESS_CONTRACT' in record['stdout'], 'production hook did not inject contract')
        require(sessions[0].isdisjoint(sessions[1]), 'second run reused session')
        if scenario == 'silence':
            for name in ('before.json', 'after.json'):
                snapshot = read(out / name)
                require(snapshot == {'markers': [], 'harness_paths': []}, 'unrelated project has marker or harness')
        # A complete JSON stream is retained as independent evidence of the second executor run.
        events = [json.loads(line) for line in (out / 'second.stdout').read_text().splitlines() if line.strip()]
        require({event.get('thread_id') for event in events if event.get('type') == 'thread.started'} == sessions[1],
                'missing or mismatched executor thread')
        require(any(event.get('type') == 'turn.completed' for event in events), 'incomplete executor stream')
    return {'scenario': scenario, 'version': version, 'overall': 'pass',
            'limitation': 'Observed retained evidence; no claim of read isolation or absence of transient writes.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'second', 'check'))
    parser.add_argument('--scenario', choices=SCENARIOS)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    try:
        if args.action == 'prepare':
            if args.scenario is None:
                raise ValueError('--scenario is required for prepare')
            prepare(out, args.scenario)
        elif args.action == 'second':
            run_second(out)
        else:
            result = check(out)
            write(out / 'audit.json', result)
            print(json.dumps(result))
        return 0
    except Exception as exc:
        if args.action == 'check' and out.is_dir():
            write(out / 'audit.json', {'overall': 'fail', 'reason': str(exc)})
        print(f'Host check failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
