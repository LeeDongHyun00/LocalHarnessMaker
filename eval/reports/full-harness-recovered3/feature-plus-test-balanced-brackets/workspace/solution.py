"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether all brackets are matched and correctly nested."""
    stack: list[str] = []
    matching = {")": "(", "]": "[", "}": "{"}
    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in matching:
            if not stack or stack.pop() != matching[character]:
                return False
    return not stack
