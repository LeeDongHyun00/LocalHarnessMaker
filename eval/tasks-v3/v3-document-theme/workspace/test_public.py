import unittest
from theme import stable_name
class PublicNames(unittest.TestCase):
    def test_same_url(self) -> None:
        self.assertEqual(stable_name('asset://logo'),stable_name('asset://logo'))
