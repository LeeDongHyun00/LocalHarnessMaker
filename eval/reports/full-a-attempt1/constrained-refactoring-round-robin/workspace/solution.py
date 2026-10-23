"""Public task implementation."""


def _round_robin(groups: list[list[int]]) -> list[int]:
    return [group[i] for i in range(max(map(len, groups), default=0)) for group in groups if i < len(group)]


def round_robin(groups: list[list[int]]) -> list[int]:
    return _round_robin(groups)


def round_robin_legacy(groups: list[list[int]]) -> list[int]:
    return _round_robin(groups)
