"""Public task implementation."""


def words(text: str) -> dict[str, int]:
    return {word: text.split().count(word) for word in text.split()}
