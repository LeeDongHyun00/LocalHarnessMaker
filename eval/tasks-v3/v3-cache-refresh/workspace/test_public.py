import unittest
from refresh import Cache
class PublicRefresh(unittest.TestCase):
    def test_fresh_hit(self) -> None:
        cache = Cache(lambda key: key.upper(), lambda: 0, 10, 5)
        self.assertEqual((cache.get('x'),cache.get('x')), (('X','loaded'),('X','fresh')))
