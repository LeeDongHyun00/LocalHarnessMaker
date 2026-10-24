from __future__ import annotations

PREFIX = 'command-dispatch'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
