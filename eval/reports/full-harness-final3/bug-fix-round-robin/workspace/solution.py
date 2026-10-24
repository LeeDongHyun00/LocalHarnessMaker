"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    return [
        group[index]
        for index in range(max((len(group) for group in groups), default=0))
        for group in groups
        if index < len(group)
    ]
