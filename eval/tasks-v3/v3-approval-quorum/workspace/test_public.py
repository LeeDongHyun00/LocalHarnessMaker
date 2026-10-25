import unittest
from approval import Approval
class PublicApproval(unittest.TestCase):
    def test_initial(self) -> None:
        form = Approval('owner', {'owner':'review','guest':'review'}, {'review':2})
        self.assertEqual((form.status, form.counts()), ('pending', {'review':0}))
