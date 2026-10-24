from __future__ import annotations

PREFIX = 'text-indexing'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
