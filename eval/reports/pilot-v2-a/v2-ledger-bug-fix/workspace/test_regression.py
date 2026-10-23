import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' Straße ', 'account': ' CASH ', 'amount': -2},
            {'id': 'STRASSE', 'account': 'cash', 'amount': -2},
            {'id': 'second', 'account': 'Cash', 'amount': 2},
            {'id': 'third', 'account': ' BANK ', 'amount': 0},
        ]
        expected = {
            'entries': [
                {'id': 'strasse', 'account': 'cash', 'amount': -2},
                {'id': 'second', 'account': 'cash', 'amount': 2},
                {'id': 'third', 'account': 'bank', 'amount': 0},
            ],
            'balances': {'bank': 0, 'cash': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['bank', 'cash'])
        self.assertEqual(compute(rows), expected)
        self.assertEqual(normalize(' Straße '), 'strasse')

    def test_duplicate_conflicts(self):
        for replacement in (
            {'id': ' A ', 'account': 'bank', 'amount': 1},
            {'id': ' A ', 'account': 'cash', 'amount': 2},
        ):
            rows = [{'id': 'a', 'account': 'cash', 'amount': 1}, replacement]
            for api in (run, compute, render):
                with self.subTest(api=api.__name__, replacement=replacement):
                    with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                        api(rows)

    def test_invalid_fields_precede_domain_errors(self):
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {},
                        {'id': 'a', 'account': 'cash'},
                        {'id': 'a', 'account': 'cash', 'amount': 1, 'extra': 0}]
        for field, values in (
            ('id', ['', ' \t', 1, None]),
            ('account', ['', ' \n', False, None]),
            ('amount', [True, False, IntSubclass(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'id': 'a', 'account': 'cash', 'amount': 1}
                row[field] = value
                invalid_rows.append(row)
        for invalid in invalid_rows:
            rows = [{'id': 'a', 'account': 'cash', 'amount': 1},
                    {'id': 'A', 'account': 'cash', 'amount': 2}, invalid]
            before = copy.deepcopy(rows)
            for api in (run, compute, validate, render):
                with self.subTest(api=api.__name__, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api(rows)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    api([[], rows])
            self.assertEqual(rows, before)

    def test_input_boundaries_and_subclasses(self):
        for value in (None, (), {}, '', iter([])):
            for api in (run, compute, validate, render):
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    api(value)
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    api([[], value])

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        rows = ListSubclass([DictSubclass(id=' A ', account=' CASH ', amount=0)])
        expected = {'entries': [{'id': 'a', 'account': 'cash', 'amount': 0}],
                    'balances': {'cash': 0}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(ListSubclass([rows])), [expected])

    def test_unicode_rendering_and_batch_order(self):
        rows = [{'id': ' Z"\nX ', 'account': ' CAFÉ ', 'amount': -1}]
        expected = '{"balances":{"café":-1},"entries":[{"account":"café","amount":-1,"id":"z\\"\\nx"}]}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, []]), expected + '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([rows, []]), [run(rows), run([])])
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_results_and_no_input_mutation(self):
        rows = [{'id': ' A ', 'account': ' CASH ', 'amount': 1}]
        before = copy.deepcopy(rows)
        expected = {'entries': [{'id': 'a', 'account': 'cash', 'amount': 1}],
                    'balances': {'cash': 1}}
        results = run_many([rows, rows])
        results[0]['entries'][0]['amount'] = 99
        results[0]['entries'].append({})
        results[0]['balances']['cash'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        validated[0]['account'] = 'changed'
        render(rows)
        render_many([rows, rows])
        self.assertEqual(rows, before)
        conflict = rows + [{'id': 'a', 'account': 'cash', 'amount': 2}]
        conflict_before = copy.deepcopy(conflict)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                api([rows, conflict])
            self.assertEqual(conflict, conflict_before)
            self.assertEqual(rows, before)
            self.assertEqual(run_many([rows]), [expected])


if __name__ == '__main__':
    unittest.main()
