"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    return [x for group in groups for x in group]
