"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether (), [] and {} are correctly nested in text.

    Ignore all other characters. Unmatched opening or closing brackets
    return False; empty text returns True. The input is not modified.
    """
    openings: list[str] = []
    matching = {')': '(', ']': '[', '}': '{'}
    for character in text:
        if character in '([{':
            openings.append(character)
        elif character in matching:
            if not openings or openings.pop() != matching[character]:
                return False
    return not openings
