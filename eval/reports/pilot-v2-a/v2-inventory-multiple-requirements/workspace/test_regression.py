import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def assert_inventory_error(self, function, value, error, message):
        with self.assertRaises(error) as caught:
            function(value)
        self.assertEqual(str(caught.exception), message)

    def test_domain_edge(self):
        # Replenishment cannot repair an earlier negative prefix.
        rows = [
            {'sku': ' a ', 'location': 'x', 'delta': -1},
            {'sku': 'A', 'location': ' X ', 'delta': 2},
        ]
        for function in (run, compute, render):
            with self.subTest(function=function.__name__):
                self.assert_inventory_error(function, rows, ValueError,
                                            'inventory: negative stock')

    def test_local_overdraft(self):
        rows = [
            {'sku': 'A', 'location': 'X', 'delta': 10},
            {'sku': 'A', 'location': 'Y', 'delta': -1},
        ]
        for function in (run, compute, render):
            self.assert_inventory_error(function, rows, ValueError,
                                        'inventory: negative stock')

    def test_canonical_aggregation_order_and_zero(self):
        rows = [
            {'sku': ' b ', 'location': 'z', 'delta': 2},
            {'sku': 'a', 'location': 'y', 'delta': 3},
            {'sku': ' B', 'location': ' Z ', 'delta': -2},
            {'sku': 'A', 'location': 'x', 'delta': 0},
        ]
        expected = {
            'stock': [
                {'sku': 'A', 'location': 'X', 'quantity': 0},
                {'sku': 'A', 'location': 'Y', 'quantity': 3},
                {'sku': 'B', 'location': 'Z', 'quantity': 0},
            ],
            'totals': {'A': 3, 'B': 0},
        }
        self.assertEqual(normalize(' a '), 'A')
        self.assertEqual(validate(rows)[0], {'sku': 'B', 'location': 'Z', 'delta': 2})
        for function in (run, compute):
            result = function(rows)
            self.assertEqual(result, expected)
            self.assertEqual(list(result['totals']), ['A', 'B'])

    def test_input_validation_and_precedence(self):
        class IntSubclass(int):
            pass

        valid = {'sku': 'A', 'location': 'X', 'delta': 1}
        invalid = [None, [], {}, {**valid, 'extra': 0}]
        for key, values in (
            ('sku', [None, 1, '', ' \t ']),
            ('location', [None, 1, '', '\n']),
            ('delta', [None, True, False, 1.0, '1', IntSubclass(1)]),
        ):
            invalid.append({k: v for k, v in valid.items() if k != key})
            invalid.extend({**valid, key: value} for value in values)
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        for function in (validate, compute, run, render):
            for value in (None, {}, (), 'rows', iter([])):
                self.assert_inventory_error(function, value, TypeError,
                                            'inventory: rows must be a list')
            for row in invalid:
                with self.subTest(function=function.__name__, row=row):
                    self.assert_inventory_error(function, [negative, row], ValueError,
                                                'inventory: invalid row')

    def test_list_and_dict_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=0)])
        self.assertEqual(run(rows), {
            'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
            'totals': {'A': 0},
        })
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_render_unicode_escaping_and_format(self):
        rows = [{'sku': ' é" ', 'location': ' x\\y ', 'delta': 1}]
        expected = '{"stock":[{"location":"X\\\\Y","quantity":1,"sku":"É\\\""}],"totals":{"É\\\"":1}}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_empty_inputs(self):
        self.assertEqual(validate([]), [])
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(compute([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_results_and_isolation(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        batches = [rows, [], rows]
        original = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows), run([]), run(rows)])
        self.assertEqual(render_many(batches), render(rows) + render([]) + render(rows))
        results[0]['stock'][0]['quantity'] = 99
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        self.assertEqual(results[2], run(rows))
        self.assertEqual(batches, original)
        self.assertEqual(run_many(batches)[0], run(rows))

    def test_batch_errors_are_independent_and_atomic(self):
        valid = [{'sku': ' a ', 'location': ' x ', 'delta': 5}]
        negative = [{'sku': 'A', 'location': 'X', 'delta': -1}]
        malformed = [*negative, {'sku': 'A'}]
        for function in (run_many, render_many):
            for value in (None, {}, (), 'batches'):
                self.assert_inventory_error(function, value, TypeError,
                                            'inventory: batches must be a list')
            for member, error, message in (
                (negative, ValueError, 'inventory: negative stock'),
                (malformed, ValueError, 'inventory: invalid row'),
                (None, TypeError, 'inventory: rows must be a list'),
            ):
                batches = [valid, member, valid]
                original = copy.deepcopy(batches)
                self.assert_inventory_error(function, batches, error, message)
                self.assertEqual(batches, original)
            self.assertEqual(run(valid)['totals'], {'A': 5})

    def test_single_input_isolation_on_success_and_failure(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        validated = validate(rows)
        validated[0]['sku'] = 'CHANGED'
        result = run(rows)
        result['stock'][0]['quantity'] = 99
        result['totals']['A'] = 99
        self.assertEqual(rows, original)
        self.assertEqual(run(rows)['totals'], {'A': 2})
        for bad_row in ({'sku': 'bad'}, {'sku': 'A', 'location': 'X', 'delta': -3}):
            failing = rows + [bad_row]
            before = copy.deepcopy(failing)
            for function in (run, compute, render):
                with self.assertRaises(ValueError):
                    function(failing)
                self.assertEqual(failing, before)


if __name__ == '__main__':
    unittest.main()
