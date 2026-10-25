class Windows:
    def __init__(self, width: int) -> None:
        self.width = width
        self.watermark: int | None = None
        self._buckets: dict[int, int] = {}
        self._late: list[tuple[int,int]] = []
    def add(self, timestamp: int, value: int) -> None:
        if self.watermark is not None and timestamp < self.watermark:
            self._late.append((timestamp,value))
            return
        start = timestamp // self.width * self.width
        self._buckets[start] = self._buckets.get(start, 0) + value
    def late(self) -> list[tuple[int,int]]:
        events, self._late = self._late, []
        return events

    def advance(self, mark: int) -> list[tuple[int,int,int]]:
        raise NotImplementedError('watermark')
