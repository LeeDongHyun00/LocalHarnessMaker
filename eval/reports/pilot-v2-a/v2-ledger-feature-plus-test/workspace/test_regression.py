import copy
import unittest

from project import render, render_many, run, run_many


class BatchRegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'id': ' P1 ', 'account': ' CASH ', 'amount': 2},
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'P2', 'account': 'Cash', 'amount': -2},
        ]
        expected = {
            'entries': [
                {'id': 'p1', 'account': 'cash', 'amount': 2},
                {'id': 'p2', 'account': 'cash', 'amount': -2},
            ],
            'balances': {'cash': 0},
        }
        self.assertEqual(run_many([[], rows]), [
            {'entries': [], 'balances': {}}, expected,
        ])
        self.assertEqual(render_many([[], rows]), render([]) + render(rows))

    def test_errors_and_precedence(self):
        conflict = [
            {'id': 'X', 'account': 'a', 'amount': 1},
            {'id': ' x ', 'account': 'b', 'amount': 1},
        ]
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                for outer in (None, (), {}, 'rows'):
                    with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                        api(outer)
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    api([[], ()])
                with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                    api([[], conflict])
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    api([conflict + [{'id': 'z', 'account': 'a', 'amount': True}]])

    def test_no_mutation_or_shared_results(self):
        rows = [{'id': ' X ', 'account': ' Cash ', 'amount': 1}]
        batches = [rows, rows]
        original = copy.deepcopy(batches)
        results = run_many(batches)
        results[0]['entries'][0]['amount'] = 99
        results[0]['entries'].append({})
        results[0]['balances']['cash'] = 99
        self.assertEqual(results[1], run(rows))
        self.assertEqual(run_many(batches), [run(rows), run(rows)])
        self.assertEqual(batches, original)
        empty = run_many([[], []])
        self.assertIsNot(empty[0], empty[1])
        self.assertIsNot(empty[0]['entries'], empty[1]['entries'])
        self.assertIsNot(empty[0]['balances'], empty[1]['balances'])
        bad = [rows, rows + [{'id': 'x', 'account': 'cash', 'amount': 2}]]
        before = copy.deepcopy(bad)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                api(bad)
            self.assertEqual(bad, before)

    def test_unicode_render_and_order(self):
        rows = [
            {'id': ' STRAẞE ', 'account': ' Z ', 'amount': -1},
            {'id': 'strasse', 'account': 'z', 'amount': -1},
            {'id': 'Ä"', 'account': ' A ', 'amount': 0},
        ]
        expected = (
            '{"balances":{"a":0,"z":-1},"entries":['
            '{"account":"z","amount":-1,"id":"strasse"},'
            '{"account":"a","amount":0,"id":"ä\\\""}]}\n'
        )
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, rows]), expected + expected)
        self.assertEqual(list(run_many([rows])[0]['balances']), ['a', 'z'])

    def test_field_validation_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Amount(int):
            pass

        valid = Row(id=' P ', account=' A ', amount=0)
        self.assertEqual(run_many(Rows([Rows([valid])])), [run([valid])])
        invalid_rows = [
            {}, {'id': 'p', 'account': 'a', 'amount': 1, 'extra': 1},
            {'id': ' ', 'account': 'a', 'amount': 1},
            {'id': 'p', 'account': 1, 'amount': 1},
            {'id': 'p', 'account': 'a', 'amount': Amount(1)},
            {'id': 'p', 'account': 'a', 'amount': 1.0},
            {'id': 'p', 'account': 'a', 'amount': False},
            [],
        ]
        for row in invalid_rows:
            for api in (run, render):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api([row])
            for api in (run_many, render_many):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        api([[], [row]])


if __name__ == '__main__':
    unittest.main()
