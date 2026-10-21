"""Public task implementation."""


def permutations(text: str) -> list[str]:
    from itertools import permutations as permute
    return sorted({''.join(p) for p in permute(text)})


def permutations_legacy(text: str) -> list[str]:
    from itertools import permutations as permute
    return sorted({''.join(p) for p in permute(text)})
