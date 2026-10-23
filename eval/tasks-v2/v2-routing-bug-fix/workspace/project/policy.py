def normalize(value: str) -> str:
    return '/' + '/'.join(part for part in value.strip().split('/') if part)
