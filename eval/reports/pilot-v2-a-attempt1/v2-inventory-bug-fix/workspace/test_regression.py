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
            {'sku': ' a ', 'location': ' x ', 'delta': -2},
            {'sku': 'A', 'location': 'X', 'delta': 2},
        ]
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
                    'totals': {'A': 0}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(normalize(' a '), 'A')

    def test_boundaries_and_error_precedence(self):
        class IntSubclass(int):
            pass

        bad_rows = [None, [], {},
                    {'sku': 'A', 'location': 'X'},
                    {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 0}]
        for field, values in [('sku', [None, 1, ' \t']),
                              ('location', [None, 1, ' \n']),
                              ('delta', [True, False, 1.0, '1', IntSubclass(1)])]:
            for value in values:
                row = {'sku': 'A', 'location': 'X', 'delta': 1}
                row[field] = value
                bad_rows.append(row)
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        for bad in bad_rows:
            for operation in (run, compute, validate, render):
                with self.subTest(bad=bad, operation=operation):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        operation([negative, bad])
        for operation in (run, compute, validate, render):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    operation(rows)
        for operation in (run, compute, render):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                operation([negative])

    def test_subclasses_sorting_and_rendering(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' z ', location=' b ', delta=0),
                     Row(sku='é"', location='\t c\\ ', delta=2),
                     Row(sku='z', location='a', delta=3)])
        expected = {'stock': [{'sku': 'Z', 'location': 'A', 'quantity': 3},
                              {'sku': 'Z', 'location': 'B', 'quantity': 0},
                              {'sku': 'É"', 'location': 'C\\', 'quantity': 2}],
                    'totals': {'Z': 3, 'É"': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['totals']), ['Z', 'É"'])
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False,
                                                sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')

    def test_batches_and_isolation(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        self.assertEqual(results, [expected, expected])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        normalized = validate(rows)
        normalized[0]['sku'] = 'CHANGED'
        self.assertEqual(rows, original)
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for operation in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    operation(batches)
            for bad, error, message in [
                (None, TypeError, 'inventory: rows must be a list'),
                ([{}], ValueError, 'inventory: invalid row'),
                ([{'sku': 'a', 'location': 'x', 'delta': -1}],
                 ValueError, 'inventory: negative stock'),
            ]:
                batches = [rows, bad]
                before = copy.deepcopy(batches)
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    operation(batches)
                self.assertEqual(batches, before)
        self.assertEqual(rows, original)


if __name__ == '__main__':
    unittest.main()
