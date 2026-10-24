import unittest
from records import Reader
class PublicRecords(unittest.TestCase):
    def test_plain_row(self) -> None:
        record = Reader('one,two\n').read()
        self.assertEqual(record.fields, ['one','two'])
