import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'path': '/a', 'target': 'svc', 'priority': 1}]), {'rules': [{'path': '/a', 'target': 'svc', 'priority': 1}], 'targets': ['svc']})

if __name__ == '__main__':
    unittest.main()
