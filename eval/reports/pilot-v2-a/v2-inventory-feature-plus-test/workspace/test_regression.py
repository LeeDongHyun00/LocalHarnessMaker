import copy
import json
import unittest

from project import render, render_many, run, run_many


class BatchTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'sku': ' a ', 'location': ' x ', 'delta': -2},
            {'sku': 'A', 'location': 'X', 'delta': 2},
        ]
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
                    'totals': {'A': 0}}
        self.assertEqual(run_many([rows, []]),
                         [expected, {'stock': [], 'totals': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                api([[], rows[:1]])

    def test_validation_precedes_domain_errors(self):
        negative = {'sku': 'A', 'location': 'X', 'delta': -1}
        invalid = {'sku': 'B', 'location': 'Y', 'delta': True}
        for api in (run, render):
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                api([negative, invalid])
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                api([[], [negative, invalid]])
            for outer in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    api(outer)
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                api([[], ()])

    def test_fresh_results_and_no_mutation(self):
        rows = [{'sku': ' a ', 'location': ' x ', 'delta': 2}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['stock'][0]['quantity'] = 99
        results[0]['totals']['A'] = 99
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, original)
        self.assertEqual(run_many([rows])[0], results[1])
        bad_rows = rows + [{'sku': 'B', 'location': 'Y', 'delta': -1}]
        original_bad = copy.deepcopy(bad_rows)
        for api in (run_many, render_many):
            with self.assertRaises(ValueError):
                api([rows, bad_rows])
            self.assertEqual(bad_rows, original_bad)
            self.assertEqual(rows, original)

    def test_render_format_and_order(self):
        rows = [
            {'sku': ' z ', 'location': 'é', 'delta': 1},
            {'sku': 'a', 'location': '"', 'delta': 2},
            {'sku': 'A', 'location': 'x', 'delta': 3},
        ]
        result = run(rows)
        self.assertEqual(list(result['totals']), ['A', 'Z'])
        self.assertEqual([(r['sku'], r['location']) for r in result['stock']],
                         [('A', '"'), ('A', 'X'), ('Z', 'É')])
        expected = json.dumps(result, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, rows]), expected + expected)


if __name__ == '__main__':
    unittest.main()
