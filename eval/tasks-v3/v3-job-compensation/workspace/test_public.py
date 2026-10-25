import unittest
from jobs import Runner
class PublicJob(unittest.TestCase):
    def test_one_step(self) -> None:
        runner=Runner('unused.json',lambda step,key:step.upper(),lambda *args:None)
        self.assertEqual(runner.run('demo',['hello'])['state'],'succeeded')
