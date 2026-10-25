from collections.abc import Callable
from typing import Any
class Cache:
    def __init__(self, loader: Callable, clock: Callable, ttl: float, stale_for: float) -> None:
        self.loader, self.clock, self.ttl, self.stale_for = loader, clock, ttl, stale_for
        self.entries: dict[Any,tuple[Any,float]] = {}
    def get(self, key: Any) -> tuple[Any,str]:
        now = self.clock()
        if key in self.entries: return self.entries[key][0], 'fresh'
        value = self.loader(key)
        self.entries[key] = value, now
        return value, 'loaded'
    def invalidate(self, key: Any) -> bool:
        return self.entries.pop(key,None) is not None
