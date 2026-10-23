"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse newline-separated key=value records into a dictionary.

    Split on the first equals sign and strip both key and value. Ignore
    blank lines; the last repeated key wins. Allow empty values. Raise
    ValueError for a missing equals sign or an empty key.

    Keys retain their first occurrence order, even when their values are
    replaced by later records. The input text is unchanged.
    """
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ValueError("Each record must contain an equals sign and a nonempty key")
        pairs[key] = value.strip()
    return pairs
