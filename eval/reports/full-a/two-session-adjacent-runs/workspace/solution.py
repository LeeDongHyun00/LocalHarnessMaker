"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings without modifying the input list."""
    encoded: list[tuple[str, int]] = []
    for item in items:
        if encoded and encoded[-1][0] == item:
            value, count = encoded[-1]
            encoded[-1] = (value, count + 1)
        else:
            encoded.append((item, 1))
    return encoded


def runs_many(cases: list[tuple]) -> list:
    """Call runs with each case's positional arguments, stopping on failure."""
    return [runs(*case) for case in cases]
