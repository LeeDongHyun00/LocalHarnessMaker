import unittest
from buildplan import plan
class PublicBuild(unittest.TestCase):
    def test_first_build(self) -> None:
        self.assertEqual(plan({}, {'program':[]}, {}, {}), ['program'])
