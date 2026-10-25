import unittest
from policy import Policy
class PublicPolicy(unittest.TestCase):
    def test_legacy(self) -> None:
        self.assertTrue(Policy({'version':1,'users':{'dev':['view']}}).allows('dev','view'))
