from collections.abc import Callable
class WorkerPool:
    def __init__(self, limit: int, on_ready: Callable[[str,int],None]) -> None:
        self.limit, self.on_ready = limit, on_ready
        self._active: set[int] = set()
        self._pending: list[str] = []
        self._next = 1
    @property
    def active(self) -> frozenset[int]: return frozenset(self._active)
    @property
    def pending(self) -> tuple[str,...]: return tuple(self._pending)
    def acquire(self, ticket: str) -> int | None:
        if len(self._active) < self.limit:
            lease = self._next
            self._next += 1
            self._active.add(lease)
            return lease
        self._pending.append(ticket)
        return None
    def release(self, lease: int) -> bool:
        if lease not in self._active: return False
        self._active.remove(lease)
        return True
    def resize(self, limit: int) -> None:
        self.limit = limit
        self._active = set(sorted(self._active)[:limit])
