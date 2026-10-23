"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count casefolded tokens separated by arbitrary whitespace."""
    counts: dict[str, int] = {}
    for token in text.split():
        token = token.casefold()
        counts[token] = counts.get(token, 0) + 1
    return counts
