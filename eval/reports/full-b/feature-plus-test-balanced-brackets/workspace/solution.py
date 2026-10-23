"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether all brackets in text are correctly paired and nested."""
    opening_for_closing = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []

    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in opening_for_closing:
            if not stack or stack.pop() != opening_for_closing[character]:
                return False

    return not stack
