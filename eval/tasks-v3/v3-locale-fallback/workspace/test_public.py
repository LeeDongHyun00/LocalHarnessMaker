import unittest
from catalog import Catalog
class PublicCatalog(unittest.TestCase):
    def test_exact(self) -> None:
        c = Catalog({'fr':{'hello':'bonjour'}}, {})
        self.assertEqual(c.lookup('fr','hello'), ('bonjour','fr'))
