import unittest
from inspection import inspect_config
class PublicInspector(unittest.TestCase):
    def test_scalar(self) -> None:
        self.assertEqual(inspect_config(7,[]),[{'path':'','value':7,'secret':False}])
