"""Public task implementation."""


def ordinal(value: int) -> str:
    return str(value) + {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
