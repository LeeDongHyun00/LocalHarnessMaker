import json
from pathlib import Path
class Corrupt(ValueError): pass
class Log:
    def __init__(self, path: str | Path) -> None: self.path=Path(path)
    def append(self, record: dict) -> bool:
        with self.path.open('a') as output: output.write(json.dumps(record)+'\n')
        return True
    def replay(self) -> dict:
        result={}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                item=json.loads(line)
                if item['op']=='put': result[item['key']]=item['value']
        return result
    def compact(self) -> None: pass
