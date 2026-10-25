import json
from pathlib import Path
import tempfile
import unittest
from buildtool import build
class PublicBuild(unittest.TestCase):
    def test_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'one.src').write_text('x')
            (root/'manifest.json').write_text(json.dumps({'jobs':[{'name':'one','source':'one.src'}]}))
            calls=[]
            build(root,'out',lambda *a,**k:calls.append(a))
            self.assertEqual(len(calls),1)
