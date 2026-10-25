import unittest
from logsink import Sink
class PublicLog(unittest.TestCase):
    def test_flush(self) -> None:
        batches=[]
        sink=Sink(batches.append)
        sink.emit('info','hello'); sink.flush()
        self.assertEqual(batches,[(b'INFO: hello\n',)])
