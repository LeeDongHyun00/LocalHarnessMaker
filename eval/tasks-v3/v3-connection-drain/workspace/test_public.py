import unittest
from connections import Pool
class PublicPool(unittest.TestCase):
    def test_roundtrip(self) -> None:
        resource=object(); pool=Pool([resource],lambda item:None)
        pool.release(pool.acquire(0))
        self.assertIs(pool.acquire(0),resource)
