import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class LedgerRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' Straße ', 'account': ' CASH ', 'amount': 2},
            {'id': 'STRASSE', 'account': 'cash', 'amount': 2},
            {'id': 'second', 'account': 'Cash', 'amount': -2},
            {'id': 'third', 'account': ' Alpha ', 'amount': 0},
        ]
        expected = {
            'entries': [
                {'id': 'strasse', 'account': 'cash', 'amount': 2},
                {'id': 'second', 'account': 'cash', 'amount': -2},
                {'id': 'third', 'account': 'alpha', 'amount': 0},
            ],
            'balances': {'alpha': 0, 'cash': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['alpha', 'cash'])
        self.assertEqual(compute(rows), expected)
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(validate(rows)[0], expected['entries'][0])

    def test_conflicting_canonical_ids(self):
        first = {'id': ' X ', 'account': 'cash', 'amount': 2}
        for change in ({'amount': 3}, {'account': 'bank'}):
            rows = [first, dict(first, id='x', **change)]
            before = copy.deepcopy(rows)
            for api in (run, compute, render):
                with self.subTest(api=api.__name__, change=change):
                    with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_field_errors_precede_conflicts(self):
        rows = [
            {'id': 'x', 'account': 'cash', 'amount': 1},
            {'id': 'x', 'account': 'cash', 'amount': 2},
            {'id': 'bad', 'account': 'cash', 'amount': True},
        ]
        before = copy.deepcopy(rows)
        for api in (run, compute, render, validate):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    api(rows)
                self.assertEqual(rows, before)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                api([[], rows])

    def test_invalid_rows(self):
        class IntSubclass(int):
            pass

        base = {'id': 'x', 'account': 'cash', 'amount': 1}
        invalid = [None, [], {}, dict(base, extra=1)]
        invalid += [{k: v for k, v in base.items() if k != field} for field in base]
        for field in ('id', 'account'):
            invalid += [dict(base, **{field: value}) for value in (None, 1, '', ' \t\n')]
        invalid += [dict(base, amount=value) for value in (True, False, 1.0, '1', None, IntSubclass(1))]
        for row in invalid:
            for api in (run, compute, render, validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api([row])

    def test_container_boundaries(self):
        for value in (None, (), {}, 'rows', iter([])):
            for api in (run, compute, render, validate):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                        api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    api(value)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                api([[], ()])

    def test_subclasses_and_empty_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' X ', account=' CASH ', amount=-1)])
        self.assertEqual(run(rows), {'entries': [{'id': 'x', 'account': 'cash', 'amount': -1}], 'balances': {'cash': -1}})
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many(Rows()), [])
        self.assertEqual(render_many(Rows()), '')

    def test_unicode_json_and_batch_order(self):
        rows = [{'id': ' É"\nZ ', 'account': ' CAFÉ ', 'amount': 0}]
        expected = '{"balances":{"café":0},"entries":[{"account":"café","amount":0,"id":"é\\"\\nz"}]}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(run_many([rows, []]), [run(rows), run([])])
        self.assertEqual(render_many([rows, []]), expected + render([]))

    def test_results_are_fresh_and_inputs_unchanged(self):
        rows = [{'id': ' X ', 'account': ' CASH ', 'amount': 1}]
        before = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['entries'][0]['amount'] = 99
        results[0]['entries'].append({})
        results[0]['balances']['cash'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        render_many([rows, rows])
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['entries'].append({})
        empty[0]['balances']['x'] = 1
        self.assertEqual(empty[1], {'entries': [], 'balances': {}})

    def test_batch_failure_has_no_state(self):
        valid = [{'id': 'x', 'account': 'cash', 'amount': 1}]
        conflict = valid + [{'id': 'X', 'account': 'cash', 'amount': 2}]
        batches = [valid, conflict, []]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                api(batches)
            self.assertEqual(batches, before)
        self.assertEqual(run_many([valid, valid]), [run(valid), run(valid)])


if __name__ == '__main__':
    unittest.main()
