import unittest
from histogram import Histogram
class PublicBuckets(unittest.TestCase):
    def test_sample(self) -> None:
        histogram = Histogram([10,20])
        histogram.observe(8)
        self.assertEqual(histogram.counts, [1,0])
