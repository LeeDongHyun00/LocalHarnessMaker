from dataclasses import dataclass
import base64
import json

@dataclass(frozen=True)
class Posting:
    doc_id: str
    score: int

@dataclass(frozen=True)
class Page:
    items: list[Posting]
    next_cursor: str | None

class Index:
    def __init__(self, records: dict[str,list[Posting]]) -> None:
        self._records: dict[str,list[Posting]] = {}
        self._revision = 0
        for query, postings in records.items():
            self._store(query, postings)
    def _store(self, query: str, postings: list[Posting]) -> None:
        best: dict[str,int] = {}
        for p in postings:
            best[p.doc_id] = max(best.get(p.doc_id, p.score), p.score)
        self._records[query] = sorted([Posting(key,value) for key,value in best.items()], key=lambda p: (-p.score,p.doc_id))
    def replace(self, query: str, postings: list[Posting]) -> None:
        self._store(query, postings)
        self._revision += 1

    def search(self, query: str, limit: int, cursor: str | None = None) -> Page:
        if type(limit) is not int or limit <= 0:
            raise ValueError('limit')
        if cursor is not None:
            raise NotImplementedError('continuation')
        return Page(list(self._records.get(query, [])[:limit]), None)
