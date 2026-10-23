"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return all keys with shared counts added, preserving every total."""
    merged = left.copy()
    for key, count in right.items():
        merged[key] = merged.get(key, 0) + count
    return merged


def merge_many(cases: list[tuple]) -> list:
    """Merge each positional argument tuple in order, stopping on any error."""
    return [merge(*case) for case in cases]
