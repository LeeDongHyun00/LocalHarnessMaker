"""Public task implementation."""


def balanced(text: str) -> bool:
    return text.count('(') == text.count(')')
