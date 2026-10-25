import unittest
from jobs import Job
class PublicJob(unittest.TestCase):
    def test_one_step(self) -> None:
        def factory():
            yield ('hello', 7)
        job = Job('public', factory, lambda key, value: value)
        self.assertTrue(job.step())
