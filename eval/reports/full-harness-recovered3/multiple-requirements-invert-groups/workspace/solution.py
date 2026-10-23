"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group input keys by their values without changing the input dictionary.

    Each resulting list of keys follows dictionary insertion order. Values are
    preserved as group keys, in order of first appearance. Empty input returns
    {}.
    """
    groups: dict[str, list[str]] = {}
    for key, value in items.items():
        groups.setdefault(value, []).append(key)
    return groups
