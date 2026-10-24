import unittest
from settings import resolve
class PublicSettings(unittest.TestCase):
    def test_nonempty_override(self) -> None:
        choice = resolve({'color':'blue'}, {'color':'green'}, {})['color']
        self.assertEqual((choice.value, choice.source), ('green','file'))
