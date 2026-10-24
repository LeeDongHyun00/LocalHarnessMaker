"""Public task implementation."""

from itertools import permutations as character_permutations


def permutations(text: str) -> list[str]:
    """Return distinct character permutations in sorted lexicographic order.

    The input is a string of at most seven characters and is left unchanged.
    The empty string has exactly one permutation: the empty string.
    """
    return sorted({"".join(chars) for chars in character_permutations(text)})
