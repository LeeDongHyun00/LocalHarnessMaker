"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in text.split():
        word = token.casefold()
        counts[word] = counts.get(word, 0) + 1
    return counts
