"""Compare recorded POSIX paths without consulting the checking host."""
from __future__ import annotations

import posixpath


def recorded_path(value: str) -> str:
    """Normalize lexical paths and known macOS aliases; keep placeholders exact."""
    if '${' in value:
        return value
    normalized = posixpath.normpath(value)
    for alias in ('var', 'tmp', 'etc'):
        prefix = f'/private/{alias}'
        if normalized == prefix or normalized.startswith(prefix + '/'):
            return normalized[len('/private'):]
    return normalized


def recorded_path_aliases(value: str) -> set[str]:
    """Return recorded spelling plus portable spellings for export prefixes."""
    canonical = recorded_path(value)
    aliases = {value, canonical}
    if '${' not in value:
        for root in ('/var', '/tmp', '/etc'):
            if canonical == root or canonical.startswith(root + '/'):
                aliases.add('/private' + canonical)
    return aliases
