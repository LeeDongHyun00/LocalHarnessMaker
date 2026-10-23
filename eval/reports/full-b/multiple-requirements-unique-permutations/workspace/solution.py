"""Public task implementation."""

from itertools import permutations as _permutations


def permutations(text: str) -> list[str]:
    """Return all distinct character permutations in lexicographic order.

    The input is a string of at most seven characters and is left unchanged.
    The empty string has one permutation, so an empty input returns [""].
    Ordering follows Python's string comparison, including case and Unicode.
    """
    return sorted({"".join(characters) for characters in _permutations(text)})
