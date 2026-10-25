def version_tuple(text: str) -> tuple[int, int, int]:
    """Read the numeric core; prerelease ordering belongs in the resolver."""
    return tuple(int(part) for part in text.split('-')[0].split('.'))
