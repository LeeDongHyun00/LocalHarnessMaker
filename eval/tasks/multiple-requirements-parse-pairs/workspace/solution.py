"""Public task implementation."""


def parse_pairs(text: str) -> dict[str, str]:
    return dict(line.split('=') for line in text.splitlines())
