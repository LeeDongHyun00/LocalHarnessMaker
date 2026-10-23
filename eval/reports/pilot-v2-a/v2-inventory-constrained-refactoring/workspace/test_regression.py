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
            {'sku': ' a ', 'location': ' x ', 'delta': -3},
            {'sku': 'A', 'location': 'X', 'delta': 3},
        ]
        self.assertEqual(run(rows), {
            'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
            'totals': {'A': 0},
        })
        with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
            run(rows[:1])

    def test_validation_precedes_domain_errors(self):
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        for entry in (run, render, compute, validate):
            with self.subTest(entry=entry.__name__):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    entry([negative, {'sku': 'B', 'location': 'Y', 'delta': True}])

    def test_runtime_normalization(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        expected = {
            'stock': [{'sku': 'patched:a', 'location': 'patched:x', 'quantity': 2}],
            'totals': {'patched:a': 2},
        }
        encoded = json.dumps(expected, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(normalize(' a '), 'A')
        with patch('project.policy.normalize', side_effect=lambda s: 'patched:' + s.strip()) as mocked:
            self.assertEqual(run(rows), expected)
            self.assertEqual(render(rows), encoded)
            self.assertEqual(run_many([rows]), [expected])
            self.assertEqual(render_many([rows]), encoded)
            self.assertEqual(mocked.call_count, 8)

    def test_field_validation_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Int(int):
            pass

        valid = {'sku': ' a ', 'location': ' x ', 'delta': 1}
        self.assertEqual(run(Rows([Row(valid)])), run([valid]))
        for invalid in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                run(invalid)
        invalid_rows = [None, {}, dict(valid, extra=1)]
        for field in ('sku', 'location'):
            for value in (None, 1, '', ' \t\n'):
                invalid_rows.append(dict(valid, **{field: value}))
        for value in (True, False, Int(1), 1.0, '1', None):
            invalid_rows.append(dict(valid, delta=value))
        for invalid in invalid_rows:
            with self.subTest(row=invalid):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    run([invalid])

    def test_ordering_rendering_and_empty_inputs(self):
        rows = [
            {'sku': ' b ', 'location': ' z ', 'delta': 2},
            {'sku': 'é"', 'location': ' \nX ', 'delta': 1},
            {'sku': 'B', 'location': 'A', 'delta': 0},
        ]
        expected = {
            'stock': [
                {'sku': 'B', 'location': 'A', 'quantity': 0},
                {'sku': 'B', 'location': 'Z', 'quantity': 2},
                {'sku': 'É"', 'location': 'X', 'quantity': 1},
            ],
            'totals': {'B': 2, 'É"': 1},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['totals']), ['B', 'É"'])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(render_many([rows, []]), encoded + render([]))

    def test_batch_errors_and_result_isolation(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        for entry in (run_many, render_many):
            for invalid in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    entry(invalid)
            for bad, error, message in (
                (None, TypeError, 'inventory: rows must be a list'),
                ([{}], ValueError, 'inventory: invalid row'),
                ([dict(rows[0], delta=-1)], ValueError, 'inventory: negative stock'),
            ):
                batches = [rows, bad]
                before = copy.deepcopy(batches)
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    entry(batches)
                self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
