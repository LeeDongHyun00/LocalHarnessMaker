import copy
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
            {'sku': 'a', 'location': 'z', 'delta': 2},
            {'sku': ' A ', 'location': ' x ', 'delta': 4},
        ]
        result = run(rows)
        self.assertEqual(result, {
            'stock': [
                {'sku': 'A', 'location': 'X', 'quantity': 4},
                {'sku': 'A', 'location': 'Z', 'quantity': 2},
                {'sku': 'B', 'location': 'Y', 'quantity': 0},
            ],
            'totals': {'A': 6, 'B': 0},
        })
        self.assertEqual(list(result['totals']), ['A', 'B'])

    def test_validation_precedes_domain_errors(self):
        negative = {'sku': 'a', 'location': 'x', 'delta': -1}
        rows = [negative, {'sku': 'b', 'location': 'y', 'delta': True}]
        before = copy.deepcopy(rows)
        for operation in (run, compute, render):
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                operation(rows)
            self.assertEqual(rows, before)
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                operation([negative])
            self.assertEqual(rows, before)

    def test_invalid_inputs(self):
        class IntSubclass(int):
            pass

        invalid_rows = [
            None, [], {},
            {'sku': 'a', 'location': 'x'},
            {'sku': 'a', 'location': 'x', 'delta': 1, 'extra': 1},
        ]
        for field, values in (
            ('sku', [None, 1, '', ' \t\n']),
            ('location', [None, 1, '', ' \t\n']),
            ('delta', [True, False, 1.0, '1', None, IntSubclass(1)]),
        ):
            for value in values:
                row = {'sku': 'a', 'location': 'x', 'delta': 1}
                row[field] = value
                invalid_rows.append(row)
        for operation in (validate, compute, run, render):
            for value in (None, {}, (), 'abc', iter([])):
                with self.subTest(operation=operation.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                        operation(value)
            for row in invalid_rows:
                with self.subTest(operation=operation.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        operation([row])

    def test_subclasses_and_normalization(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' a ', location=' x ', delta=0)])
        self.assertEqual(normalize(' a '), 'A')
        self.assertEqual(validate(rows), [{'sku': 'A', 'location': 'X', 'delta': 0}])
        self.assertEqual(run(rows), {
            'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
            'totals': {'A': 0},
        })

    def test_immutable_inputs_and_fresh_results(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        before = copy.deepcopy(rows)
        expected = run(rows)
        result = run(rows)
        result['stock'][0]['quantity'] = 99
        result['stock'].append({})
        result['totals']['A'] = 99
        validated = validate(rows)
        validated[0]['sku'] = 'CHANGED'
        validated.append({})
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), expected)
        render(rows)
        self.assertEqual(rows, before)

    def test_render_and_empty_results(self):
        rows = [{'sku': ' é ', 'location': ' x"\n\\ ', 'delta': 2}]
        self.assertEqual(render(rows),
                         '{"stock":[{"location":"X\\"\\n\\\\","quantity":2,"sku":"É"}],"totals":{"É":2}}\n')
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        result = run([])
        result['stock'].append({})
        result['totals']['A'] = 1
        self.assertEqual(run([]), {'stock': [], 'totals': {}})

    def test_batch_order_and_rendering(self):
        batches = [
            [{'sku': ' b ', 'location': ' y ', 'delta': -3},
             {'sku': 'B', 'location': 'Y', 'delta': 3},
             {'sku': 'a', 'location': 'z', 'delta': 2},
             {'sku': 'A', 'location': 'x', 'delta': 4}],
            [],
            [{'sku': ' é ', 'location': ' x"\n\\ ', 'delta': 2}],
        ]
        before = copy.deepcopy(batches)
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(render_many(batches).count('\n'), 3)
        self.assertEqual(batches, before)

    def test_batch_empty_and_subclasses(self):
        class Batches(list):
            pass

        class Row(dict):
            pass

        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        batches = Batches([Batches([Row(sku=' a ', location=' x ', delta=0)])])
        self.assertEqual(run_many(batches), [run(batches[0])])
        self.assertEqual(render_many(batches), render(batches[0]))
        result = run_many([])
        result.append({})
        self.assertEqual(run_many([]), [])

    def test_batch_invalid_outer_inputs(self):
        for operation in (run_many, render_many):
            for value in (None, {}, (), 'abc', iter([]), 1):
                with self.subTest(operation=operation.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                        operation(value)

    def test_batch_member_errors_and_immutability(self):
        valid = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        negative = {'sku': 'b', 'location': 'y', 'delta': -1}
        cases = [
            (None, TypeError, 'inventory: rows must be a list'),
            ((), TypeError, 'inventory: rows must be a list'),
            ([{}], ValueError, 'inventory: invalid row'),
            ([{'sku': 'a', 'location': 'x', 'delta': True}],
             ValueError, 'inventory: invalid row'),
            ([negative, {}], ValueError, 'inventory: invalid row'),
            ([negative], ValueError, 'inventory: negative stock'),
        ]
        for operation in (run_many, render_many):
            for member, error, message in cases:
                for batches in ([member, valid], [valid, member]):
                    with self.subTest(operation=operation.__name__, batches=batches):
                        before = copy.deepcopy(batches)
                        with self.assertRaisesRegex(error, '^' + message + '$'):
                            operation(batches)
                        self.assertEqual(batches, before)
            # Separate members cannot offset each other's stock or errors.
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                operation([[negative], [{}]])
            self.assertEqual(operation([valid]),
                             [run(valid)] if operation is run_many else render(valid))

    def test_batch_results_are_independent(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        expected = run_many(batches)
        result = run_many(batches)
        result[0]['stock'][0]['quantity'] = 99
        result[0]['stock'].append({})
        result[0]['totals']['A'] = 99
        result[2]['stock'].append({})
        result[2]['totals']['A'] = 99
        self.assertEqual(result[1], expected[1])
        self.assertEqual(result[3], expected[3])
        self.assertEqual(batches, before)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(run(rows), expected[0])


if __name__ == '__main__':
    unittest.main()
