import unittest
from catalog import extract
class PublicCatalog(unittest.TestCase):
    def test_literal(self) -> None:
        self.assertEqual(extract({'a.py':'_("Hello")'})[0]['id'],'Hello')
