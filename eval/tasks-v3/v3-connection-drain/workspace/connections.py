from contextlib import contextmanager
from typing import Any, Callable, Iterator
class Pool:
    def __init__(self, resources: list[Any], close: Callable) -> None:
        self.resources=list(resources)
    def acquire(self, timeout: float | None = None) -> Any:
        if not self.resources: raise TimeoutError('pool')
        return self.resources.pop(0)
    def release(self, resource: Any) -> None: self.resources.append(resource)
    @contextmanager
    def lease(self, timeout: float | None = None) -> Iterator[Any]:
        resource=self.acquire(timeout)
        try: yield resource
        finally: self.release(resource)
    def drain(self, timeout: float | None = None) -> dict: return self.diagnostics()
    def diagnostics(self) -> dict: return {'state':'open','idle':len(self.resources)}
