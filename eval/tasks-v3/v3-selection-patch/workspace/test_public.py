import unittest
from patching import Document
class PublicPatch(unittest.TestCase):
    def test_replace(self) -> None:
        doc = Document('cat', [])
        doc.apply([(0, 3, 'dog')])
        self.assertEqual(doc.text, 'dog')
