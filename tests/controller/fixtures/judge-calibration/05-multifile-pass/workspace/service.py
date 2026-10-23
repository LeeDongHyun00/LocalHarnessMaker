from settings import DEFAULT_LIMIT

def build(limit: int = DEFAULT_LIMIT) -> dict[str, int]:
    return {"limit": limit}
