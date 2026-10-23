"""Public task implementation."""

from itertools import permutations as character_permutations


def permutations(text: str) -> list[str]:
    return sorted({"".join(chars) for chars in character_permutations(text)})
