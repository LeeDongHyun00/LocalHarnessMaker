import unittest
from routes import route
class PublicRoute(unittest.TestCase):
    def test_edge(self) -> None:
        self.assertEqual(route({'a':['b']},'a','b'),['a','b'])
