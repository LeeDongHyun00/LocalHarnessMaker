"""Public task implementation."""

from itertools import permutations as character_permutations


def permutations(text: str) -> list[str]:
    """Return distinct character permutations in lexicographic order."""
    return sorted({"".join(chars) for chars in character_permutations(text)})
