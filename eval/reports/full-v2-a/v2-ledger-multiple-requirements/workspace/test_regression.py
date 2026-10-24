import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class LedgerRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' P1 ', 'account': ' Straße ', 'amount': 50},
            {'id': 'p2', 'account': 'Cash', 'amount': -3},
            {'id': 'p1', 'account': 'STRASSE', 'amount': 0},
            {'id': ' P2 ', 'account': ' cash ', 'amount': -3},
        ]
        expected = {
            'entries': [
                {'id': 'p1', 'account': 'strasse', 'amount': 0},
                {'id': 'p2', 'account': 'cash', 'amount': -3},
            ],
            'balances': {'cash': -3, 'strasse': 0},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['cash', 'strasse'])
        self.assertEqual(normalize(' Straße '), 'strasse')

    def test_error_precedence_and_batch_failures(self):
        conflict = [
            {'id': ' X ', 'account': 'a', 'amount': 1},
            {'id': 'x', 'account': 'b', 'amount': 2},
        ]
        for rows, message in [(conflict, 'ledger: duplicate id'),
                              (conflict + [{}], 'ledger: invalid row')]:
            before = copy.deepcopy(rows)
            for call in (run, compute, render,
                         lambda value: run_many([[], value]),
                         lambda value: render_many([[], value])):
                with self.subTest(call=call, message=message):
                    with self.assertRaisesRegex(ValueError, '^' + message + '$'):
                        call(rows)
                    self.assertEqual(rows, before)
        self.assertEqual(run_many([[]]), [{'entries': [], 'balances': {}}])

    def test_validation_contract(self):
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        good = {'id': ' I ', 'account': ' A ', 'amount': -1}
        self.assertEqual(validate(ListSubclass([DictSubclass(good)])),
                         [{'id': 'i', 'account': 'a', 'amount': -1}])
        invalid = [None, [], {}, dict(good, extra=1)]
        for key in good:
            missing = dict(good)
            del missing[key]
            invalid.append(missing)
        for key in ('id', 'account'):
            for value in (None, 1, '', ' \t\n'):
                invalid.append(dict(good, **{key: value}))
        for value in (True, False, IntSubclass(1), 1.0, '1', None):
            invalid.append(dict(good, amount=value))
        for row in invalid:
            for call in (validate, compute, run, render):
                with self.subTest(row=row, call=call):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        call([row])
        for value in (None, (), {}, 'rows', iter([])):
            for call in (validate, compute, run, render):
                with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                    call(value)
            for call in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                    call(value)
        for call in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                call([[], None])

    def test_rendering_and_empty_batches(self):
        rows = [{'id': ' É\n" ', 'account': ' 한글 ', 'amount': 0}]
        expected = '{"balances":{"한글":0},"entries":[{"account":"한글","amount":0,"id":"é\\n\\\""}]}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([[], rows]),
                         '{"balances":{},"entries":[]}\n' + expected)
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_results_and_no_input_mutation(self):
        rows = [{'id': ' I ', 'account': ' A ', 'amount': 1},
                {'id': 'i', 'account': 'a', 'amount': 2}]
        before = copy.deepcopy(rows)
        expected = {'entries': [{'id': 'i', 'account': 'a', 'amount': 2}],
                    'balances': {'a': 2}}
        result = run_many([rows, rows])
        result[0]['entries'][0]['amount'] = 100
        result[0]['entries'].append({})
        result[0]['balances']['a'] = 100
        self.assertEqual(result[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['amount'] = 100
        self.assertEqual(rows, before)


if __name__ == '__main__':
    unittest.main()
