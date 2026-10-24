import unicodedata


def display_width(text: str) -> int:
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in {'W', 'F'} else 1 for c in text)


