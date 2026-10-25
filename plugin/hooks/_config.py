"""Plugin deadlines, validated before installing or writing demo files."""
from __future__ import annotations
import os
import re

OUTER = {'SessionStart': 10, 'UserPromptSubmit': 60, 'Stop': 660}
CALLS = {('controller', 'contract'): ('CONTRACT', 30),
         ('verifier', 'check'): ('VERIFY', 480),
         ('controller', 'handoff'): ('HANDOFF', 120),
         ('verifier', 'validate-handoff'): ('VALIDATE', 5)}


def integer_timeout(value: object, name: str, minimum: int = 1) -> int:
    """Use integer seconds, bounded by one day; reject JSON booleans and floats."""
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
        number = int(value)
    else:
        raise ValueError(f'{name}: timeout type or value mismatch (integer seconds required)')
    if not minimum <= number <= 86400:
        raise ValueError(f'{name}: timeout type or value mismatch (range {minimum}..86400)')
    return number


def seconds(name: str, default: int) -> int:
    """Read a bounded integer deadline override."""
    minimum = 5 if name in {f'HARNESS_{event.upper()}_TIMEOUT' for event in OUTER} else 1
    return integer_timeout(os.environ.get(name, str(default)), name, minimum)


def validate_settings() -> dict[str, int]:
    """Preflight every setting, including ones used only after approval."""
    values = {f'HARNESS_{event.upper()}_TIMEOUT': seconds(f'HARNESS_{event.upper()}_TIMEOUT', default)
              for event, default in OUTER.items()}
    values.update({f'HARNESS_{name}_TIMEOUT': seconds(f'HARNESS_{name}_TIMEOUT', default)
                   for name, default in CALLS.values()})
    integer_timeout(os.environ.get('HARNESS_MAX_ATTEMPTS', '3'), 'HARNESS_MAX_ATTEMPTS')
    return values
