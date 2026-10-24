import unittest
from timers import Timers
class PublicTimer(unittest.TestCase):
    def test_simple_poll(self) -> None:
        calls = []
        timers = Timers(lambda: 1)
        timers.call_at(0, lambda: calls.append('done'))
        self.assertEqual(timers.run_due(), 1)
        self.assertEqual(calls, ['done'])
