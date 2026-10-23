"""Public task implementation."""


def balanced(text: str) -> bool:
    opening_for = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for char in text:
        if char in '([{':
            stack.append(char)
        elif char in opening_for:
            if not stack or stack.pop() != opening_for[char]:
                return False
    return not stack
