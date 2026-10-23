"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    """Interleave groups in round-robin order without modifying the inputs.

    Take one item from each nonempty group, in collection order, per round
    until all groups are exhausted. Preserve the order and values within
    each group. Neither the outer list nor any group is modified.
    Return an empty list when there are no items.
    """
    result: list[int] = []
    for index in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if index < len(group):
                result.append(group[index])
    return result
