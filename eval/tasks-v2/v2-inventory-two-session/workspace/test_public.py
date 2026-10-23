import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'sku': 'A', 'location': 'X', 'delta': 2}]), {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 2}], 'totals': {'A': 2}})

if __name__ == '__main__':
    unittest.main()
