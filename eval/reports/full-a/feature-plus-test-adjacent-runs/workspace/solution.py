"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings without modifying the input."""
    result: list[tuple[str, int]] = []
    for item in items:
        if result and result[-1][0] == item:
            value, count = result[-1]
            result[-1] = (value, count + 1)
        else:
            result.append((item, 1))
    return result
