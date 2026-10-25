import unittest
from merge import Merge
class PublicMerge(unittest.TestCase):
    def test_order(self) -> None:
        merger = Merge({'one':[(2,'early'),(9,'late')]})
        self.assertEqual(merger.take(3), [('one',2,'early'),('one',9,'late')])
