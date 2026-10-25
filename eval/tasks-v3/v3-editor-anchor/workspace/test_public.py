import unittest
from anchors import transform
class PublicAnchors(unittest.TestCase):
    def test_distant_insert(self) -> None:
        self.assertEqual(transform(6, [('insert', 1, 'ab')]), 8)
