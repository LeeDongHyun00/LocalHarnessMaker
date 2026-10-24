import sqlite3
import unittest
from unitwork import UnitOfWork
class PublicTransaction(unittest.TestCase):
    def test_commit(self) -> None:
        db = sqlite3.connect(':memory:', isolation_level=None)
        db.execute('CREATE TABLE sample(n)')
        with UnitOfWork(db):
            db.execute('INSERT INTO sample VALUES (5)')
        self.assertEqual(db.execute('SELECT n FROM sample').fetchall(), [(5,)])
        db.close()
