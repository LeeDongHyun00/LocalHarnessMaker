from typing import Any

class ReadyQueue:
    def __init__(self) -> None:
        self.items = {}
        self.sequence = 0
    def push(self, key: str, priority: Any, payload: Any) -> None:
        if key in self.items:
            raise ValueError('duplicate key')
        self.items[key] = (priority, self.sequence, payload)
        self.sequence += 1
    def cancel(self, key: str) -> bool:
        return self.items.pop(key, None) is not None
    def pop(self) -> tuple[str, Any]:
        if not self.items:
            raise IndexError('empty')
        key = sorted(self.items, key=lambda k: self.items[k][:2])[0]
        return key, self.items.pop(key)[2]
    def __len__(self) -> int:
        return len(self.items)
