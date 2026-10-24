def normalize(value: str) -> str:
    return '/' + '/'.join(part for part in value.strip().casefold().split('/') if part)
