"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether (), [] and {} are correctly matched and nested.

    Ignore all other characters. Any unmatched opening or closing bracket
    makes the result False; empty text returns True. The input is unchanged.
    """
    stack: list[str] = []
    matching: dict[str, str] = {')': '(', ']': '[', '}': '{'}
    for character in text:
        if character in '([{':
            stack.append(character)
        elif character in matching:
            if not stack or stack.pop() != matching[character]:
                return False
    return not stack
