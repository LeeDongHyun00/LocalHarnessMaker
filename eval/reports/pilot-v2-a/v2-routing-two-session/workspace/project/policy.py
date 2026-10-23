def normalize(value: str) -> str:
    """Return a canonical path, retaining a single slash for the root."""
    parts = value.strip().casefold().split('/')
    return '/' + '/'.join(part for part in parts if part)
