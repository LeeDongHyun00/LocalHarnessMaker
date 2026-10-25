import io
import tarfile
import unittest
from unpack import extract
class PublicArchive(unittest.TestCase):
    def test_empty_preview(self) -> None:
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w'): pass
        buffer.seek(0)
        self.assertEqual(extract(buffer,'unused',max_files=0,max_bytes=0,dry_run=True)['files'],0)
