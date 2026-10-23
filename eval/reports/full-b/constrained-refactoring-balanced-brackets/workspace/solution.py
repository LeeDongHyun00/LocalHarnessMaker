"""Public task implementation."""


def _balanced(text: str) -> bool:
    stack: list[str] = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for char in text:
        if char in '([{':
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
    return not stack


def balanced(text: str) -> bool:
    return _balanced(text)


def balanced_legacy(text: str) -> bool:
    return _balanced(text)
