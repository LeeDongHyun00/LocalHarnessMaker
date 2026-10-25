import unittest
from emitter import render
class PublicHtml(unittest.TestCase):
    def test_element(self) -> None:
        self.assertEqual(render(('p',[],['hello'])), '<p>hello</p>')
