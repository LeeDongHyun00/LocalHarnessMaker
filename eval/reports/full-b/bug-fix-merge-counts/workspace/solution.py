"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    merged = left.copy()
    for key, count in right.items():
        merged[key] = merged.get(key, 0) + count
    return merged
