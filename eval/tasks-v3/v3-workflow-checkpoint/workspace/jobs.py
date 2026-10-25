import copy
from typing import Any, Callable, Generator

class Job:
    def __init__(self, name: str, factory: Callable[[], Generator], effect: Callable[[str, Any], Any]) -> None:
        self.name, self.factory, self.effect = name, factory, effect
        self._generator = factory()
        self._completed: list[dict] = []
        self._pending = next(self._generator, None)

    def step(self) -> bool:
        if self._pending is None:
            return False
        key, payload = self._pending
        result = self.effect(key, copy.deepcopy(payload))
        self._completed.append(dict(key=key, result=copy.deepcopy(result)))
        try:
            self._pending = self._generator.send(copy.deepcopy(result))
        except StopIteration:
            self._pending = None
        return True

    def snapshot(self) -> dict:
        return copy.deepcopy(dict(version=1, job=self.name, completed=self._completed))

    def restore(self, checkpoint: dict) -> None:
        raise NotImplementedError('checkpoint replay')
