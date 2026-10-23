from pathlib import Path

def load(path: Path) -> str:
    with path.open(encoding="utf-8") as stream:
        return stream.read()
