import unittest
from datetime import date
from shifts import Shift, compile_shifts
class PublicWeek(unittest.TestCase):
    def test_one_monday(self) -> None:
        result=compile_shifts([Shift('desk',0,540,600)],{},date(2024,1,1),date(2024,1,2))
        self.assertEqual(result[0][2],'desk')
