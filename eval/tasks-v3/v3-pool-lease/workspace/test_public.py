import unittest
from leases import Pool
class PublicPool(unittest.TestCase):
    def test_bound(self) -> None:
        pool = Pool(1, lambda: 0)
        first, second = pool.request(), pool.request()
        self.assertIsNotNone(pool.acquire(first, 3))
        self.assertIsNone(pool.acquire(second, 3))
