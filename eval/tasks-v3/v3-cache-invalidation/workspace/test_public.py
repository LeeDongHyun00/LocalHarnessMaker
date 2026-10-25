import unittest
from tagcache import Cache
class PublicCache(unittest.TestCase):
    def test_value(self) -> None:
        cache=Cache(4); cache.put('demo','key','value',[])
        self.assertEqual(cache.get('demo','key'),(True,'value'))
