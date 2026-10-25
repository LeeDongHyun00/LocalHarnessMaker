import unittest
from memo import Memoizer
class PublicMemo(unittest.TestCase):
    def test_positive(self) -> None:
        calls = []
        cache = Memoizer(lambda key: calls.append(key) or 'ok', 10, 2, lambda: 0)
        cache.get('public')
        cache.get('public')
        self.assertEqual(calls, ['public'])
