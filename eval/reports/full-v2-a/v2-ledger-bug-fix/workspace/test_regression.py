import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class LedgerRegressionTests(unittest.TestCase):
    def assert_error(self, error_type, message, function, value):
        with self.assertRaises(error_type) as caught:
            function(value)
        self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        rows = [
            {'id': ' StraßE ', 'account': ' CASH ', 'amount': -2},
            {'id': 'STRASSE', 'account': 'cash', 'amount': -2},
            {'id': 'next', 'account': 'Cash', 'amount': 2},
            {'id': 'zero', 'account': ' Alpha ', 'amount': 0},
        ]
        expected = {
            'entries': [
                {'id': 'strasse', 'account': 'cash', 'amount': -2},
                {'id': 'next', 'account': 'cash', 'amount': 2},
                {'id': 'zero', 'account': 'alpha', 'amount': 0},
            ],
            'balances': {'alpha': 0, 'cash': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['alpha', 'cash'])
        self.assertEqual(normalize(' StraßE '), 'strasse')
        self.assertEqual(validate(rows)[0], expected['entries'][0])

    def test_duplicate_conflicts(self):
        first = {'id': ' A ', 'account': 'cash', 'amount': 1}
        for second in (
            {'id': 'a', 'account': 'bank', 'amount': 1},
            {'id': 'a', 'account': 'cash', 'amount': -1},
        ):
            for function in (run, compute, render):
                self.assert_error(ValueError, 'ledger: duplicate id', function,
                                  [first, second])

    def test_validation_precedes_domain_errors(self):
        conflicting = [
            {'id': 'a', 'account': 'cash', 'amount': 1},
            {'id': 'a', 'account': 'cash', 'amount': 2},
            {'id': 'bad', 'account': 'cash', 'amount': True},
        ]
        for function in (run, compute, render, validate):
            self.assert_error(ValueError, 'ledger: invalid row', function, conflicting)
        for function in (run_many, render_many):
            self.assert_error(ValueError, 'ledger: invalid row', function,
                              [[], conflicting])

    def test_shape_and_field_boundaries(self):
        class Integer(int):
            pass

        valid = {'id': 'a', 'account': 'cash', 'amount': 1}
        invalid = [None, [], {}, dict(valid, extra=1)]
        for key in valid:
            invalid.append({k: v for k, v in valid.items() if k != key})
        for key in ('id', 'account'):
            for value in (None, 1, True, [], '', ' \t\n'):
                invalid.append(dict(valid, **{key: value}))
        for value in (True, False, Integer(1), 1.0, '1', None):
            invalid.append(dict(valid, amount=value))
        for function in (run, compute, render, validate):
            for rows in (None, (), {}, 'rows', iter([])):
                self.assert_error(TypeError, 'ledger: rows must be a list', function, rows)
            for row in invalid:
                self.assert_error(ValueError, 'ledger: invalid row', function, [row])

    def test_container_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' A ', account=' Cash ', amount=0)])
        self.assertEqual(run(rows), {
            'entries': [{'id': 'a', 'account': 'cash', 'amount': 0}],
            'balances': {'cash': 0},
        })
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_unicode_rendering(self):
        rows = [{'id': ' É\"\\\n ', 'account': ' 한글 ', 'amount': -1}]
        expected = ('{"balances":{"한글":-1},"entries":'
                    '[{"account":"한글","amount":-1,"id":"é\\\"\\\\"}]}\n')
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_empty_and_batch_order(self):
        a = [{'id': 'same', 'account': 'z', 'amount': 1}]
        b = [{'id': 'SAME', 'account': 'a', 'amount': -1}]
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run_many([a, [], b]), [run(a), run([]), run(b)])
        self.assertEqual(render_many([a, [], b]), render(a) + render([]) + render(b))
        for function in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                self.assert_error(TypeError, 'ledger: batches must be a list',
                                  function, batches)
            self.assert_error(TypeError, 'ledger: rows must be a list', function, [a, ()])
            self.assert_error(ValueError, 'ledger: duplicate id', function,
                              [a, a + [dict(a[0], amount=2)]])

    def test_input_and_result_isolation(self):
        rows = [{'id': ' A ', 'account': ' CASH ', 'amount': 1}]
        original = copy.deepcopy(rows)
        result = run_many([rows, rows])
        result[0]['entries'][0]['amount'] = 99
        result[0]['entries'].append({})
        result[0]['balances']['cash'] = 99
        self.assertEqual(result[1], run(rows))
        self.assertEqual(rows, original)
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        for function in (run, compute, render):
            function(rows)
            self.assertEqual(rows, original)
        for tail, message in (([dict(rows[0], amount=2)], 'ledger: duplicate id'),
                              ([{'nested': {'values': []}}], 'ledger: invalid row')):
            failing = rows + tail
            snapshot = copy.deepcopy(failing)
            for function in (run, compute, render):
                self.assert_error(ValueError, message, function, failing)
                self.assertEqual(failing, snapshot)
            for function in (run_many, render_many):
                self.assert_error(ValueError, message, function, [rows, failing])
                self.assertEqual(failing, snapshot)
                self.assertEqual(rows, original)


if __name__ == '__main__':
    unittest.main()
