"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    """Interleave groups in round order without modifying any input list."""
    result: list[int] = []
    for index in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if index < len(group):
                result.append(group[index])
    return result
