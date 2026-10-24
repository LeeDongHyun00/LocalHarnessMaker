from __future__ import annotations

PREFIX = 'search-facets'

def normalize(value: str) -> str:
    return value.strip().casefold()
