from __future__ import annotations

PREFIX = 'dependency-graph'

def normalize(value: str) -> str:
    return value.strip().casefold()
