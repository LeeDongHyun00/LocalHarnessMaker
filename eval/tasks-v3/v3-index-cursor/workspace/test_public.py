import unittest
from postings import Index, Posting
class PublicIndex(unittest.TestCase):
    def test_first(self) -> None:
        self.assertEqual(Index({'q':[Posting('doc',2)]}).search('q', 1).items, [Posting('doc',2)])
