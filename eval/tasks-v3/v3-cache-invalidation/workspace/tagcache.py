from typing import Any
class Cache:
    def __init__(self, capacity: int) -> None:
        self.capacity=capacity; self.values: dict = {}
    def put(self, namespace: str, key: str, value: Any, tags: list[str]) -> None:
        self.values[(namespace,key)]=value
    def get(self, namespace: str, key: str) -> tuple[bool,Any]:
        return (True,self.values[(namespace,key)]) if (namespace,key) in self.values else (False,None)
    def invalidate(self, namespace: str, tags: list[str]) -> list[str]: return []
    def clear(self, namespace: str) -> list[str]: return []
    def stats(self, namespace: str) -> dict: return {'entries':len(self.values)}
    def snapshot(self) -> dict: return {}
    @classmethod
    def restore(cls, snapshot: dict) -> 'Cache': return cls(snapshot['capacity'])
