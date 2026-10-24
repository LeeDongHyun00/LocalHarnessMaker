import heapq
from collections.abc import Callable

class Timers:
    def __init__(self, clock: Callable[[], float]) -> None:
        self.clock = clock
        self.heap: list[tuple[float, int, Callable[[], None]]] = []
        self.active: set[int] = set()
        self.sequence = 0

    def call_at(self, deadline: float, callback: Callable[[], None]) -> int:
        handle = self.sequence
        self.sequence += 1
        heapq.heappush(self.heap, (deadline, handle, callback))
        self.active.add(handle)
        return handle

    def cancel(self, handle: int) -> bool:
        if handle not in self.active:
            return False
        self.active.remove(handle)
        return True

    def run_due(self) -> int:
        cutoff = self.clock()
        fired = 0
        while self.heap and self.heap[0][0] <= cutoff:
            _, handle, callback = heapq.heappop(self.heap)
            if handle not in self.active:
                break
            self.active.remove(handle)
            callback()
            fired += 1
        return fired
