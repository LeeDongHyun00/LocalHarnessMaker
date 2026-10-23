"""Public task implementation."""


def round_robin(groups: list[list[int]]) -> list[int]:
    """Take one item from each nonempty group in order each round until exhausted.

    Preserve item order within each group and the supplied order of groups.
    Return a new list without modifying the groups or their values.
    """
    result: list[int] = []
    for index in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if index < len(group):
                result.append(group[index])
    return result
