"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count whitespace-separated, casefolded tokens, preserving punctuation."""
    counts: dict[str, int] = {}
    for token in text.split():
        folded = token.casefold()
        counts[folded] = counts.get(folded, 0) + 1
    return counts


def words_many(cases: list[tuple]) -> list:
    """Call words with each case's positional arguments, in order."""
    return [words(*case) for case in cases]
