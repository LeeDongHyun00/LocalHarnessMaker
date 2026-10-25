import tempfile
from pathlib import Path
import unittest
from copyplan import plan
class PublicCopy(unittest.TestCase):
    def test_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'src').mkdir()
            (root/'src'/'one.txt').write_text('one')
            self.assertEqual(plan(root/'src', root/'out').entries, ('one.txt',))
