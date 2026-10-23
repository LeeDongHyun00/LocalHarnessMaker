"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    """Count casefolded tokens separated by arbitrary whitespace.

    Punctuation remains part of each token. Empty or whitespace-only text
    returns an empty dictionary. Keys retain the order in which their
    casefolded tokens first appear, and the input is left unchanged.
    """
    counts: dict[str, int] = {}
    for token in text.split():
        word = token.casefold()
        counts[word] = counts.get(word, 0) + 1
    return counts
