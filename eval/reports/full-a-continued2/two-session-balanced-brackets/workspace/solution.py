"""Public task implementation."""


def balanced(text: str) -> bool:
    """Return whether the brackets in text are properly paired and nested."""
    closing_to_opening = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for character in text:
        if character in "([{":
            stack.append(character)
        elif character in closing_to_opening:
            if not stack or stack.pop() != closing_to_opening[character]:
                return False
    return not stack


def balanced_many(cases: list[tuple]) -> list:
    """Call balanced with each case's positional arguments, in order.

    Stop at the first exception and let it propagate unchanged.
    """
    return [balanced(*case) for case in cases]
