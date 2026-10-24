"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count casefolded whitespace-delimited tokens, retaining punctuation."""
    counts: dict[str, int] = {}
    for token in text.split():
        folded = token.casefold()
        counts[folded] = counts.get(folded, 0) + 1
    return counts
