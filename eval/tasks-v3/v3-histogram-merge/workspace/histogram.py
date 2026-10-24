import math
from collections.abc import Sequence

class Histogram:
    def __init__(self, bounds: Sequence[float]) -> None:
        self.bounds = list(bounds)
        if not self.bounds or any(not math.isfinite(v) for v in self.bounds) or any(a >= b for a, b in zip(self.bounds, self.bounds[1:])):
            raise ValueError('bounds')
        self.counts = [0] * len(self.bounds)
        self.overflow = 0

    def observe(self, value: float) -> None:
        if not math.isfinite(value):
            raise ValueError('sample')
        for i, bound in enumerate(self.bounds):
            if value <= bound:
                self.counts[i] += 1
                return
        self.overflow += 1

    @property
    def total(self) -> int:
        return sum(self.counts) + self.overflow

    def merge(self, other: 'Histogram') -> 'Histogram':
        if self.bounds != other.bounds:
            raise ValueError('incompatible')
        merged = Histogram(self.bounds)
        merged.counts = [a + b for a, b in zip(self.counts, other.counts)]
        merged.overflow = self.overflow + other.overflow + other.counts[-1]
        return merged
