import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class TestCase(unittest.TestCase):
    def test_domain_edge(self):
        self.assertEqual(run([
            {'sku': ' a ', 'location': ' x ', 'delta': -2},
            {'sku': 'A', 'location': 'X', 'delta': 2},
        ]), {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
             'totals': {'A': 0}})

    def test_validation_precedes_domain_error(self):
        for operation in (run, compute, render):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    operation([{'sku': 'A', 'location': 'X', 'delta': -1},
                               {'sku': 'B', 'location': 'Y', 'delta': True}])

    def test_invalid_inputs(self):
        class IntSubclass(int):
            pass

        for rows in (None, (), {}, 'rows', iter([])):
            with self.subTest(rows=rows):
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    run(rows)
        base = {'sku': 'A', 'location': 'X', 'delta': 0}
        invalid = [None, [], {}, {**base, 'extra': 1}]
        invalid.extend({key: value for key, value in base.items() if key != missing}
                       for missing in base)
        for key in ('sku', 'location'):
            invalid.extend({**base, key: value} for value in (None, 1, '', ' \t\n'))
        invalid.extend({**base, 'delta': value}
                       for value in (True, False, 1.0, '1', None, IntSubclass(1)))
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    run([row])

    def test_subclasses_order_and_totals(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(sku=' b ', location='z', delta=2),
                     Row(sku='a', location=' y ', delta=3),
                     Row(sku='A', location='x', delta=0)])
        result = run(rows)
        self.assertEqual(result, {'stock': [
            {'sku': 'A', 'location': 'X', 'quantity': 0},
            {'sku': 'A', 'location': 'Y', 'quantity': 3},
            {'sku': 'B', 'location': 'Z', 'quantity': 2}],
            'totals': {'A': 3, 'B': 2}})
        self.assertEqual(list(result['totals']), ['A', 'B'])
        self.assertEqual(normalize(' a '), 'A')

    def test_negative_final_stock(self):
        for operation in (run, compute, render):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                    operation([{'sku': 'A', 'location': 'X', 'delta': -1}])

    def test_immutability_and_fresh_results(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        normalized = validate(rows)
        normalized[0]['sku'] = 'CHANGED'
        result = run(rows)
        result['stock'][0]['quantity'] = 999
        result['stock'].append({})
        result['totals']['A'] = 999
        self.assertEqual(rows, original)
        self.assertEqual(run(rows), expected)
        for failing_rows in (
            rows + [{'sku': '', 'location': 'X', 'delta': 0}],
            rows + [{'sku': 'B', 'location': 'X', 'delta': -1}],
        ):
            before = copy.deepcopy(failing_rows)
            with self.assertRaises(ValueError):
                run(failing_rows)
            self.assertEqual(failing_rows, before)

    def test_render_unicode_escaping_and_empty(self):
        self.assertEqual(render([{'sku': 'é"', 'location': 'x\\y', 'delta': 2}]),
                         '{"stock":[{"location":"X\\\\Y","quantity":2,"sku":"É\\\""}],"totals":{"É\\\"":2}}\n')
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')

    def test_batch_outer_inputs(self):
        for operation in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.subTest(operation=operation.__name__, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                        operation(batches)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_order_and_rendering(self):
        class Batches(list):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        batches = Batches([
            Rows([Row(sku=' b ', location='z', delta=2),
                  Row(sku='a', location='y', delta=3)]),
            [],
            [{'sku': 'é"', 'location': 'x\\y', 'delta': -2},
             {'sku': 'É"', 'location': 'X\\Y', 'delta': 2}],
        ])
        before = copy.deepcopy(batches)
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(render_many([[], []]),
                         '{"stock":[],"totals":{}}\n' * 2)
        self.assertEqual(batches, before)

    def test_batch_member_errors_and_input_preservation(self):
        class IntSubclass(int):
            pass

        valid = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        base = {'sku': 'B', 'location': 'Y', 'delta': 0}
        invalid_rows = [None, [], {}, {**base, 'extra': 1}]
        invalid_rows.extend({key: value for key, value in base.items() if key != missing}
                            for missing in base)
        for key in ('sku', 'location'):
            invalid_rows.extend({**base, key: value} for value in (None, 1, '', ' \t\n'))
        invalid_rows.extend({**base, 'delta': value}
                            for value in (True, False, 1.0, '1', None, IntSubclass(1)))
        failures = [(member, TypeError, 'inventory: rows must be a list')
                    for member in (None, (), {}, 'rows')]
        failures.extend(([row], ValueError, 'inventory: invalid row')
                        for row in invalid_rows)
        negative = [{'sku': 'B', 'location': 'Y', 'delta': -1}]
        failures.append((negative, ValueError, 'inventory: negative stock'))
        # Malformed rows take precedence over domain errors within a member.
        failures.append((negative + [{}], ValueError, 'inventory: invalid row'))
        for operation in (run_many, render_many):
            for member, error_type, message in failures:
                for batches in ([member, valid], [valid, member, valid]):
                    with self.subTest(operation=operation.__name__, member=member):
                        before = copy.deepcopy(batches)
                        with self.assertRaisesRegex(error_type, '^' + message + '$'):
                            operation(batches)
                        self.assertEqual(batches, before)
            # Members are processed in encounter order, independently.
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                operation([negative, [{}]])
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                operation([iter([])])
            self.assertEqual(operation([valid]),
                             [run(valid)] if operation is run_many else render(valid))

    def test_batch_result_isolation(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        expected = [run(member) for member in batches]
        later = run_many(batches)
        result = run_many(batches)
        result[0]['stock'][0]['quantity'] = 999
        result[0]['stock'].append({})
        result[0]['totals']['A'] = 999
        result[2]['stock'].append({})
        result[2]['totals']['B'] = 1
        self.assertEqual(result[1], expected[1])
        self.assertEqual(result[3], expected[3])
        self.assertEqual(later, expected)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
