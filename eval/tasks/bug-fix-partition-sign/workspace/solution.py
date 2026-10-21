"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    return (sorted(x for x in items if x < 0), [], sorted(x for x in items if x > 0))
