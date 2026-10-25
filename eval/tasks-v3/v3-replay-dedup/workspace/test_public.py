import tempfile
from pathlib import Path
import unittest
from replay import Log
class PublicLog(unittest.TestCase):
    def test_put(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log=Log(Path(directory)/'rows')
            log.append({'id':'1','key':'x','op':'put','value':'hello'})
            self.assertEqual(log.replay(),{'x':'hello'})
