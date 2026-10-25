import unittest
from directives import Parser
class PublicDirectives(unittest.TestCase):
    def test_set(self) -> None:
        self.assertEqual(Parser().parse('set greeting hello'),{'greeting':'hello'})
