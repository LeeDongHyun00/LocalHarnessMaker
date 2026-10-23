"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether brackets are correctly paired and nested in text."""
    matching_openers = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in matching_openers:
            if not stack or stack.pop() != matching_openers[character]:
                return False
    return not stack


def balanced_many(cases: list[tuple]) -> list:
    """Call balanced for each argument tuple in order, propagating exceptions."""
    return [balanced(*arguments) for arguments in cases]
