import threading
from typing import Any, Callable

class NotFound(LookupError):
    pass

class Memoizer:
    def __init__(self, loader: Callable[[str], Any], ttl: float, negative_ttl: float, clock: Callable[[],float]) -> None:
        self.loader, self.ttl, self.negative_ttl, self.clock = loader, ttl, negative_ttl, clock
        self._entries: dict[str,tuple[float,bool,Any]] = {}
        self._busy: dict[str,bool] = {}
        self._condition = threading.Condition()

    def get(self, key: str) -> Any:
        entry = self._entries.get(key)
        if entry is not None and self.clock() < entry[0]:
            return entry[2]
        value = self.loader(key)
        self._entries[key] = (self.clock() + self.ttl, True, value)
        return value
