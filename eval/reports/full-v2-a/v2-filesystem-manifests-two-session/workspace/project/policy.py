from __future__ import annotations

PREFIX = 'filesystem-manifests'

def normalize(value: str) -> str:
    return value.strip().casefold().replace('_', '-')
