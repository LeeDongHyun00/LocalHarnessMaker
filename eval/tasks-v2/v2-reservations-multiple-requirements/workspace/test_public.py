import unittest
from project import run

class PublicTests(unittest.TestCase):
    def test_existing_example(self) -> None:
        self.assertEqual(run([{'id': 'b1', 'resource': 'room', 'start': 1, 'end': 2}]), {'bookings': [{'id': 'b1', 'resource': 'room', 'start': 1, 'end': 2}], 'resources': ['room']})

if __name__ == '__main__':
    unittest.main()
