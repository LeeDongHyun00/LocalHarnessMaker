"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse key=value lines, keeping the last value for repeated keys."""
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ValueError("Each record must contain '=' and a nonempty key")
        pairs[key] = value.strip()
    return pairs
