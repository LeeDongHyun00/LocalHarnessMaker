"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count casefolded tokens split on arbitrary whitespace.

    Punctuation remains part of each token. Empty or whitespace-only text
    returns {}. Keys retain the order of first occurrence after casefolding,
    and the input text is unchanged.
    """
    counts: dict[str, int] = {}
    for token in text.split():
        word = token.casefold()
        counts[word] = counts.get(word, 0) + 1
    return counts
