import unittest
from traces import Collector
class PublicTrace(unittest.TestCase):
    def test_single_root(self) -> None:
        collector=Collector(100)
        collector.accept({'trace':'demo','id':'root','parent':None,'start':0,'end':1})
        self.assertEqual(len(collector.export()),1)
