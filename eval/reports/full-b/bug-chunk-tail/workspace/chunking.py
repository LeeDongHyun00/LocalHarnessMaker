"""Small list partitioning utility."""


def chunked(items: list[int], size: int) -> list[list[int]]:
    """Partition items into consecutive chunks of a positive size."""
    return [items[start : start + size] for start in range(0, len(items), size)]
