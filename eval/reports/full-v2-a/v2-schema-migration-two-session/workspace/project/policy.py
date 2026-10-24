from __future__ import annotations

PREFIX = 'schema-migration'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
