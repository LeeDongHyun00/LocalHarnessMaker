from __future__ import annotations

PREFIX = 'job-queues'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
