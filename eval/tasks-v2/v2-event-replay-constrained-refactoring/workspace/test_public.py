import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'id': 'sample', 'target': 'sample', 'value': 1}]), {'balances': {'sample': 1}, 'history': [1]})

if __name__ == '__main__':
    unittest.main()
