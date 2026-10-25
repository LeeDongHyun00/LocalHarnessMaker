from collections.abc import Iterable
class Search:
    def __init__(self, documents: Iterable[dict]) -> None:
        self.documents = {d['id']:d for d in documents}
    def put(self, document: dict) -> None:
        self.documents[document['id']] = document
    def remove(self, id: str) -> bool:
        return self.documents.pop(id,None) is not None
    def page(self, query: str, tags: Iterable[str] = (), exclude: Iterable[str] = (), offset: int = 0, limit: int = 10) -> dict:
        wanted = set(query.casefold().split())
        hits = sorted(id for id,d in self.documents.items() if wanted & set(d['text'].casefold().split()))
        return {'ids':hits[offset:offset+limit], 'total':len(hits), 'next_offset':None}
