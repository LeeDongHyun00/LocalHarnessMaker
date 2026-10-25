import unittest
from catalog import parse_rows
class PublicCatalog(unittest.TestCase):
    def test_literal(self) -> None:
        self.assertEqual(parse_rows('msg[other] = "hello"')[0][:3], ('msg','other','hello'))
