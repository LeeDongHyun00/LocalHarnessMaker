"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse newline-separated key=value records; the last repeated key wins.

    Blank lines are ignored. Keys and values are stripped of whitespace;
    missing separators and empty keys raise ValueError.
    """
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            raise ValueError("Each record must contain '=' and a nonempty key")
        pairs[key.strip()] = value.strip()
    return pairs
