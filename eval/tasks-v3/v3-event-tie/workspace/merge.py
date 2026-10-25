from collections.abc import Mapping, Iterable
class Merge:
    def __init__(self, streams: Mapping[str,Iterable[tuple]], checkpoint: dict | None = None) -> None:
        self.streams = dict(streams)
        self.counts = dict.fromkeys(streams,0)
        self.events = None
    def take(self, n: int) -> list[tuple]:
        if self.events is None:
            self.events = sorted([(name,t,p) for name,source in self.streams.items() for t,p in source],key=lambda e:e[1])
        output = self.events[:n]
        self.events = self.events[n:]
        for name,_,_ in output: self.counts[name] += 1
        return output
    def checkpoint(self) -> dict[str,int]: return dict(self.counts)
