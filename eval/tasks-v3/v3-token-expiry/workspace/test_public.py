import unittest
from tokens import TokenService
class PublicTokens(unittest.TestCase):
    def test_unexpired(self) -> None:
        service = TokenService(b'demo-secret', lambda: 3)
        self.assertEqual(service.verify(service.issue('reader', 90))['sub'], 'reader')
