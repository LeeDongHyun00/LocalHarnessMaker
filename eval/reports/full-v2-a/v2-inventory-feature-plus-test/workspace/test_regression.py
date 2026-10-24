import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class BatchRegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'sku': ' a ', 'location': ' x ', 'delta': -3},
            {'sku': 'A', 'location': 'X', 'delta': 3},
        ]
        expected = {
            'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
            'totals': {'A': 0},
        }
        self.assertEqual(run_many([rows, []]), [expected, {'stock': [], 'totals': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                    api([[], rows[:1]])

    def test_validation_precedes_domain_errors(self):
        negative = {'sku': 'a', 'location': 'x', 'delta': -1}
        invalid_rows = [
            None,
            {'sku': 'A', 'location': 'X'},
            {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 0},
            {'sku': 1, 'location': 'X', 'delta': 1},
            {'sku': 'A', 'location': '  ', 'delta': 1},
            {'sku': 'A', 'location': 'X', 'delta': True},
            {'sku': 'A', 'location': 'X', 'delta': 1.0},
        ]

        class IntSubclass(int):
            pass

        invalid_rows.append({'sku': 'A', 'location': 'X', 'delta': IntSubclass(1)})
        for invalid in invalid_rows:
            rows = [negative, invalid]
            before = copy.deepcopy(rows)
            for api in (run, render, compute, validate):
                with self.subTest(api=api.__name__, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        api(rows)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    api([[], rows])
            self.assertEqual(rows, before)

    def test_input_shapes(self):
        for value in (None, {}, (), 'rows', 1):
            for api in (run, render, compute, validate):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                        api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    api(value)
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    api([[], value])

    def test_canonicalization_order_and_rendering(self):
        rows = [
            {'sku': ' b ', 'location': ' z ', 'delta': 2},
            {'sku': ' é ', 'location': ' "\\\n ', 'delta': 1},
            {'sku': 'a', 'location': 'y', 'delta': 4},
            {'sku': 'B', 'location': 'a', 'delta': 3},
        ]
        expected = {
            'stock': [
                {'sku': 'A', 'location': 'Y', 'quantity': 4},
                {'sku': 'B', 'location': 'A', 'quantity': 3},
                {'sku': 'B', 'location': 'Z', 'quantity': 2},
                {'sku': 'É', 'location': '"\\', 'quantity': 1},
            ],
            'totals': {'A': 4, 'B': 5, 'É': 1},
        }
        self.assertEqual(normalize(' é '), 'É')
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['totals']), ['A', 'B', 'É'])
        serialized = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(run_many([rows, rows]), [expected, expected])
        self.assertEqual(render_many([rows, rows]), serialized * 2)

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        results[0]['stock'][0]['quantity'] = 99
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 2}], 'totals': {'A': 2}}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(batches, before)
        validated = validate(rows)
        validated[0]['sku'] = 'CHANGED'
        self.assertEqual(batches, before)
        bad = [{'sku': 'a', 'location': 'x', 'delta': -1}]
        failing = [rows, bad]
        before_failure = copy.deepcopy(failing)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                api(failing)
            self.assertEqual(failing, before_failure)
        self.assertEqual(run_many([rows])[0], expected)

    def test_list_and_dict_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=2)])
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 2}], 'totals': {'A': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render_many(Rows([rows])), render(rows))


if __name__ == '__main__':
    unittest.main()
