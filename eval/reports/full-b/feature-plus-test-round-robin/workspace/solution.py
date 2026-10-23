"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    """Take one item per group each round without modifying the groups."""
    result: list[int] = []
    for position in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if position < len(group):
                result.append(group[position])
    return result
