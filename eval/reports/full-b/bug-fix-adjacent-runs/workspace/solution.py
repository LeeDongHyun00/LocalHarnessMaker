"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    encoded: list[tuple[str, int]] = []
    for value in items:
        if encoded and encoded[-1][0] == value:
            encoded[-1] = (value, encoded[-1][1] + 1)
        else:
            encoded.append((value, 1))
    return encoded
