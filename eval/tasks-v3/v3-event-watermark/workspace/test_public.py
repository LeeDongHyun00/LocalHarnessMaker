import unittest
from windows import Windows
class PublicWindows(unittest.TestCase):
    def test_add(self) -> None:
        w = Windows(4)
        self.assertIsNone(w.add(2, 3))
