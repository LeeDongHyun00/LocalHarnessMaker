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
            {'id': ' Straße ', 'account': ' CASH ', 'amount': 100},
            {'id': 'other', 'account': 'bank', 'amount': -2},
            {'id': 'STRASSE', 'account': 'cash', 'amount': -3},
            {'id': 'third', 'account': 'cash', 'amount': 3},
        ]
        expected = {
            'entries': [
                {'id': 'strasse', 'account': 'cash', 'amount': -3},
                {'id': 'other', 'account': 'bank', 'amount': -2},
                {'id': 'third', 'account': 'cash', 'amount': 3},
            ],
            'balances': {'bank': -2, 'cash': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['bank', 'cash'])
        self.assertEqual(compute(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(json.loads(render(rows)), expected)
        self.assertEqual(render_many([rows]), render(rows))

    def test_validation_and_error_precedence(self):
        class IntSubclass(int):
            pass

        conflict = [
            {'id': ' A ', 'account': 'cash', 'amount': 1},
            {'id': 'a', 'account': 'bank', 'amount': 1},
        ]
        invalid = [None, {}, {'id': 'a', 'account': 'cash', 'amount': 1, 'extra': 0}]
        for key, values in [('id', ['', '  ', 1, None]),
                            ('account', ['', '\t', [], None]),
                            ('amount', [True, False, 1.0, '1', IntSubclass(1)])]:
            for value in values:
                invalid.append(dict(id='a', account='cash', amount=1, **{}) | {key: value})
        for row in invalid:
            rows = conflict + [row]
            original = copy.deepcopy(rows)
            for call in (validate, compute, run, render,
                         lambda rows: run_many([[], rows]),
                         lambda rows: render_many([[], rows])):
                with self.subTest(row=row, call=call):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        call(rows)
                    self.assertEqual(rows, original)
        for call in (compute, run, render,
                     lambda rows: run_many([rows]),
                     lambda rows: render_many([rows])):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                call(conflict)

    def test_outer_shapes_and_empty_results(self):
        for value in (None, {}, (), '', iter([])):
            for call in (validate, compute, run, render):
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    call(value)
            for call in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    call(value)
        self.assertEqual(validate([]), [])
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for call in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                call([[], ()])

    def test_subclasses_idempotence_and_freshness(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' P1 ', account=' CASH ', amount=0)] * 2)
        original = copy.deepcopy(rows)
        expected = {'entries': [{'id': 'p1', 'account': 'cash', 'amount': 0}],
                    'balances': {'cash': 0}}
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        self.assertIsNot(validated[0], validated[1])
        validated[0]['amount'] = 8
        results = run_many(Rows([rows, rows]))
        results[0]['entries'][0]['amount'] = 99
        results[0]['balances']['cash'] = 99
        results[0]['entries'].append({})
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        empty = run_many([[], []])
        self.assertIsNot(empty[0], empty[1])
        self.assertIsNot(empty[0]['entries'], empty[1]['entries'])
        self.assertIsNot(empty[0]['balances'], empty[1]['balances'])

    def test_render_unicode_escaping_and_batch_order(self):
        first = [{'id': ' É\n" ', 'account': ' 현금 ', 'amount': -1}]
        second = [{'id': 'b', 'account': 'bank', 'amount': 2}]
        expected = '{"balances":{"현금":-1},"entries":[{"account":"현금","amount":-1,"id":"é\\n\\\""}]}\n'
        self.assertEqual(render(first), expected)
        self.assertEqual(run_many([first, second]), [run(first), run(second)])
        self.assertEqual(render_many([first, second]), expected + render(second))


if __name__ == '__main__':
    unittest.main()
