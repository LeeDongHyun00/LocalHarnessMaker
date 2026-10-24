"""Fail-closed, non-generating installed-Codex/model/pricing preflight."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import subprocess
import time
from typing import Any, Callable

from plugin.artifacts import ROOT, confined, digest, read, snapshot, validate, write
from plugin.hooks._process import run_group
from plugin.versions import validate_version, verified_versions

MODEL = 'gpt-6-luna'
PRICES = ROOT / 'controller/prices.yaml'


def inspect_models(codex: str, invoke: Callable[..., Any]) -> tuple[bytes, bool]:
    """Prefer an advertised models subcommand; otherwise use model/list RPC.

    The stdio app-server probe initializes a client and requests model/list only;
    it never creates a thread or invokes a model. Unsupported protocol fails closed.
    """
    help_result = invoke([codex, '--help'])
    if help_result.returncode != 0:
        raise ValueError('Codex help unavailable')
    commands = {line.strip().split()[0] for line in help_result.stdout.splitlines() if line.strip()}
    if 'models' in commands:
        result = invoke([codex, 'models', '--json'])
        if result.returncode != 0:
            raise ValueError('model listing failed')
        data = json.loads(result.stdout)
    else:
        messages = [
            {'id': 1, 'method': 'initialize', 'params': {
                'clientInfo': {'name': 'localharness-pin-check', 'version': '3'}}},
            {'method': 'initialized', 'params': {}},
            {'id': 2, 'method': 'model/list', 'params': {'limit': 100}},
        ]
        result = invoke([codex, 'app-server'], input=''.join(json.dumps(m) + '\n' for m in messages))
        if result.returncode != 0:
            raise ValueError('model/list probe failed')
        replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        initialized = [r for r in replies if r.get('id') == 1 and 'result' in r]
        listings = [r for r in replies if r.get('id') == 2 and 'result' in r]
        if len(initialized) != 1 or len(listings) != 1:
            raise ValueError('model/list response missing or ambiguous')
        data = listings[0]['result']
    rows = data if isinstance(data, list) else data.get('data', data.get('models'))
    if isinstance(data, dict) and data.get('nextCursor'):
        raise ValueError('model listing truncated')
    if not isinstance(rows, list):
        raise ValueError('unsupported model listing')
    identities = []
    for row in rows:
        # Only the provider model identity counts, never displayName or aliases.
        identity = row if isinstance(row, str) else row.get('model', row.get('id'))
        if not isinstance(identity, str):
            raise ValueError('missing model identity')
        identities.append(identity)
    return result.stdout.encode(), identities.count(MODEL) == 1


def check(session_id: str, directory: Path, codex: str, *,
          runner: Callable[..., Any] = run_group, pricing: Path = PRICES,
          budget: float = 5.0) -> dict[str, Any]:
    """Bound the complete probe, retaining exact observed bytes and prices."""
    expected = digest(session_id.encode())
    if (directory.name != expected or directory.parent.name != 'sessions'
            or directory.parent.parent.name != 'v3'
            or directory.parent.parent.parent.name != '.localharness'):
        raise ValueError('artifacts must be the exact v3 native-session directory')
    confined(directory.parents[3], str(directory.relative_to(directory.parents[3])))
    directory.mkdir(parents=True, exist_ok=True)
    confined(directory, 'evidence').mkdir(exist_ok=True)
    deadline = time.monotonic() + budget

    def invoke(command: list[str], **kwargs: Any) -> Any:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('pin-check budget exhausted')
        return runner(command, shell=False, text=True, capture_output=True, check=False,
                      timeout=remaining, env={**os.environ, 'HARNESS_NESTED': '1'}, **kwargs)

    version = None
    reasons: list[str] = []
    checks = {'codex_version_verified': False, 'model_listed': False, 'pricing_covered': False}
    model_ref = price_ref = None
    pricing_ref = None
    try:
        result = invoke([codex, '--version'])
        if result.returncode == 0:
            version = validate_version(result.stdout.strip())
            checks['codex_version_verified'] = version in verified_versions()
    except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired):
        pass
    if not checks['codex_version_verified']:
        reasons.append('codex_version_unverified')
    try:
        model_bytes, checks['model_listed'] = inspect_models(codex, invoke)
        model_ref = snapshot(directory, 'models.txt', model_bytes)
        if not checks['model_listed']:
            reasons.append('model_missing')
    except (OSError, ValueError, TypeError, AttributeError, TimeoutError, subprocess.TimeoutExpired):
        reasons.append('model_list_unavailable')
    try:
        raw = pricing.read_bytes()
        book = json.loads(raw)
        prices = book['models'][MODEL]
        for key in ('input_per_million', 'cached_input_per_million', 'output_per_million'):
            value = Decimal(str(prices[key]))
            if not value.is_finite() or value < 0:
                raise ValueError('invalid price')
        if not book['source'] or not book['checked_on']:
            raise ValueError('missing price provenance')
        price_ref = snapshot(directory, 'prices.json', raw)
        pricing_ref = f'controller/prices.yaml@{book["checked_on"]}#{MODEL}:sha256:{digest(raw)}'
        checks['pricing_covered'] = True
    except (OSError, ValueError, KeyError, TypeError, ArithmeticError):
        reasons.append('pricing_missing')
    enabled = all(checks.values())
    advisory = ('Pinned gpt-6-luna low-effort hooks enabled; live compatibility remains separately measured.'
                if enabled else 'Luna hooks disabled: ' + ', '.join(reasons) +
                '. Continue ordinary work; this session cannot be represented as H3. No model substitution.')
    value = {'schema_version': 3, 'session_id': session_id,
             'checked_at': datetime.now(timezone.utc).isoformat(),
             'status': 'enabled' if enabled else 'disabled', 'requested_model': MODEL,
             'codex_version': version, 'checks': checks, 'model_list': model_ref,
             'pricing_snapshot': price_ref, 'pricing_ref': pricing_ref,
             'reason_codes': reasons, 'advisory': advisory}
    validate(value, 'pin-check.schema.json')
    write(confined(directory, 'pin-check.json'), value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--codex', required=True)
    args = parser.parse_args()
    try:
        value = check(args.session_id, args.artifacts.absolute(), args.codex)
        print(value['advisory'])
        return 0 if value['status'] == 'enabled' else 1
    except Exception as exc:
        print(f'Pin-check internal error: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
