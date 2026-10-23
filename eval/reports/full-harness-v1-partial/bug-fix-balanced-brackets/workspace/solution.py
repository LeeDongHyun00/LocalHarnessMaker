"""Public task implementation."""


def balanced(text: str) -> bool:
    """Check bracket nesting, ignoring other characters; empty text is balanced."""
    stack: list[str] = []
    matching: dict[str, str] = {')': '(', ']': '[', '}': '{'}
    for char in text:
        if char in '([{':
            stack.append(char)
        elif char in matching:
            if not stack or stack.pop() != matching[char]:
                return False
    return not stack
