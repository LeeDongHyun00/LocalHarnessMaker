"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Return each adjacent run of equal strings with its length."""
    encoded: list[tuple[str, int]] = []
    for item in items:
        if encoded and encoded[-1][0] == item:
            value, count = encoded[-1]
            encoded[-1] = (value, count + 1)
        else:
            encoded.append((item, 1))
    return encoded
