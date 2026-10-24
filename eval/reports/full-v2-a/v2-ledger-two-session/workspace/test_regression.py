import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class LedgerRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' P1 ', 'account': ' CASH ', 'amount': 2},
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'P2', 'account': 'cash', 'amount': -2},
            {'id': 'p3', 'account': 'Alpha', 'amount': 0},
        ]
        result = run(rows)
        self.assertEqual(result, {
            'entries': [
                {'id': 'p1', 'account': 'cash', 'amount': 2},
                {'id': 'p2', 'account': 'cash', 'amount': -2},
                {'id': 'p3', 'account': 'alpha', 'amount': 0},
            ],
            'balances': {'alpha': 0, 'cash': 0},
        })
        self.assertEqual(list(result['balances']), ['alpha', 'cash'])

    def test_validation_precedes_conflict(self):
        conflict = [
            {'id': 'x', 'account': 'a', 'amount': 1},
            {'id': ' X ', 'account': 'b', 'amount': 1},
        ]
        for call in (run, compute, render):
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                call(conflict)
            rows = conflict + [{'id': 'bad', 'account': 'a', 'amount': True}]
            before = copy.deepcopy(rows)
            with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                call(rows)
            self.assertEqual(rows, before)

    def test_input_contract(self):
        class IntSubclass(int):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        valid = {'id': 'x', 'account': 'a', 'amount': 0}
        invalid = [None, [], {}, {**valid, 'extra': 1}]
        for key in valid:
            invalid.append({k: v for k, v in valid.items() if k != key})
        for key in ('id', 'account'):
            for value in (None, 1, '', ' \t\n'):
                invalid.append({**valid, key: value})
        for amount in (True, False, IntSubclass(1), 1.0, '1', None):
            invalid.append({**valid, 'amount': amount})
        for call in (run, compute, validate, render):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(call=call.__name__, rows=type(rows)):
                    with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                        call(rows)
            for row in invalid:
                with self.subTest(call=call.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        call([row])
        self.assertEqual(run(ListSubclass([DictSubclass(valid)])), run([valid]))

    def test_fresh_results_and_empty_input(self):
        rows = [{'id': ' X ', 'account': ' A ', 'amount': -1}]
        before = copy.deepcopy(rows)
        expected = {'entries': [{'id': 'x', 'account': 'a', 'amount': -1}],
                    'balances': {'a': -1}}
        result = run(rows)
        self.assertEqual(result, expected)
        self.assertIsNot(result['entries'][0], rows[0])
        result['entries'][0]['amount'] = 99
        result['entries'].append({})
        result['balances']['a'] = 99
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), expected)
        empty = run([])
        empty['entries'].append({})
        empty['balances']['a'] = 1
        self.assertEqual(run([]), {'entries': [], 'balances': {}})

    def test_render_and_unicode_policy(self):
        self.assertEqual(normalize(' STRAẞE '), 'strasse')
        rows = [{'id': ' É\n" ', 'account': ' 現金\\ ', 'amount': -2}]
        self.assertEqual(render(rows),
                         '{"balances":{"現金\\\\":-2},"entries":[{"account":"現金\\\\","amount":-2,"id":"é\\n\\\""}]}\n')
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')

    def test_batch_outer_input_contract(self):
        class ListSubclass(list):
            pass

        for call, empty in ((run_many, []), (render_many, '')):
            for batches in (None, (), {}, 'batches', iter([]), 0):
                with self.subTest(call=call.__name__, batches=type(batches)):
                    with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                        call(batches)
            self.assertEqual(call([]), empty)
            self.assertEqual(call(ListSubclass()), empty)
            self.assertEqual(call(ListSubclass([ListSubclass()])), call([[]]))

    def test_batch_results_in_encounter_order(self):
        batches = [
            [
                {'id': ' Z ', 'account': ' CASH ', 'amount': 2},
                {'id': 'z', 'account': 'cash', 'amount': 2},
                {'id': ' A ', 'account': 'Alpha', 'amount': 0},
                {'id': 'B', 'account': 'cash', 'amount': -2},
            ],
            [],
            [{'id': 'z', 'account': 'other', 'amount': -3}],
        ]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows) for rows in batches])
        self.assertEqual([row['id'] for row in results[0]['entries']], ['z', 'a', 'b'])
        self.assertEqual(list(results[0]['balances']), ['alpha', 'cash'])
        self.assertEqual(results[0]['balances'], {'alpha': 0, 'cash': 0})
        self.assertEqual(batches, before)

    def test_batch_render_preserves_exact_strings(self):
        batches = [
            [{'id': ' É\n" ', 'account': ' 現金\\ ', 'amount': -2}],
            [],
            [{'id': ' STRAẞE ', 'account': 'CASH', 'amount': 0}],
        ]
        before = copy.deepcopy(batches)
        rendered = render_many(batches)
        self.assertEqual(rendered, ''.join(render(rows) for rows in batches))
        self.assertTrue(rendered.endswith('\n'))
        self.assertEqual([json.loads(line) for line in rendered.splitlines()], run_many(batches))
        self.assertEqual(batches, before)

    def test_batch_member_errors_and_input_preservation(self):
        class IntSubclass(int):
            pass

        valid = {'id': ' X ', 'account': ' A ', 'amount': 1}
        invalid_rows = [None, [], {}, {**valid, 'extra': 1}]
        invalid_rows.extend({k: v for k, v in valid.items() if k != key} for key in valid)
        for key in ('id', 'account'):
            invalid_rows.extend({**valid, key: value} for value in (None, 1, '', ' \t\n'))
        invalid_rows.extend({**valid, 'amount': value}
                            for value in (True, False, IntSubclass(1), 1.0, '1', None))
        conflict = [valid, {**valid, 'account': 'other'}]
        cases = [(member, TypeError, 'ledger: rows must be a list')
                 for member in (None, (), {}, 'rows', 0)]
        cases.extend(([row], ValueError, 'ledger: invalid row') for row in invalid_rows)
        cases.extend([
            (conflict, ValueError, 'ledger: duplicate id'),
            (conflict + [invalid_rows[-1]], ValueError, 'ledger: invalid row'),
        ])
        for call in (run_many, render_many):
            for member, error, message in cases:
                for index in (0, 1, 2):
                    batches = [[valid], [valid]]
                    batches.insert(index, member)
                    before = copy.deepcopy(batches)
                    with self.subTest(call=call.__name__, member=member, index=index):
                        with self.assertRaises(error) as raised:
                            call(batches)
                        self.assertEqual(str(raised.exception), message)
                        self.assertEqual(batches, before)
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                call([conflict, [invalid_rows[-1]]])
            self.assertEqual(call([[valid]]), [run([valid])] if call is run_many else render([valid]))

    def test_batch_results_are_independent(self):
        rows = [{'id': ' X ', 'account': ' A ', 'amount': -1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        later = run_many(batches)
        expected = copy.deepcopy(results)
        self.assertIsNot(results[0], results[1])
        self.assertIsNot(results[0]['entries'][0], rows[0])
        results[0]['entries'][0]['amount'] = 99
        results[0]['entries'].append({})
        results[0]['balances']['a'] = 99
        results[2]['entries'].append({})
        results[2]['balances']['a'] = 99
        self.assertEqual(results[1], expected[1])
        self.assertEqual(results[3], expected[3])
        self.assertEqual(later, expected)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
