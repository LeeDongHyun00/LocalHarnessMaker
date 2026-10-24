"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count casefolded whitespace-separated tokens, preserving punctuation."""
    counts: dict[str, int] = {}
    for token in text.split():
        normalized = token.casefold()
        counts[normalized] = counts.get(normalized, 0) + 1
    return counts


def words_many(cases: list[tuple]) -> list:
    """Call words with each case's positional arguments, in order."""
    return [words(*case) for case in cases]
