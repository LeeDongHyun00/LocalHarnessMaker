import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' First ', 'account': ' CASH ', 'amount': 3},
            {'id': 'FIRST', 'account': 'cash', 'amount': 3},
            {'id': 'second', 'account': 'Cash', 'amount': -3},
            {'id': 'third', 'account': 'asset', 'amount': 0},
        ]
        self.assertEqual(run(rows), {
            'entries': [
                {'id': 'first', 'account': 'cash', 'amount': 3},
                {'id': 'second', 'account': 'cash', 'amount': -3},
                {'id': 'third', 'account': 'asset', 'amount': 0},
            ],
            'balances': {'asset': 0, 'cash': 0},
        })
        self.assertEqual(list(run(rows)['balances']), ['asset', 'cash'])

    def test_runtime_policy_for_all_entry_points(self):
        rows = [{'id': ' A ', 'account': ' CASH ', 'amount': 2}]
        expected = {
            'entries': [{'id': 'patched:a', 'account': 'patched:cash', 'amount': 2}],
            'balances': {'patched:cash': 2},
        }
        encoded = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        cases = (
            (run, rows, expected), (render, rows, encoded),
            (run_many, [rows], [expected]), (render_many, [rows], encoded),
            (compute, rows, expected), (validate, rows, expected['entries']),
        )
        for function, argument, result in cases:
            with self.subTest(function=function.__name__):
                with patch('project.policy.normalize', side_effect=lambda value: 'patched:' + normalize(value)) as mocked:
                    self.assertEqual(function(argument), result)
                    self.assertEqual(mocked.call_args_list, [unittest.mock.call(' A '), unittest.mock.call(' CASH ')])

    def test_invalid_rows_precede_duplicate_conflicts(self):
        conflicts = [
            {'id': 'same', 'account': 'cash', 'amount': 1},
            {'id': ' SAME ', 'account': 'cash', 'amount': 2},
        ]
        for function in (run, render, compute):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    function(conflicts + [{'id': 'bad', 'account': ' ', 'amount': 1}])
                with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                    function(conflicts)
        for function in (run_many, render_many):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    function([[], conflicts + [{}]])

    def test_input_contract(self):
        class IntSubclass(int):
            pass

        row = {'id': 'a', 'account': 'cash', 'amount': 1}
        invalid = [None, [], {}, dict(row, extra=1)]
        for field, values in (
            ('id', [None, 1, '', ' \t\n']),
            ('account', [None, 1, '', ' \t\n']),
            ('amount', [True, False, 1.0, '1', IntSubclass(1)]),
        ):
            invalid.extend(dict(row, **{field: value}) for value in values)
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    run([candidate])
        for function in (run, render, compute, validate):
            for argument in (None, {}, (), iter([]), ''):
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    function(argument)
        for function in (run_many, render_many):
            for argument in (None, {}, (), iter([]), ''):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    function(argument)
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                function([[], ()])

    def test_subclasses_unicode_and_render_format(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' Straße ', account=' 한글\n" ', amount=-2)])
        expected = {
            'entries': [{'id': 'strasse', 'account': '한글\n"', 'amount': -2}],
            'balances': {'한글\n"': -2},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(render(rows), '{"balances":{"한글\\n\\\"":-2},"entries":[{"account":"한글\\n\\\"","amount":-2,"id":"strasse"}]}\n')

    def test_fresh_results_and_atomic_batches(self):
        rows = [{'id': ' A ', 'account': ' Cash ', 'amount': 1}]
        original = copy.deepcopy(rows)
        batches = [rows, rows]
        results = run_many(batches)
        expected = copy.deepcopy(results[1])
        results[0]['entries'][0]['id'] = 'changed'
        results[0]['entries'].append({})
        results[0]['balances']['cash'] = 10
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        self.assertEqual(render_many(batches), render(rows) * 2)
        failing = [rows, [{'id': 'x', 'account': 'cash', 'amount': 1}, {}]]
        before = copy.deepcopy(failing)
        for function in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                function(failing)
            self.assertEqual(failing, before)

    def test_empty_results(self):
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
