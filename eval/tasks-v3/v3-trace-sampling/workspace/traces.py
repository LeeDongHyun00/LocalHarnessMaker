import copy
class Collector:
    def __init__(self, rate: int) -> None:
        self.rate=rate
        self.spans: dict[tuple,dict]={}
    def accept(self, span: dict) -> None:
        self.spans[(span['trace'],span['id'])]=copy.deepcopy(span)
    def export(self) -> list[dict]:
        return copy.deepcopy(sorted(self.spans.values(),key=lambda s:(s['trace'],s['start'],s['id'])))
