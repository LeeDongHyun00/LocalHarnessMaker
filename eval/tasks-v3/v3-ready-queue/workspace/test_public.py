import unittest
from ready import ReadyQueue
class PublicReady(unittest.TestCase):
    def test_single(self) -> None:
        queue = ReadyQueue()
        queue.push('work',1,'payload')
        self.assertEqual(queue.pop(), ('work','payload'))
