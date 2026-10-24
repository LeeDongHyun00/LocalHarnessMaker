from __future__ import annotations

PREFIX = 'workflow-state'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
