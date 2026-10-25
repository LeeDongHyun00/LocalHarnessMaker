import unittest
from commands import History

class PublicHistory(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertFalse(History().undo())
