"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether (), [], and {} are correctly nested in text.

    Ignore all other characters. Unmatched opening or closing brackets
    return False; empty text returns True. Input is read in its original
    order and is never modified.
    """
    stack: list[str] = []
    matching = {')': '(', ']': '[', '}': '{'}
    for character in text:
        if character in '([{':
            stack.append(character)
        elif character in matching:
            if not stack or stack.pop() != matching[character]:
                return False
    return not stack
