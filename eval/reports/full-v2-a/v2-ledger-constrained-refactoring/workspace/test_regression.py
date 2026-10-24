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
            {'id': ' P1 ', 'account': ' CASH ', 'amount': 2},
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'p2', 'account': 'Cash', 'amount': -2},
            {'id': 'p3', 'account': 'bank', 'amount': 0},
        ]
        result = run(rows)
        self.assertEqual(result['entries'], [
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'p2', 'account': 'cash', 'amount': -2},
            {'id': 'p3', 'account': 'bank', 'amount': 0},
        ])
        self.assertEqual(list(result['balances'].items()), [('bank', 0), ('cash', 0)])
        with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
            run(rows + [{'id': 'P1', 'account': 'cash', 'amount': 3}])

    def test_runtime_normalization(self):
        rows = [{'id': ' A ', 'account': ' B ', 'amount': 1}]
        expected = {'entries': [{'id': 'new:a', 'account': 'new:b', 'amount': 1}],
                    'balances': {'new:b': 1}}
        encoded = json.dumps(expected, sort_keys=True, separators=(',', ':')) + '\n'
        for api, argument, output in (
            (run, rows, expected), (compute, rows, expected),
            (validate, rows, expected['entries']), (render, rows, encoded),
            (run_many, [rows, rows], [expected, expected]),
            (render_many, [rows, rows], encoded + encoded),
        ):
            with self.subTest(api=api.__name__):
                with patch('project.policy.normalize', side_effect=lambda value: 'new:' + normalize(value)) as patched:
                    self.assertEqual(api(argument), output)
                    self.assertEqual(patched.call_count, 4 if api in (run_many, render_many) else 2)

    def test_validation_and_error_precedence(self):
        class IntSubclass(int):
            pass

        good = {'id': 'x', 'account': 'cash', 'amount': 1}
        conflict = dict(good, amount=2)
        invalid = [None, [], {}, dict(good, extra=1)]
        for field, values in (
            ('id', [None, 1, '', ' \t']),
            ('account', [None, 1, '', '\n ']),
            ('amount', [True, False, 1.0, '1', IntSubclass(1)]),
        ):
            invalid.extend(dict(good, **{field: value}) for value in values)
        invalid.extend({key: value for key, value in good.items() if key != field} for field in good)
        for row in invalid:
            rows = [good, conflict, row]
            before = copy.deepcopy(rows)
            for api, argument in ((run, rows), (render, rows),
                                  (run_many, [[good], rows]), (render_many, [[good], rows])):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api(argument)
                    self.assertEqual(rows, before)
        for value in (None, (), {}, 'rows', iter([])):
            for api in (run, render, compute, validate):
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    api(value)

    def test_fresh_results_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' X ', account=' Cash ', amount=1)])
        before = copy.deepcopy(rows)
        results = run_many(Rows([rows, rows]))
        expected = run(rows)
        results[0]['entries'][0]['account'] = 'changed'
        results[0]['balances']['cash'] = 99
        results[0]['entries'].append({})
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        self.assertIsNot(validate(rows)[0], rows[0])
        with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
            run_many([rows, rows + [dict(rows[0], amount=2)]])
        self.assertEqual(rows, before)

    def test_rendering_and_empty_inputs(self):
        rows = [{'id': ' STRAẞE ', 'account': ' É\"\n ', 'amount': -1}]
        expected = {'entries': [{'id': 'strasse', 'account': 'é"', 'amount': -1}],
                    'balances': {'é"': -1}}
        self.assertEqual(run(rows), expected)
        encoded = '{"balances":{"é\\\"":-1},"entries":[{"account":"é\\\"","amount":-1,"id":"strasse"}]}\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, []]), encoded + render([]))
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
