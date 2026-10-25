"""Read the history of Codex versions with passing compatibility evidence."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re
import os
import shutil
from typing import Any, Callable

REGISTRY = Path(__file__).with_name('VERIFIED_VERSIONS.json')


def cli_version(*, runner: Callable[..., Any], timeout: float) -> str:
    """Probe the current CLI using the installer's discovery order, without models."""
    bundle = '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
    executable = next((found for candidate in (os.environ.get('HARNESS_CODEX'), 'codex', bundle)
                       if candidate and (found := shutil.which(candidate))), None)
    if executable is None or timeout <= 0:
        raise ValueError('CLI unavailable or version probe budget exhausted')
    result = runner([executable, '--version'], shell=False, capture_output=True, text=True,
                    check=False, timeout=min(1.0, timeout), env={**os.environ, 'HARNESS_NESTED': '1'})
    if result.returncode != 0:
        raise ValueError('CLI version probe failed')
    return validate_version(result.stdout.strip())


def validate_version(value: object) -> str:
    """Require a complete CLI version identity rather than empty/error output."""
    if not isinstance(value, str) or not re.fullmatch(r'codex-cli [0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', value):
        raise ValueError(f'invalid Codex version: {value!r}')
    return value


def verified_versions(path: Path = REGISTRY) -> dict[str, list[str]]:
    """Reject duplicate versions and evidence paths outside plugin/evidence."""
    rows = json.loads(path.read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('verified versions must be a nonempty list')
    result: dict[str, list[str]] = {}
    for row in rows:
        if (not isinstance(row, dict) or not {'version', 'evidence'} <= set(row)
                or set(row) - {'version', 'evidence', 'luna_observation'}):
            raise ValueError('verified version requires version and evidence')
        version = validate_version(row['version'])
        evidence = row['evidence']
        if version in result or not isinstance(evidence, list) or not evidence:
            raise ValueError('duplicate version or missing evidence')
        for directory in evidence:
            if (not isinstance(directory, str) or len(Path(directory).parts) < 2
                    or Path(directory).parts[0] != 'evidence' or '..' in Path(directory).parts):
                raise ValueError('evidence must name a directory inside plugin/evidence')
        result[version] = evidence
    return result


def luna_observation(version: str | None, path: Path = REGISTRY) -> dict[str, Any] | None:
    """Return only a complete, well-formed observation for the exact CLI version."""
    try:
        verified_versions(path)
        row = next(row for row in json.loads(path.read_text()) if row['version'] == version)
        value = row.get('luna_observation')
        fields = {'model', 'service_tier', 'observed_at', 'thread_id', 'evidence_sha256'}
        if not isinstance(value, dict) or set(value) != fields:
            return None
        if not isinstance(value['model'], str):
            return None
        if any(value[key] is not None and not isinstance(value[key], str)
               for key in ('service_tier', 'thread_id')):
            return None
        timestamp = value['observed_at']
        if (not isinstance(timestamp, str) or not re.fullmatch(
                r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})', timestamp)
                or datetime.fromisoformat(timestamp.upper().replace('Z', '+00:00')).tzinfo is None):
            return None
        sha = value['evidence_sha256']
        if sha is not None and (not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha)):
            return None
        return dict(value)
    except (OSError, ValueError, TypeError, KeyError, StopIteration):
        return None
