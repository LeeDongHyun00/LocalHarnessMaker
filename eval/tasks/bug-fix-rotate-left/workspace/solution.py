"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    return items[steps:] + items[:steps]
