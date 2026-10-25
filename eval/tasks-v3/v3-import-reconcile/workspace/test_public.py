import unittest
from reconcile import Importer
class PublicImport(unittest.TestCase):
    def test_first_row(self) -> None:
        importer=Importer(['primary'])
        self.assertEqual(importer.ingest([{'id':'one','updated':1,'source':'primary','fields':{}}]),['inserted'])
