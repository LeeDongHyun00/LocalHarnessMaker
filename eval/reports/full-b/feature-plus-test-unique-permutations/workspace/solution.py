"""Public task implementation."""

from itertools import permutations as _character_permutations


def permutations(text: str) -> list[str]:
    """Return distinct permutations of text in lexicographic order."""
    return sorted({"".join(chars) for chars in _character_permutations(text)})
