import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'id': 'p1', 'account': 'cash', 'amount': 2}]), {'entries': [{'id': 'p1', 'account': 'cash', 'amount': 2}], 'balances': {'cash': 2}})

if __name__ == '__main__':
    unittest.main()
