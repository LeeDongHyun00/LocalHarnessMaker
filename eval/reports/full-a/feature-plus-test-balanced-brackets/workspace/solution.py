"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether the brackets in text are properly matched and nested."""
    openings: list[str] = []
    matching = {")": "(", "]": "[", "}": "{"}
    for character in text:
        if character in "([{":
            openings.append(character)
        elif character in matching:
            if not openings or openings.pop() != matching[character]:
                return False
    return not openings
