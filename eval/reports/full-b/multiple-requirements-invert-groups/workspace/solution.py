"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group input keys by their values without modifying the input dictionary.

    Original values become dictionary keys, each mapping to a list of input
    keys in dictionary insertion order. Groups follow the order in which
    their values first appear. Empty input returns {}.
    """
    groups: dict[str, list[str]] = {}
    for key, value in items.items():
        groups.setdefault(value, []).append(key)
    return groups
