from __future__ import annotations

PREFIX = 'cache-invalidation'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
