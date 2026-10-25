import unittest
from components import Graph
class PublicComponents(unittest.TestCase):
    def test_isolated(self) -> None:
        self.assertEqual(Graph(['a'],[]).condensation()['components'],[('a',)])
