import json
import unittest
from lockfile import resolve
class PublicLock(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(json.loads(resolve({},[])),{'packages':[]})
