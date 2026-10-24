import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


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

    def test_runtime_policy_for_all_entry_points(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        expected = {
            'stock': [{'sku': 'patched:a', 'location': 'patched:x', 'quantity': 2}],
            'totals': {'patched:a': 2},
        }
        serialized = json.dumps(expected, sort_keys=True, separators=(',', ':')) + '\n'
        for entry, argument, result in (
            (run, rows, expected),
            (render, rows, serialized),
            (run_many, [rows], [expected]),
            (render_many, [rows], serialized),
            (engine.compute, rows, expected),
            (validation.validate, rows, [
                {'sku': 'patched:a', 'location': 'patched:x', 'delta': 2},
            ]),
        ):
            with self.subTest(entry=entry.__name__):
                with patch.object(policy, 'normalize', side_effect=lambda v: 'patched:' + v.strip().lower()) as normalize:
                    self.assertEqual(entry(argument), result)
                    self.assertEqual(normalize.call_count, 2)
        self.assertEqual(policy.normalize(' a '), 'A')

    def test_validation_precedes_domain_errors(self):
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        for entry in (run, render, engine.compute):
            with self.subTest(entry=entry.__name__):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    entry([negative, {'sku': 'B', 'location': 'Y', 'delta': True}])
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                entry([[negative, {}]])

    def test_shapes_and_field_types(self):
        class IntSubclass(int):
            pass

        valid = {'sku': 'A', 'location': 'X', 'delta': 1}
        invalid_rows = [None, [], {}, dict(valid, extra=1)]
        invalid_rows += [dict(valid, **{field: value})
                         for field in ('sku', 'location')
                         for value in (None, 1, '', ' \t\n')]
        invalid_rows += [dict(valid, delta=value) for value in (True, 1.0, '1', IntSubclass(1))]
        for entry in (run, render, validation.validate, engine.compute):
            for outer in (None, (), {}, iter([])):
                with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                    entry(outer)
            for row in invalid_rows:
                with self.subTest(entry=entry.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                        entry([row])
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                entry(())
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                entry([[] , ()])

    def test_subclasses_ordering_and_unicode_render(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([
            Row(sku=' b ', location=' z ', delta=1),
            Row(sku=' a ', location=' y ', delta=2),
            Row(sku='a', location=' x ', delta=3),
            Row(sku='é', location='"\n', delta=0),
        ])
        result = run(rows)
        self.assertEqual([(r['sku'], r['location']) for r in result['stock']],
                         [('A', 'X'), ('A', 'Y'), ('B', 'Z'), ('É', '"')])
        self.assertEqual(list(result['totals'].items()), [('A', 5), ('B', 1), ('É', 0)])
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')) + '\n')
        self.assertEqual(run_many(Rows([rows, []])), [result, {'stock': [], 'totals': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        batches = [rows, rows]
        results = run_many(batches)
        results[0]['stock'][0]['sku'] = 'changed'
        results[0]['stock'].append({})
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, original)
        normalized = validation.validate(rows)
        normalized[0]['sku'] = 'changed'
        self.assertEqual(rows, original)
        for entry in (run_many, render_many):
            bad_batches = [rows, [{'sku': 'B', 'location': 'Y', 'delta': -1}]]
            before = copy.deepcopy(bad_batches)
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                entry(bad_batches)
            self.assertEqual(bad_batches, before)
        invalid = [rows[0], {'nested': {'unchanged': []}}]
        before = copy.deepcopy(invalid)
        with self.assertRaises(ValueError):
            run(invalid)
        self.assertEqual(invalid, before)

    def test_empty_inputs(self):
        self.assertEqual(run([]), {'stock': [], 'totals': {}})
        self.assertEqual(render([]), '{"stock":[],"totals":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
