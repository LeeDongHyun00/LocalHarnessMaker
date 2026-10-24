from __future__ import annotations

PREFIX = 'document-patches'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
