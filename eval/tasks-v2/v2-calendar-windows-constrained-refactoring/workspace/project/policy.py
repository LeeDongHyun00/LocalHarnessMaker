from __future__ import annotations

PREFIX = 'calendar-windows'

def normalize(value: str) -> str:
    return value.strip().casefold()
