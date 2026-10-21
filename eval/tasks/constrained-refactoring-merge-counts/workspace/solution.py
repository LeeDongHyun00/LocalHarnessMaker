"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    result = dict(left)
    for key, value in right.items(): result[key] = result.get(key, 0) + value
    return result


def merge_legacy(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    result = dict(left)
    for key, value in right.items(): result[key] = result.get(key, 0) + value
    return result
