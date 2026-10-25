import unittest
from query import search
class PublicQuery(unittest.TestCase):
    def test_word(self) -> None:
        self.assertEqual(search([{'id':'x','text':'hello world'}],'hello'),['x'])
