"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    """Return items by taking one from each nonempty group in order per round.

    Continue until all groups are exhausted, preserving the order of items
    within each group. Empty groups are skipped. Neither the outer collection
    nor any group or input value is modified.
    """
    return [
        group[index]
        for index in range(max((len(group) for group in groups), default=0))
        for group in groups
        if index < len(group)
    ]
