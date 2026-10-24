import unittest
from columns import render
class PublicColumns(unittest.TestCase):
    def test_ascii(self) -> None:
        self.assertEqual(render([['a','bc']], [2,3]), 'a  | bc ')
