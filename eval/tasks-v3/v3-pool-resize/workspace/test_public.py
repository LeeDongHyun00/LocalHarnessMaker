import unittest
from workers import WorkerPool
class PublicWorkers(unittest.TestCase):
    def test_single_lease(self) -> None:
        pool = WorkerPool(1, lambda *_: None)
        lease = pool.acquire('job')
        self.assertEqual((lease,pool.release(lease)), (1,True))
