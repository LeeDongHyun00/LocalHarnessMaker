import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.validation import validate


class BatchRegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'id': ' P1 ', 'account': ' Straße ', 'amount': 2},
            {'id': 'p1', 'account': 'STRASSE', 'amount': 2},
            {'id': 'P2', 'account': 'strasse', 'amount': -2},
        ]
        expected = {
            'entries': [
                {'id': 'p1', 'account': 'strasse', 'amount': 2},
                {'id': 'p2', 'account': 'strasse', 'amount': -2},
            ],
            'balances': {'strasse': 0},
        }
        self.assertEqual(run_many([rows, []]), [expected, {'entries': [], 'balances': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_errors_and_atomicity(self):
        conflict = [
            {'id': 'x', 'account': 'a', 'amount': 1},
            {'id': ' X ', 'account': 'b', 'amount': 1},
        ]
        valid = [{'id': 'ok', 'account': 'a', 'amount': 0}]
        for api in (run_many, render_many):
            for value in (None, {}, (), 'rows'):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    api(value)
            batches = [valid, conflict]
            original = copy.deepcopy(batches)
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                api(batches)
            self.assertEqual(batches, original)
            with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                api([conflict + [{'id': 'bad', 'account': 'a', 'amount': True}]])
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                api([valid, ()])

    def test_validation_contract(self):
        class IntSubclass(int):
            pass

        invalid = [
            None, {}, {'id': 'x', 'account': 'a', 'amount': 1, 'extra': 0},
            {'id': ' ', 'account': 'a', 'amount': 1},
            {'id': 1, 'account': 'a', 'amount': 1},
            {'id': 'x', 'account': '\t', 'amount': 1},
            {'id': 'x', 'account': None, 'amount': 1},
        ]
        invalid += [{'id': 'x', 'account': 'a', 'amount': amount}
                    for amount in (True, IntSubclass(1), 1.0, '1', None)]
        for api in (validate, compute, run, render):
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                api(())
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api([row])

    def test_fresh_results_and_order(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' Z ', account=' Z ', amount=0),
                     Row(id=' A ', account=' A ', amount=-1)])
        original = copy.deepcopy(rows)
        expected = run(rows)
        self.assertEqual(list(expected['balances']), ['a', 'z'])
        self.assertEqual([row['id'] for row in expected['entries']], ['z', 'a'])
        results = run_many(Rows([rows, rows]))
        results[0]['entries'][0]['id'] = 'changed'
        results[0]['entries'].append({})
        results[0]['balances']['z'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(rows, original)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows])[0], expected)

    def test_render_format(self):
        rows = [{'id': ' É ', 'account': ' B"\nC ', 'amount': -1}]
        expected = ('{"balances":{"b\\"\\nc":-1},"entries":'
                    '[{"account":"b\\"\\nc","amount":-1,"id":"é"}]}\n')
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, rows]), expected + expected)
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')


if __name__ == '__main__':
    unittest.main()
