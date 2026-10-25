from contextlib import contextmanager
from typing import Any, Iterator

class History:
    def __init__(self) -> None:
        self._past: list[Any] = []
        self._future: list[Any] = []

    def execute(self, command: Any) -> None:
        command.do()
        self._past.append(command)
        self._future.clear()

    @contextmanager
    def group(self) -> Iterator[None]:
        yield

    def undo(self) -> bool:
        if not self._past:
            return False
        command = self._past.pop()
        command.undo()
        self._future.append(command)
        return True

    def redo(self) -> bool:
        if not self._future:
            return False
        command = self._future.pop()
        command.do()
        self._past.append(command)
        return True
