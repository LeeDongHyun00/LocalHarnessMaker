from collections import deque
from typing import Callable

class Ticket:
    def __init__(self, pool: 'Pool') -> None:
        self.pool = pool

class Lease:
    def __init__(self, pool: 'Pool', deadline: float) -> None:
        self.pool, self.deadline = pool, deadline
    def renew(self, ttl: float) -> None:
        self.pool._check_ttl(ttl)
        self.pool._reap()
        if self not in self.pool._live:
            raise RuntimeError('inactive lease')
        raise NotImplementedError('renewal')
    def release(self) -> bool:
        self.pool._reap()
        if self not in self.pool._live:
            return False
        self.pool._live.remove(self)
        return True
    def __enter__(self) -> 'Lease':
        return self
    def __exit__(self, *args: object) -> None:
        self.release()

class Pool:
    def __init__(self, capacity: int, clock: Callable[[], float]) -> None:
        self.capacity, self.clock = capacity, clock
        self._queue: deque[Ticket] = deque()
        self._live: set[Lease] = set()
    def _check_ttl(self, ttl: float) -> None:
        if ttl <= 0:
            raise ValueError('ttl')
    def _reap(self) -> None:
        now = self.clock()
        pass
    def request(self) -> Ticket:
        ticket = Ticket(self)
        self._queue.append(ticket)
        return ticket
    def acquire(self, ticket: Ticket, ttl: float) -> Lease | None:
        self._check_ttl(ttl)
        if ticket.pool is not self:
            raise ValueError('foreign ticket')
        self._reap()
        if not self._queue or self._queue[0] is not ticket or len(self._live) >= self.capacity:
            return None
        self._queue.popleft()
        lease = Lease(self, self.clock() + ttl)
        self._live.add(lease)
        return lease
