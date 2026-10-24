import unittest
from cycles import find_cycle
class PublicCycle(unittest.TestCase):
    def test_loop(self) -> None:
        self.assertEqual(find_cycle({'loop':['loop']}), ['loop','loop'])
