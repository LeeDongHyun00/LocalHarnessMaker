"""Public task implementation."""


def balanced(text: str) -> bool:
    opening_brackets: list[str] = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for character in text:
        if character in '([{':
            opening_brackets.append(character)
        elif character in pairs:
            if not opening_brackets or opening_brackets.pop() != pairs[character]:
                return False
    return not opening_brackets
