"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result
