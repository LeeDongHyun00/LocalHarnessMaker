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
            {'id': ' P1 ', 'account': ' CASH ', 'amount': 2},
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'P2', 'account': 'Cash', 'amount': -2},
        ]
        expected = {
            'entries': [
                {'id': 'p1', 'account': 'cash', 'amount': 2},
                {'id': 'p2', 'account': 'cash', 'amount': -2},
            ],
            'balances': {'cash': 0},
        }
        self.assertEqual(run_many([rows, []]), [expected, {'entries': [], 'balances': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_errors_and_precedence(self):
        conflict = [
            {'id': 'x', 'account': 'a', 'amount': 1},
            {'id': ' X ', 'account': 'b', 'amount': 1},
        ]
        for api in (run, render, compute, run_many, render_many):
            for rows, message in ((conflict, 'ledger: duplicate id'),
                                  (conflict + [{}], 'ledger: invalid row')):
                argument = [[], rows] if api in (run_many, render_many) else rows
                original = copy.deepcopy(argument)
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^' + message + '$'):
                        api(argument)
                    self.assertEqual(argument, original)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                api(())
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                api([[], ()])

    def test_validation_contract(self):
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        valid = DictSubclass(id=' A ', account=' STRASSE ', amount=0)
        self.assertEqual(run(ListSubclass([valid]))['balances'], {'strasse': 0})
        invalid_rows = [None, {}, dict(valid, extra=1), dict(valid, id=' '),
                        dict(valid, account=3), dict(valid, amount=True),
                        dict(valid, amount=IntSubclass(1)), dict(valid, amount=1.0)]
        for row in invalid_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    validate([row])
        with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
            validate(())

    def test_fresh_results_and_unicode_rendering(self):
        rows = [
            {'id': ' Z ', 'account': ' Straße ', 'amount': -1},
            {'id': ' A ', 'account': ' É ', 'amount': 0},
        ]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['entries'][0]['account'] = 'changed'
        results[0]['entries'].append({})
        results[0]['balances']['strasse'] = 99
        self.assertEqual(rows, original)
        self.assertEqual(results[1], expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(list(expected['balances']), ['strasse', 'é'])
        self.assertEqual([row['id'] for row in expected['entries']], ['z', 'a'])
        self.assertEqual(
            render_many([rows]),
            '{"balances":{"strasse":-1,"é":0},"entries":'
            '[{"account":"strasse","amount":-1,"id":"z"},'
            '{"account":"é","amount":0,"id":"a"}]}\n',
        )


if __name__ == '__main__':
    unittest.main()
