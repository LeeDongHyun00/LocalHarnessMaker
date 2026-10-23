"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings as (value, count) pairs in input order.

    Nonadjacent equal values form separate runs. Empty input returns [].
    Preserve the original string values and do not mutate the input collection.
    """
    result: list[tuple[str, int]] = []
    for value in items:
        if result and result[-1][0] == value:
            run_value, count = result[-1]
            result[-1] = (run_value, count + 1)
        else:
            result.append((value, 1))
    return result
