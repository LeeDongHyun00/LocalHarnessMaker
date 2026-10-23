"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive prefix sums in the original input order.

    Each result element is the sum of the input values up to and including
    that position. The result has the same length as the input; empty input
    returns []. Negative numbers are supported. Input values and their
    order are left unchanged.
    """
    return [sum(items[:i + 1]) for i in range(len(items))]
