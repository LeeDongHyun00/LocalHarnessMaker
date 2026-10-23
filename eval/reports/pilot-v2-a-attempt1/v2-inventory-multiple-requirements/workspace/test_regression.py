import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def assert_error(self, function, value, kind, message):
        with self.assertRaises(kind) as caught:
            function(value)
        self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        cases = [
            [{'sku': 'a', 'location': 'x', 'delta': -1},
             {'sku': ' A ', 'location': ' X ', 'delta': 2}],
            [{'sku': 'A', 'location': 'X', 'delta': 5},
             {'sku': 'A', 'location': 'Y', 'delta': -1}],
            [{'sku': 'A', 'location': 'X', 'delta': 1},
             {'sku': ' a ', 'location': ' x ', 'delta': -2},
             {'sku': 'A', 'location': 'X', 'delta': 3}],
        ]
        for rows in cases:
            for function in (run, compute, render):
                with self.subTest(function=function, rows=rows):
                    self.assert_error(function, rows, ValueError,
                                      'inventory: negative stock')
            for function in (run_many, render_many):
                self.assert_error(function, [[], rows], ValueError,
                                  'inventory: negative stock')

    def test_validation_precedes_domain(self):
        rows = [{'sku': 'A', 'location': 'X', 'delta': -1},
                {'sku': 'B', 'location': 'Y', 'delta': True}]
        original = copy.deepcopy(rows)
        for function in (run, compute, render, validate):
            self.assert_error(function, rows, ValueError, 'inventory: invalid row')
        for function in (run_many, render_many):
            self.assert_error(function, [[], rows], ValueError, 'inventory: invalid row')
        self.assertEqual(rows, original)

    def test_field_validation(self):
        class IntSubclass(int):
            pass

        invalid = [None, [], {},
                   {'sku': 'A', 'location': 'X'},
                   {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 2}]
        for field, values in (
            ('sku', [None, 1, '', ' \t\n']),
            ('location', [None, 1, '', ' \t\n']),
            ('delta', [True, False, 1.0, '1', None, IntSubclass(1)]),
        ):
            for value in values:
                row = {'sku': 'A', 'location': 'X', 'delta': 1}
                row[field] = value
                invalid.append(row)
        for row in invalid:
            for function in (validate, compute, run, render):
                with self.subTest(row=row, function=function):
                    self.assert_error(function, [row], ValueError,
                                      'inventory: invalid row')

    def test_container_validation(self):
        for value in (None, (), {}, '', iter([])):
            for function in (validate, compute, run, render):
                self.assert_error(function, value, TypeError,
                                  'inventory: rows must be a list')
            for function in (run_many, render_many):
                self.assert_error(function, value, TypeError,
                                  'inventory: batches must be a list')
        for function in (run_many, render_many):
            self.assert_error(function, [[], ()], TypeError,
                              'inventory: rows must be a list')

    def test_canonicalization_order_and_zero(self):
        rows = [{'sku': ' b ', 'location': ' z ', 'delta': 3},
                {'sku': ' a ', 'location': ' y ', 'delta': 2},
                {'sku': 'A', 'location': 'X', 'delta': 0},
                {'sku': 'a', 'location': 'Y', 'delta': -2},
                {'sku': ' B', 'location': 'a ', 'delta': 4}]
        expected = {'stock': [
            {'sku': 'A', 'location': 'X', 'quantity': 0},
            {'sku': 'A', 'location': 'Y', 'quantity': 0},
            {'sku': 'B', 'location': 'A', 'quantity': 4},
            {'sku': 'B', 'location': 'Z', 'quantity': 3},
        ], 'totals': {'A': 0, 'B': 7}}
        self.assertEqual(normalize(' a '), 'A')
        for function in (run, compute):
            result = function(rows)
            self.assertEqual(result, expected)
            self.assertEqual(list(result['totals']), ['A', 'B'])
        self.assertEqual(run_many([rows, []]), [expected, {'stock': [], 'totals': {}}])
        self.assertEqual(json.loads(render(rows)), expected)

    def test_render_format(self):
        rows = [{'sku': ' é" ', 'location': ' 한\\\n글 ', 'delta': 2}]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertIn('É', expected)
        self.assertIn('한', expected)
        self.assertEqual(render_many([rows, [], rows]),
                         expected + render([]) + expected)

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        validated = validate(rows)
        validated[0]['sku'] = 'changed'
        results = run_many([rows, rows])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        render(rows)
        render_many([rows, rows])
        self.assertEqual(rows, original)
        bad = rows + [{'sku': 'A', 'location': 'X', 'delta': -3}]
        batches = [rows, bad]
        before = copy.deepcopy(batches)
        for function in (run_many, render_many):
            self.assert_error(function, batches, ValueError, 'inventory: negative stock')
            self.assertEqual(batches, before)
        self.assertEqual(run_many([rows]), [expected])

    def test_empty_and_subclasses(self):
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = ListSubclass([DictSubclass(sku=' a ', location=' x ', delta=0)])
        self.assertEqual(run_many(ListSubclass([rows])), [run(rows)])
        self.assertEqual(render_many(ListSubclass([rows])), render(rows))


if __name__ == '__main__':
    unittest.main()
