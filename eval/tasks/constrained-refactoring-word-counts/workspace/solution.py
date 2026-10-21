"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in text.split():
        word = word.casefold()
        result[word] = result.get(word, 0) + 1
    return result


def words_legacy(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in text.split():
        word = word.casefold()
        result[word] = result.get(word, 0) + 1
    return result
