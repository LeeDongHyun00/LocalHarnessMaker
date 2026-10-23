"""Public task implementation."""


def _parse_pairs(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition('=')
        key = key.strip()
        if not sep or not key:
            raise ValueError('invalid record')
        result[key] = value.strip()
    return result


def parse_pairs(text: str) -> dict[str, str]:
    return _parse_pairs(text)


def parse_pairs_legacy(text: str) -> dict[str, str]:
    return _parse_pairs(text)
