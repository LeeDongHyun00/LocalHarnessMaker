import copy
import json
from pathlib import Path
class Importer:
    def __init__(self, rank: list[str]) -> None:
        self.rank=list(rank)
        self.rows: dict[str,dict]={}
    def ingest(self, rows: object) -> list[str]:
        statuses=[]
        for row in rows:
            self.rows[row['id']]=copy.deepcopy(row)
            statuses.append('inserted')
        return statuses
    def snapshot(self) -> list[dict]:
        return copy.deepcopy(sorted(self.rows.values(),key=lambda r:r['id']))
    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({'rank':self.rank,'rows':self.snapshot()},sort_keys=True,separators=(',',':')))
    @classmethod
    def load(cls, path: str | Path) -> 'Importer':
        state=json.loads(Path(path).read_text())
        obj=cls(state['rank'])
        obj.ingest(state['rows'])
        return obj
