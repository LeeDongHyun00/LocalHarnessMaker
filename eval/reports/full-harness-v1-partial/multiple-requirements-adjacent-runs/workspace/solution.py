"""Public specification for runs(items: list[str]) -> list[tuple[str, int]].

Run-length encode adjacent equal strings as (value, count) pairs, preserving
the exact input string values and collection order. Nonadjacent equal values
form separate runs. Empty input returns []. Do not mutate input collections.
The public API retains type hints; no algorithmic complexity constraint applies.
"""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings as (value, count) pairs in input order.

    Preserve string values exactly and keep nonadjacent equal values in
    separate runs. Return [] for empty input without mutating the input list.
    """
    result: list[tuple[str, int]] = []
    for value in items:
        if result and result[-1][0] == value:
            previous_value, count = result[-1]
            result[-1] = (previous_value, count + 1)
        else:
            result.append((value, 1))
    return result
