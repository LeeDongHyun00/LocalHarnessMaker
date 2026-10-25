from pathlib import Path
import tempfile
import unittest
from walkplan import walk
class PublicWalker(unittest.TestCase):
    def test_regular(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            Path(name, 'memo').write_text('public')
            self.assertEqual([(x.path, x.kind) for x in walk(name)], [('memo', 'file')])
