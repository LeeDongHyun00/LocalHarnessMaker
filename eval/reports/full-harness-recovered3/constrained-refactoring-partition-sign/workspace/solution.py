"""Public task implementation."""


def _partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return ([x for x in items if x < 0], [x for x in items if x == 0], [x for x in items if x > 0])


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return _partition(items)


def partition_legacy(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return _partition(items)
