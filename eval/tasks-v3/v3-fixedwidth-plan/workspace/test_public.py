import unittest
from fixedwidth import render_rows
class PublicWidth(unittest.TestCase):
    def test_row(self) -> None:
        self.assertEqual(render_rows([('x',3,'L')],[{'x':'ok'}]),['ok '])
