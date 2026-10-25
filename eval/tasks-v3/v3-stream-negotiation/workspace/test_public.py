import unittest
from negotiation import Codec
class PublicTransport(unittest.TestCase):
    def test_text_payload(self) -> None:
        codec = Codec({'version': 1, 'capabilities': []})
        self.assertEqual(codec.decode(codec.encode('hello'))[0], 'hello')
