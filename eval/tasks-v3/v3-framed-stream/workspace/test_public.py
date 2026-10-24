import unittest
from framing import Decoder
class PublicWire(unittest.TestCase):
    def test_complete_read(self) -> None:
        delivered = []
        Decoder(delivered.append, print).feed(b'hello\r\n.\r\n')
        self.assertEqual(delivered, [b'hello'])
