import unittest
from search import Search
class PublicSearch(unittest.TestCase):
    def test_word(self) -> None:
        search = Search([{'id':'a','text':'blue sky','tags':[]}])
        self.assertEqual(search.page('BLUE')['ids'], ['a'])
