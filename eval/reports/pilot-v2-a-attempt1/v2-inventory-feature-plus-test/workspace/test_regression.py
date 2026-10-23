import copy
import unittest

from project import render, render_many, run, run_many


class RegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'sku': ' a ', 'location': ' x ', 'delta': -2},
            {'sku': 'A', 'location': 'X', 'delta': 2},
        ]
        expected = {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 0}],
                    'totals': {'A': 0}}
        self.assertEqual(run_many([rows, []]), [expected, {'stock': [], 'totals': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^inventory: negative stock$'):
                api([rows, [{'sku': 'A', 'location': 'X', 'delta': -1}]])

    def test_validation_precedes_domain_error(self):
        rows = [{'sku': 'A', 'location': 'X', 'delta': -1},
                {'sku': 'B', 'location': 'Y', 'delta': True}]
        before = copy.deepcopy(rows)
        for api, argument in ((run, rows), (render, rows),
                              (run_many, [[], rows]), (render_many, [[], rows])):
            with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                api(argument)
            self.assertEqual(rows, before)

    def test_input_contract(self):
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        for api in (run_many, render_many):
            for value in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^inventory: batches must be a list$'):
                    api(value)
            with self.assertRaisesRegex(TypeError, '^inventory: rows must be a list$'):
                api([()])
        valid = {'sku': 'A', 'location': 'X', 'delta': 1}
        invalid = [None, {}, dict(valid, extra=1), dict(valid, sku='  '),
                   dict(valid, location=1), dict(valid, delta=True),
                   dict(valid, delta=IntSubclass(1))]
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^inventory: invalid row$'):
                    run_many([[row]])
        self.assertEqual(run_many(ListSubclass([ListSubclass([DictSubclass(valid)])])),
                         [run([valid])])

    def test_order_unicode_and_fresh_results(self):
        rows = [{'sku': ' b ', 'location': ' y ', 'delta': 2},
                {'sku': ' é ', 'location': ' "x" ', 'delta': 0},
                {'sku': ' a ', 'location': ' z ', 'delta': 3},
                {'sku': 'A', 'location': 'X', 'delta': 1}]
        before = copy.deepcopy(rows)
        result = run_many([rows, rows])
        self.assertEqual(list(result[0]['totals']), ['A', 'B', 'É'])
        self.assertEqual([(r['sku'], r['location']) for r in result[0]['stock']],
                         [('A', 'X'), ('A', 'Z'), ('B', 'Y'), ('É', '"X"')])
        result[0]['stock'][0]['quantity'] = 100
        result[0]['totals']['A'] = 100
        self.assertEqual(result[1], run(rows))
        self.assertEqual(rows, before)
        self.assertEqual(render_many([[rows[1]]]),
                         '{"stock":[{"location":"\\"X\\"","quantity":0,"sku":"É"}],"totals":{"É":0}}\n')


if __name__ == '__main__':
    unittest.main()
