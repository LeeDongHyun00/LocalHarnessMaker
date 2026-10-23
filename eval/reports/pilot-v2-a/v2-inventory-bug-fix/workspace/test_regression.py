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
            {'sku': ' b ', 'location': ' y ', 'delta': -3},
            {'sku': 'B', 'location': 'Y', 'delta': 3},
            {'sku': ' a ', 'location': ' z ', 'delta': 2},
            {'sku': 'A', 'location': ' x ', 'delta': 1},
        ]
        expected = {
            'stock': [
                {'sku': 'A', 'location': 'X', 'quantity': 1},
                {'sku': 'A', 'location': 'Z', 'quantity': 2},
                {'sku': 'B', 'location': 'Y', 'quantity': 0},
            ],
            'totals': {'A': 3, 'B': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)['totals']), ['A', 'B'])
        self.assertEqual(normalize(' ß '), 'SS')
        self.assertEqual(validate(rows)[0],
                         {'sku': 'B', 'location': 'Y', 'delta': -3})

    def test_validation_and_error_precedence(self):
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {},
                        {'sku': 'A', 'location': 'X', 'delta': 1, 'extra': 0}]
        for field, values in [('sku', [None, 1, '', ' \t']),
                              ('location', [None, 1, '', '\n']),
                              ('delta', [True, False, 1.0, '1', IntSubclass(1)])]:
            for value in values:
                row = {'sku': 'A', 'location': 'X', 'delta': 1}
                row[field] = value
                invalid_rows.append(row)
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        for row in invalid_rows:
            for call in (run, compute, validate, render):
                with self.subTest(row=row, call=call.__name__):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        call([negative, row])
        for call in (run, compute, validate, render):
            for rows in (None, {}, (), 'rows', iter([])):
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    call(rows)
        for call in (run, compute, render):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                call([negative])

    def test_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=2)])
        original = copy.deepcopy(rows)
        expected = run(rows)
        validated = validate(rows)
        validated[0]['delta'] = 99
        results = run_many([rows, rows])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        for call in (run, render, run_many, render_many):
            invalid = rows + [{'sku': 'A', 'location': 'X', 'delta': False}]
            before = copy.deepcopy(invalid)
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                call([rows, invalid] if call in (run_many, render_many) else invalid)
            self.assertEqual(invalid, before)
            self.assertEqual(rows, original)

    def test_render_and_batches(self):
        rows = [{'sku': ' é ', 'location': ' x"\\\n ', 'delta': 0}]
        encoded = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, [], rows]), encoded + render([]) + encoded)
        self.assertEqual(run_many([rows, [], rows]), [run(rows), run([]), run(rows)])
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for call in (run_many, render_many):
            for batches in (None, {}, (), 'batches'):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    call(batches)
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                call([rows, ()])
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                call([rows, [{'sku': 'A', 'location': 'X', 'delta': -1}]])


if __name__ == '__main__':
    unittest.main()
