import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'id': 'sample', 'target': 'sample', 'value': 1}]), {'index': {'sample': {'count': 1, 'documents': ['sample']}}})

if __name__ == '__main__':
    unittest.main()
