"""Preflight and repair an explicitly targeted, project-scoped installation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVENTS = {'SessionStart': 'session_start.py', 'UserPromptSubmit': 'user_prompt_submit.py', 'Stop': 'stop.py'}
REQUIRED = ('controller/__main__.py', 'verifier/__main__.py', 'schemas/contract.schema.json',
            'schemas/verdict.schema.json', 'schemas/handoff.schema.json',
            'plugin/hooks/_runtime.py', 'plugin/hooks/_entrypoint.py', 'plugin/hooks/_scope.py',
            'plugin/hooks/_config.py', 'plugin/hooks/_process.py', 'plugin/skills/harness/SKILL.md',
            'plugin/CODEX_VERSION', *(f'plugin/hooks/{name}' for name in EVENTS.values()))
APP_CODEX = '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'


def resolve_codex() -> str | None:
    """Prefer the explicit executable, then PATH, then the macOS app bundle."""
    for candidate in (os.environ.get('HARNESS_CODEX'), 'codex', APP_CODEX):
        if candidate and (resolved := shutil.which(candidate)):
            return resolved
    return None


def configuration(snapshot: Path) -> dict[str, Any]:
    """Render integer deadlines from validated settings before writing targets."""
    from plugin.hooks._config import validate_settings
    values = validate_settings()
    hooks = json.loads((ROOT / 'plugin/hooks/hooks.json').read_text())
    for event, script in EVENTS.items():
        handler = hooks['hooks'][event][0]['hooks'][0]
        timeout = values[f'HARNESS_{event.upper()}_TIMEOUT']
        handler['timeout'] = timeout
        handler['command'] = shlex.join(['env', f'HARNESS_{event.upper()}_TIMEOUT={timeout}',
                                          sys.executable, str(snapshot / 'plugin/hooks' / script)])
    return hooks


def load_hooks(path: Path) -> dict[str, Any]:
    """Reject malformed existing configuration before any installation writes."""
    value = json.loads(path.read_text()) if path.exists() else {'hooks': {}}
    if not isinstance(value, dict) or not isinstance(value.get('hooks'), dict):
        raise ValueError('malformed hooks.json')
    for groups in value['hooks'].values():
        if not isinstance(groups, list):
            raise ValueError('malformed hook event groups')
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
                raise ValueError('malformed hook group')
            if any(not isinstance(handler, dict) or not isinstance(handler.get('command'), str)
                   for handler in group['hooks']):
                raise ValueError('malformed hook command')
    return value


def script_command(handler: dict[str, Any], script: Path) -> bool:
    """Recognize the actual script operand, independent of Python or env spelling."""
    try:
        parts = shlex.split(handler['command'])
    except (KeyError, ValueError):
        return False
    if parts and parts[0] == 'env':
        parts = parts[1:]
        while parts and '=' in parts[0] and not parts[0].startswith('/'):
            parts = parts[1:]
    return (handler.get('type') == 'command' and len(parts) == 2
            and Path(parts[1]).is_absolute() and Path(parts[1]).resolve() == script.resolve())


def check_install(home: Path, project: Path) -> bool:
    """Check persisted integer budgets and semantic registrations, ignoring caller env."""
    from plugin.hooks._config import integer_timeout
    snapshot = home / 'local-harness-maker'
    valid = True
    try:
        manifest = json.loads((snapshot / 'install.json').read_text())
        if not all((snapshot / name).is_file() for name in REQUIRED):
            raise ValueError('partial runtime snapshot')
        installed = load_hooks(home / 'hooks.json')
        for event, filename in EVENTS.items():
            if type(manifest['timeouts'][event]) is not int:
                raise ValueError(f'{event}: timeout type or value mismatch in manifest')
            expected = integer_timeout(manifest['timeouts'][event], event, 5)
            script = snapshot / 'plugin/hooks' / filename
            matches = [handler for group in installed['hooks'].get(event, []) for handler in group['hooks']
                       if script_command(handler, script)]
            if not script.is_file() or len(matches) != 1:
                raise ValueError('missing or duplicate registration')
            handler = matches[0]
            if type(handler.get('timeout')) is not int:
                raise ValueError(f'{event}: timeout type or value mismatch')
            actual = integer_timeout(handler['timeout'], event, 5)
            if actual != expected:
                raise ValueError(f'{event}: timeout type or value mismatch')
            tokens = shlex.split(handler['command'])
            setting = f'HARNESS_{event.upper()}_TIMEOUT='
            embedded = [part[len(setting):] for part in tokens if part.startswith(setting)]
            if len(embedded) != 1 or integer_timeout(embedded[0], event, 5) != actual:
                raise ValueError(f'{event}: timeout type or value mismatch in runtime budget')
        if tomllib.loads((home / 'config.toml').read_text()).get('features', {}).get('hooks') is not True:
            raise ValueError('feature disabled')
        if not (project / '.local-harness-maker').is_file():
            raise ValueError('project marker missing')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if 'timeout type or value mismatch' in str(exc):
            print(str(exc), file=sys.stderr)
        print('Hooks not registered', file=sys.stderr)
        valid = False
    if not (home / 'skills/harness/SKILL.md').is_file():
        print('Skill missing', file=sys.stderr)
        valid = False
    return valid


def enabled_config(path: Path) -> bytes:
    """Preserve other TOML settings while enabling the hooks feature."""
    text = path.read_text() if path.exists() else ''
    parsed = tomllib.loads(text)
    if parsed.get('features', {}).get('hooks') is True:
        return text.encode()
    if 'features' in parsed and not isinstance(parsed['features'], dict):
        raise ValueError('features must be a TOML table')
    match = re.search(r'(?m)^\[features\]\s*(?:#.*)?$', text)
    if match:
        end_match = re.search(r'(?m)^\s*\[', text[match.end():])
        end = match.end() + end_match.start() if end_match else len(text)
        table = text[match.end():end]
        if re.search(r'(?m)^\s*hooks\s*=', table):
            table = re.sub(r'(?m)^\s*hooks\s*=.*$', '\nhooks = true', table)
        else:
            table = '\nhooks = true\n' + table
        text = text[:match.end()] + table + text[end:]
    elif 'features' not in parsed:
        text += '\n[features]\nhooks = true\n'
    else:
        raise ValueError('cannot safely enable hooks in inline/dotted features; use [features]')
    if tomllib.loads(text).get('features', {}).get('hooks') is not True:
        raise ValueError('failed to enable hooks')
    return text.encode()


def plan_install(home: Path, project: Path) -> dict[Path, bytes]:
    """Load, validate and serialize every target before creating directories/files."""
    snapshot = home / 'local-harness-maker'
    wanted = configuration(snapshot)
    if not all((ROOT / name).is_file() for name in REQUIRED):
        raise ValueError('source runtime is incomplete')
    existing = load_hooks(home / 'hooks.json')
    for event, filename in EVENTS.items():
        script = snapshot / 'plugin/hooks' / filename
        groups = existing['hooks'].setdefault(event, [])
        # Repair our handlers without deleting unrelated plugins in shared groups.
        kept = []
        for group in groups:
            handlers = [handler for handler in group['hooks'] if not script_command(handler, script)]
            if handlers:
                kept.append({**group, 'hooks': handlers})
        existing['hooks'][event] = [*kept, *wanted['hooks'][event]]
    plan: dict[Path, bytes] = {home / 'config.toml': enabled_config(home / 'config.toml')}
    for name in ('controller', 'verifier', 'schemas', 'plugin/hooks', 'plugin/skills', 'plugin/templates'):
        for source in sorted((ROOT / name).rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc':
                plan[snapshot / source.relative_to(ROOT)] = source.read_bytes()
    plan[snapshot / 'plugin/CODEX_VERSION'] = (ROOT / 'plugin/CODEX_VERSION').read_bytes()
    for source in (ROOT / 'plugin/skills/harness').rglob('*'):
        if source.is_file():
            plan[home / 'skills/harness' / source.relative_to(ROOT / 'plugin/skills/harness')] = source.read_bytes()
    template = (ROOT / 'plugin/templates/AGENTS.md').read_bytes()
    instructions = (project / 'AGENTS.md').read_bytes() if (project / 'AGENTS.md').exists() else b''
    plan[project / 'AGENTS.md'] = instructions if template in instructions else instructions + (b'\n' if instructions else b'') + template
    plan[project / '.local-harness-maker'] = b'LocalHarnessMaker project opt-in v1\n'
    plan[home / 'hooks.json'] = (json.dumps(existing, indent=2) + '\n').encode()
    manifest = {'timeouts': {event: wanted['hooks'][event][0]['hooks'][0]['timeout'] for event in EVENTS}}
    plan[snapshot / 'install.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    for target in plan:
        boundary = home if target.is_relative_to(home) else project
        if not target.resolve().is_relative_to(boundary):
            raise ValueError(f'target symlink escapes installation: {target}')
        for parent in (target, *target.parents):
            if parent == boundary.parent:
                break
            if parent.exists() and (parent.is_dir() if parent == target else not parent.is_dir()):
                raise ValueError(f'invalid installation target: {parent}')
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    home, project = args.codex_home.resolve(), args.project.resolve()
    # Preflight does not run under --check: installed settings are authoritative.
    plan = None if args.check else plan_install(home, project)
    executable = resolve_codex()
    version_ok = False
    if executable is None:
        print('Codex CLI not found', file=sys.stderr)
    else:
        from plugin.hooks._process import run_group
        try:
            result = run_group([executable, '--version'], capture_output=True, text=True, timeout=5,
                               check=False, shell=False, env={**os.environ, 'HARNESS_NESTED': '1'})
            expected = (ROOT / 'plugin/CODEX_VERSION').read_text().strip()
            version_ok = result.returncode == 0 and result.stdout.strip() == expected
            if not version_ok:
                print(f'Codex version mismatch: expected {expected}; found {result.stdout.strip()}', file=sys.stderr)
        except (OSError, TimeoutError) as exc:
            print(f'Codex version probe failed: {exc}', file=sys.stderr)
        except Exception as exc:
            print(f'Codex version probe failed: {exc}', file=sys.stderr)
    if args.check:
        installed_ok = check_install(home, project)
        if version_ok and installed_ok:
            print('LocalHarnessMaker installation OK')
        return 0 if version_ok and installed_ok else 1
    if not version_ok:
        return 1
    assert plan is not None
    from uuid import uuid4
    for target, data in plan.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f'.{target.name}.{uuid4().hex}.tmp')
        temporary.write_bytes(data)
        temporary.replace(target)
    print(f'Installed LocalHarnessMaker: {home / "local-harness-maker"}')
    return 0


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'Installation error: {exc}', file=sys.stderr)
        raise SystemExit(1)
