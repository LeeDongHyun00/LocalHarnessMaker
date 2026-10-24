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
            {'sku': ' a ', 'location': ' x ', 'delta': -3},
            {'sku': 'A', 'location': 'X', 'delta': 3},
        ]
        expected = {
            'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
            'totals': {'A': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(json.loads(render(rows)), expected)
        self.assertEqual(render_many([rows]), render(rows))
        self.assertEqual(normalize(' a '), 'A')
        self.assertEqual(validate(rows)[0],
                         {'sku': 'A', 'location': 'X', 'delta': -3})

    def test_ordering_and_unicode_render(self):
        rows = [
            {'sku': ' b ', 'location': 'z', 'delta': 2},
            {'sku': 'a', 'location': 'y', 'delta': 1},
            {'sku': 'B', 'location': 'a', 'delta': 0},
            {'sku': 'é"\\', 'location': '\t한\n', 'delta': 3},
        ]
        result = run(rows)
        self.assertEqual(
            [(r['sku'], r['location'], r['quantity']) for r in result['stock']],
            [('A', 'Y', 1), ('B', 'A', 0), ('B', 'Z', 2), ('É"\\', '한', 3)])
        self.assertEqual(list(result['totals'].items()),
                         [('A', 1), ('B', 2), ('É"\\', 3)])
        self.assertEqual(render(rows), json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')

    def test_invalid_fields_and_error_precedence(self):
        class IntSubclass(int):
            pass

        invalid = [
            None, [], {}, {'sku': 'A', 'location': 'X'},
            {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 0},
        ]
        for key, values in (
            ('sku', [None, 1, '', ' \t\n']),
            ('location', [None, 1, '', ' \t\n']),
            ('delta', [True, False, 1.0, '1', None, IntSubclass(1)]),
        ):
            for value in values:
                row = {'sku': 'A', 'location': 'X', 'delta': 1}
                row[key] = value
                invalid.append(row)
        for row in invalid:
            rows = [{'sku': 'A', 'location': 'X', 'delta': -1}, row]
            for single in (run, compute, validate, render):
                with self.subTest(row=row, api=single.__name__):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        single(rows)
            for batch in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    batch([[], rows])

    def test_outer_types_and_subclasses(self):
        for value in (None, (), {}, '', iter([])):
            for single in (run, compute, validate, render):
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    single(value)
            for batch in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    batch(value)
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    batch([[], value])

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=1)])
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_final_negative_stock(self):
        rows = [
            {'sku': 'a', 'location': 'x', 'delta': 2},
            {'sku': 'A', 'location': 'X', 'delta': -3},
            {'sku': 'a', 'location': 'y', 'delta': 10},
        ]
        for single in (run, compute, render):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                single(rows)
        for batch in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                batch([[], rows, []])

    def test_inputs_and_results_are_independent(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        validated[0]['sku'] = 'CHANGED'
        self.assertEqual(rows, original)
        render_many([rows, rows])
        self.assertEqual(rows, original)
        for tail in ({'sku': '', 'location': 'X', 'delta': 0},
                     {'sku': 'A', 'location': 'X', 'delta': -3}):
            failing = rows + [tail]
            before = copy.deepcopy(failing)
            for single in (run, render):
                with self.assertRaises(ValueError):
                    single(failing)
                self.assertEqual(failing, before)
            for batch in (run_many, render_many):
                with self.assertRaises(ValueError):
                    batch([rows, failing])
                self.assertEqual(failing, before)
                self.assertEqual(rows, original)

    def test_empty_and_batch_order(self):
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        batches = [
            [{'sku': 'b', 'location': 'x', 'delta': 1}],
            [],
            [{'sku': 'a', 'location': 'y', 'delta': 2}],
        ]
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        empty_results = run_many([[], []])
        empty_results[0]['stock'].append({})
        empty_results[0]['totals']['A'] = 1
        self.assertEqual(empty_results[1], {'stock': [], 'totals': {}})


if __name__ == '__main__':
    unittest.main()
