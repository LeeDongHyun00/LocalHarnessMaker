"""Public task implementation."""


def balanced(text: str) -> bool:
    opening: list[str] = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for char in text:
        if char in '([{':
            opening.append(char)
        elif char in pairs:
            if not opening or opening.pop() != pairs[char]:
                return False
    return not opening
