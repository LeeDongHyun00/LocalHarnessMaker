"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return ([x for x in items if x < 0], [x for x in items if x == 0], [x for x in items if x > 0])


def partition_legacy(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return ([x for x in items if x < 0], [x for x in items if x == 0], [x for x in items if x > 0])
