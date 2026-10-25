from typing import NamedTuple

class Token(NamedTuple):
    kind: str
    value: str
    start: int
    end: int
