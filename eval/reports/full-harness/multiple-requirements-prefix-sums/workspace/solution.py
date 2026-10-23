'''Public specification for the prefix API.

def prefix(items: list[int]) -> list[int]::

    """Return a new list of inclusive prefix sums in input order.

    Each result[i] equals sum(items[:i + 1]); the result has the same
    length as the input. Empty input returns []. Negative values are
    supported. Input values and collection order remain unchanged.
    """
'''


def prefix(items: list[int]) -> list[int]:
    """Return inclusive prefix sums in input order as a new list.

    For every index i, result[i] equals sum(items[:i + 1]). The returned
    list has the same length as items and follows the original input order.
    Empty input returns []. Negative numbers and zero are supported.
    The input collection, its values, and its order are never mutated.
    """
    result: list[int] = []
    total = 0
    for item in items:
        total += item
        result.append(total)
    return result
