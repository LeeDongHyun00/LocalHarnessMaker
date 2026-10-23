"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether (), [] and {} are correctly paired and nested in text.

    Ignore all other characters. Any unmatched opening or closing bracket
    makes the result False; empty text returns True. The input is not modified,
    and its characters are checked in their original order.
    """
    opening_for = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []

    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in opening_for:
            if not stack or stack.pop() != opening_for[character]:
                return False

    return not stack
