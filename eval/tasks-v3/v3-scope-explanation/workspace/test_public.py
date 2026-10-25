import unittest
from access import Policy, Rule
class PublicAccess(unittest.TestCase):
    def test_direct(self) -> None:
        self.assertTrue(Policy({}, [Rule('reader', 'memo', 'allow')]).allows(['reader'], 'memo'))
