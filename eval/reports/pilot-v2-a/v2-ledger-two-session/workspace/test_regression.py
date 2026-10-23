import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' A ', 'account': ' Straße ', 'amount': -2},
            {'id': 'a', 'account': 'STRASSE', 'amount': -2},
            {'id': 'B', 'account': 'strasse', 'amount': 2},
            {'id': 'C', 'account': ' Alpha ', 'amount': 0},
        ]
        result = run(rows)
        self.assertEqual(result, {
            'entries': [
                {'id': 'a', 'account': 'strasse', 'amount': -2},
                {'id': 'b', 'account': 'strasse', 'amount': 2},
                {'id': 'c', 'account': 'alpha', 'amount': 0},
            ],
            'balances': {'alpha': 0, 'strasse': 0},
        })
        self.assertEqual(list(result['balances']), ['alpha', 'strasse'])

    def test_validation_precedes_conflict(self):
        conflict = [
            {'id': 'a', 'account': 'cash', 'amount': 1},
            {'id': ' A ', 'account': 'cash', 'amount': 2},
        ]
        for entrypoint in (run, compute, render,
                           lambda rows: run_many([rows]),
                           lambda rows: render_many([rows])):
            with self.subTest(entrypoint=entrypoint):
                with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                    entrypoint(conflict)
                rows = conflict + [{'id': 'bad', 'account': '', 'amount': 0}]
                original = copy.deepcopy(rows)
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    entrypoint(rows)
                self.assertEqual(rows, original)

    def test_invalid_inputs(self):
        class IntSubclass(int):
            pass

        invalid_rows = [
            None, [], {},
            {'id': 'a', 'account': 'b'},
            {'id': 'a', 'account': 'b', 'amount': 1, 'extra': 0},
        ]
        for field, values in (
            ('id', [None, 1, '', ' \t\n']),
            ('account', [None, 1, '', ' \t\n']),
            ('amount', [True, False, 1.0, '1', None, IntSubclass(1)]),
        ):
            for value in values:
                invalid_rows.append({'id': 'a', 'account': 'b', 'amount': 1} | {field: value})
        for entrypoint in (validate, compute, run, render,
                           lambda rows: run_many([rows]),
                           lambda rows: render_many([rows])):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(entrypoint=entrypoint, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                        entrypoint(rows)
            for row in invalid_rows:
                with self.subTest(entrypoint=entrypoint, row=row):
                    with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                        entrypoint([row])

    def test_subclasses_and_direct_helpers(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=' X ', account=' CASH ', amount=-1)])
        expected = [{'id': 'x', 'account': 'cash', 'amount': -1}]
        self.assertEqual(normalize(' Straße '), 'strasse')
        self.assertEqual(validate(rows), expected)
        self.assertEqual(compute(rows), {'entries': expected, 'balances': {'cash': -1}})

    def test_fresh_results_and_input_immutability(self):
        rows = [{'id': ' A ', 'account': ' Cash ', 'amount': 3}]
        original = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        self.assertIsNot(first['entries'], second['entries'])
        self.assertIsNot(first['entries'][0], rows[0])
        self.assertIsNot(first['entries'][0], second['entries'][0])
        self.assertIsNot(first['balances'], second['balances'])
        first['entries'][0]['amount'] = 100
        first['entries'].append({})
        first['balances']['cash'] = 100
        validated = validate(rows)
        validated[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        self.assertEqual(run(rows), second)

    def test_render_exact_bytes(self):
        rows = [{'id': ' É\n"\\ ', 'account': ' 한글 ', 'amount': -2}]
        self.assertEqual(
            render(rows),
            '{"balances":{"한글":-2},"entries":[{"account":"한글","amount":-2,"id":"é\\n\\"\\\\"}]}\n',
        )

    def test_empty(self):
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')

    def test_batch_empty(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run_many([[]]), [run([])])
        self.assertEqual(render_many([[]]), render([]))

    def test_batch_outer_type(self):
        for entrypoint in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.subTest(entrypoint=entrypoint, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                        entrypoint(batches)

    def test_batch_order_policy_and_rendering(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        batches = Rows([
            Rows([Row(id=' B ', account=' Straße ', amount=-2),
                  Row(id='b', account='STRASSE', amount=-2),
                  Row(id=' A ', account='strasse', amount=2),
                  Row(id='c', account=' Alpha ', amount=0)]),
            [],
            [{'id': ' B ', 'account': ' 한글 ', 'amount': 7}],
            [{'id': ' É\n"\\ ', 'account': ' 한글 ', 'amount': -2}],
        ])
        original = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows) for rows in batches])
        self.assertEqual(list(results[0]), ['entries', 'balances'])
        self.assertEqual(list(results[0]['balances']), ['alpha', 'strasse'])
        self.assertEqual([row['id'] for row in results[0]['entries']], ['b', 'a', 'c'])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(render_many([[], []]), render([]) + render([]))
        self.assertEqual(batches, original)

    def test_batch_failures_leave_inputs_and_result_unchanged(self):
        good = [{'id': ' A ', 'account': ' Cash ', 'amount': 3}]
        conflict = good + [{'id': 'a', 'account': 'cash', 'amount': 4}]
        invalid = conflict + [{'id': 'bad', 'account': '', 'amount': 0}]
        for entrypoint in (run_many, render_many):
            for bad, error, message in (
                (None, TypeError, 'ledger: rows must be a list'),
                (conflict, ValueError, 'ledger: duplicate id'),
                (invalid, ValueError, 'ledger: invalid row'),
            ):
                batches = [good, bad, good]
                original = copy.deepcopy(batches)
                result = object()
                sentinel = result
                with self.subTest(entrypoint=entrypoint, message=message):
                    with self.assertRaisesRegex(error, '^' + message + '$'):
                        result = entrypoint(batches)
                    self.assertIs(result, sentinel)
                    self.assertEqual(batches, original)
            # Encounter order applies across members; validation precedence is per member.
            with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                entrypoint([conflict, invalid])

    def test_batch_results_are_independent(self):
        rows = [{'id': ' A ', 'account': ' Cash ', 'amount': 3}]
        batches = [rows, rows, [], []]
        original = copy.deepcopy(batches)
        first = run_many(batches)
        expected = copy.deepcopy(first)
        second = run_many(batches)
        for left, right in ((first[0], first[1]), (first[2], first[3]),
                            (first[0], second[0])):
            self.assertIsNot(left, right)
            self.assertIsNot(left['entries'], right['entries'])
            self.assertIsNot(left['balances'], right['balances'])
        self.assertIsNot(first[0]['entries'][0], first[1]['entries'][0])
        self.assertIsNot(first[0]['entries'][0], second[0]['entries'][0])
        self.assertIsNot(first[0]['entries'][0], rows[0])
        first[0]['entries'][0]['amount'] = 100
        first[0]['entries'].append({})
        first[0]['balances']['cash'] = 100
        first[2]['entries'].append({})
        first[2]['balances']['new'] = 1
        self.assertEqual(first[1], expected[1])
        self.assertEqual(first[3], expected[3])
        self.assertEqual(second, expected)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(batches, original)


if __name__ == '__main__':
    unittest.main()
