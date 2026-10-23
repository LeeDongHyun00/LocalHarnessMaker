"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse newline-separated key=value records into a dictionary.

    Ignore blank or whitespace-only lines. Split each nonblank line at its
    first equals sign and strip whitespace from both the key and value.
    Values may be empty and retain any additional equals signs. Raise
    ValueError if a nonblank line has no equals sign or its stripped key is
    empty.

    The last value for a repeated key wins. Keys retain their order of first
    appearance, including when their values are replaced. The input is not
    modified.
    """
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
