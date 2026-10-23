import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' P1 ', 'account': ' Straße ', 'amount': 100},
            {'id': 'p2', 'account': ' CASH ', 'amount': -4},
            {'id': 'p1', 'account': 'STRASSE', 'amount': 0},
            {'id': 'P2', 'account': 'cash', 'amount': 4},
            {'id': 'p3', 'account': 'cash', 'amount': -4},
            {'id': 'p1', 'account': 'strasse', 'amount': 0},
        ]
        expected = {
            'entries': [
                {'id': 'p1', 'account': 'strasse', 'amount': 0},
                {'id': 'p2', 'account': 'cash', 'amount': 4},
                {'id': 'p3', 'account': 'cash', 'amount': -4},
            ],
            'balances': {'cash': 0, 'strasse': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['cash', 'strasse'])
        self.assertEqual(normalize(' Straße '), 'strasse')

    def test_invalid_inputs_across_entry_points(self):
        class IntSubclass(int):
            pass

        invalid_rows = [
            None, [], {},
            {'id': 'x', 'account': 'a'},
            {'id': 'x', 'account': 'a', 'amount': 1, 'extra': 2},
        ]
        for field, values in (
            ('id', [None, 1, '', ' \t\n']),
            ('account', [None, 1, '', ' \t\n']),
            ('amount', [True, False, 1.0, '1', None, IntSubclass(1)]),
        ):
            for value in values:
                row = {'id': 'x', 'account': 'a', 'amount': 1}
                row[field] = value
                invalid_rows.append(row)
        for function in (validate, compute, run, render):
            for value in (None, {}, (), 'rows', iter([])):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                        function(value)
            for row in invalid_rows:
                with self.subTest(function=function.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        function([row])

    def test_validation_precedes_domain_conflicts(self):
        conflict = [
            {'id': ' X ', 'account': 'a', 'amount': 1},
            {'id': 'x', 'account': 'b', 'amount': 2},
        ]
        for function in (compute, run, render, lambda rows: run_many([[], rows]),
                         lambda rows: render_many([[], rows])):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                function(conflict)
            rows = conflict + [{'id': 'bad', 'account': 'a', 'amount': True}]
            original = copy.deepcopy(rows)
            with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                function(rows)
            self.assertEqual(rows, original)

    def test_render_format(self):
        rows = [{'id': ' É\"\\\nX ', 'account': ' 한글 ', 'amount': -2}]
        expected = {'entries': [{'id': 'é\"\\\nx', 'account': '한글', 'amount': -2}],
                    'balances': {'한글': -2}}
        text = render(rows)
        self.assertEqual(text, json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                          separators=(',', ':')) + '\n')
        self.assertEqual(json.loads(text), run(rows))
        self.assertEqual(text.count('\n'), 1)

    def test_batches_and_empty_inputs(self):
        rows = [{'id': ' X ', 'account': ' A ', 'amount': 2}]
        batches = [rows, [], rows]
        self.assertEqual(run_many(batches), [run(rows), run([]), run(rows)])
        self.assertEqual(render_many(batches), render(rows) + render([]) + render(rows))
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for function in (run_many, render_many):
            for value in (None, {}, (), 'batches'):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    function(value)
            original = copy.deepcopy(batches)
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                function(batches + [None])
            self.assertEqual(batches, original)

    def test_subclasses_and_result_isolation(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' X ', account=' A ', amount=2)])
        original = copy.deepcopy(rows)
        validated = validate(rows)
        self.assertEqual(validated, [{'id': 'x', 'account': 'a', 'amount': 2}])
        validated[0]['amount'] = 99
        result = run_many(Rows([rows, rows]))
        result[0]['entries'][0]['amount'] = 99
        result[0]['entries'].append({})
        result[0]['balances']['a'] = 99
        self.assertEqual(result[1], run(rows))
        expected = {'entries': [{'id': 'x', 'account': 'a', 'amount': 2}],
                    'balances': {'a': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        empty = run_many([[], []])
        empty[0]['entries'].append({})
        empty[0]['balances']['x'] = 1
        self.assertEqual(empty[1], {'entries': [], 'balances': {}})


if __name__ == '__main__':
    unittest.main()
