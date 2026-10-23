"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    """Parse newline-separated key=value records into an ordered dictionary.

    Ignore blank or whitespace-only lines. Split each remaining line on its
    first equals sign, stripping surrounding whitespace from both the key and
    value. Empty values are allowed. Raise ValueError if a nonblank line has
    no equals sign or its stripped key is empty.

    The last value for a repeated key wins; keys retain the order of their
    first appearance. Preserve whitespace and equals signs inside values.
    The input is not modified.
    """
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue

        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError("Each nonblank record must contain an equals sign")

        key = key.strip()
        if not key:
            raise ValueError("Record keys must not be empty")

        pairs[key] = value.strip()

    return pairs
