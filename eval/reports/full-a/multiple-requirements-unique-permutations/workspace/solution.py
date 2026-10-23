"""Public task implementation."""

from itertools import permutations as character_permutations


def permutations(text: str) -> list[str]:
    """Return all distinct character permutations in sorted lexicographic order.

    Inputs contain at most seven characters. The empty string has one
    permutation: the empty string. The input value is preserved.
    """
    return sorted({"".join(chars) for chars in character_permutations(text)})
