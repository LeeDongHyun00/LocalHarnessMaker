"""Public task implementation."""


def _count_words(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in text.split():
        word = word.casefold()
        result[word] = result.get(word, 0) + 1
    return result


def words(text: str) -> dict[str, int]:
    return _count_words(text)


def words_legacy(text: str) -> dict[str, int]:
    return _count_words(text)
