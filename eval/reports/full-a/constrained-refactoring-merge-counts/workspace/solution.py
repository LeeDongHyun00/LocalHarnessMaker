"""Public task implementation."""


def _merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    result = dict(left)
    for key, value in right.items():
        result[key] = result.get(key, 0) + value
    return result


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return _merge(left, right)


def merge_legacy(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return _merge(left, right)
