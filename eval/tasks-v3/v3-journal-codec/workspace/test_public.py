import io
import unittest
import journal
class PublicJournal(unittest.TestCase):
    def test_roundtrip(self) -> None:
        stream = io.BytesIO()
        journal.append(stream, b'hello')
        stream.seek(0)
        self.assertEqual(journal.replay(stream), [b'hello'])
