"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings as ``(value, count)`` pairs.

    Preserve the original string values and the order of runs. Nonadjacent
    equal values form separate runs. Empty input returns an empty list.
    The input collection is not mutated.
    """
    result: list[tuple[str, int]] = []
    for value in items:
        if result and result[-1][0] == value:
            previous_value, count = result[-1]
            result[-1] = (previous_value, count + 1)
        else:
            result.append((value, 1))
    return result
