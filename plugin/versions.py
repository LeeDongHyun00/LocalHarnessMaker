"""Read the history of Codex versions with passing compatibility evidence."""
from __future__ import annotations

import json
from pathlib import Path
import re

REGISTRY = Path(__file__).with_name('VERIFIED_VERSIONS.json')


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
        if not isinstance(row, dict) or set(row) != {'version', 'evidence'}:
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
