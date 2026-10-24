import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def assert_inventory_error(self, call, value, error_type, message):
        before = copy.deepcopy(value)
        with self.assertRaises(error_type) as caught:
            call(value)
        self.assertEqual(str(caught.exception), message)
        self.assertEqual(value, before)

    def test_domain_edge(self):
        cases = [
            [{'sku': 'a', 'location': 'x', 'delta': -1},
             {'sku': 'A', 'location': 'X', 'delta': 2}],
            [{'sku': 'a', 'location': 'x', 'delta': 5},
             {'sku': 'A', 'location': 'y', 'delta': -1}],
            [{'sku': 'a', 'location': 'x', 'delta': 1},
             {'sku': ' A ', 'location': ' X ', 'delta': -2},
             {'sku': 'a', 'location': 'x', 'delta': 1}],
        ]
        for rows in cases:
            for call in (run, compute, render):
                with self.subTest(rows=rows, call=call):
                    self.assert_inventory_error(call, rows, ValueError,
                                                'inventory: negative stock')

    def test_validation_precedes_domain_errors(self):
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {},
                        {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 0}]
        valid = {'sku': 'A', 'location': 'X', 'delta': 1}
        for field, values in [('sku', [None, 2, '', ' \t']),
                              ('location', [None, 2, '', '\n ']),
                              ('delta', [True, False, 1.0, '1', IntSubclass(1), None])]:
            invalid_rows.extend(dict(valid, **{field: value}) for value in values)
        for invalid in invalid_rows:
            rows = [dict(valid, delta=-1), invalid]
            for call in (validate, compute, run, render,
                         lambda rows: run_many([[], rows]),
                         lambda rows: render_many([[], rows])):
                with self.subTest(invalid=invalid, call=call):
                    self.assert_inventory_error(call, rows, ValueError,
                                                'inventory: invalid row')

    def test_input_shapes(self):
        for value in (None, (), {}, 'rows', 1):
            for call in (validate, compute, run, render):
                self.assert_inventory_error(call, value, TypeError,
                                            'inventory: rows must be a list')
            for call in (run_many, render_many):
                self.assert_inventory_error(call, value, TypeError,
                                            'inventory: batches must be a list')
                self.assert_inventory_error(call, [[], value], TypeError,
                                            'inventory: rows must be a list')

    def test_canonicalization_order_and_zero(self):
        rows = [{'sku': ' b ', 'location': ' z ', 'delta': 2},
                {'sku': ' a ', 'location': ' y ', 'delta': 3},
                {'sku': ' B ', 'location': ' Z ', 'delta': -2},
                {'sku': 'a', 'location': 'x', 'delta': 0}]
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0},
                              {'sku': 'A', 'location': 'Y', 'quantity': 3},
                              {'sku': 'B', 'location': 'Z', 'quantity': 0}],
                    'totals': {'A': 3, 'B': 0}}
        before = copy.deepcopy(rows)
        self.assertEqual(normalize(' a '), 'A')
        self.assertEqual(validate(rows)[0], {'sku': 'B', 'location': 'Z', 'delta': 2})
        for call in (run, compute):
            result = call(rows)
            self.assertEqual(result, expected)
            self.assertEqual(list(result['totals']), ['A', 'B'])
        self.assertEqual(rows, before)

    def test_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=2)])
        before = copy.deepcopy(rows)
        validated = validate(rows)
        validated[0]['sku'] = 'CHANGED'
        results = run_many(Rows([rows, rows]))
        expected = run(rows)
        results[0]['stock'][0]['quantity'] = 99
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        self.assertIsNot(run(rows)['stock'], run(rows)['stock'])

    def test_render_format_and_batches(self):
        rows = [{'sku': ' é"\n ', 'location': ' 한\\ ', 'delta': 2}]
        expected = ('{"stock":[{"location":"한\\\\","quantity":2,'
                    '"sku":"É\\\""}],"totals":{"É\\\"":2}}\n')
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(run_many([rows, []]), [run(rows), run([])])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_empty_results(self):
        self.assertEqual(validate([]), [])
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(compute([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_failure_and_recovery(self):
        good = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        bad = [{'sku': 'a', 'location': 'x', 'delta': -1}]
        for call in (run_many, render_many):
            self.assert_inventory_error(call, [good, bad], ValueError,
                                        'inventory: negative stock')
        self.assertEqual(run_many([good, good]), [run(good), run(good)])
        self.assertEqual(render_many([good]), render(good))


if __name__ == '__main__':
    unittest.main()
