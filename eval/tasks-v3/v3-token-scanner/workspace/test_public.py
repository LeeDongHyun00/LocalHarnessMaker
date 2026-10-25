import unittest
from scanner import scan
class PublicScan(unittest.TestCase):
    def test_word(self) -> None:
        self.assertEqual(scan('hello')[0].value, 'hello')
