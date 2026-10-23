"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse key=value lines, ignoring blanks and keeping the last value."""
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError("Record is missing an equals sign")
        key = key.strip()
        if not key:
            raise ValueError("Record has an empty key")
        pairs[key] = value.strip()
    return pairs
