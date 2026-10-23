import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'id': ' P1 ', 'account': ' CASH ', 'amount': 2},
            {'id': 'p1', 'account': 'cash', 'amount': 2},
            {'id': 'p2', 'account': 'Cash', 'amount': -2},
        ]
        self.assertEqual(run(rows), {
            'entries': [
                {'id': 'p1', 'account': 'cash', 'amount': 2},
                {'id': 'p2', 'account': 'cash', 'amount': -2},
            ],
            'balances': {'cash': 0},
        })

    def test_runtime_policy_for_all_entry_points(self):
        rows = [{'id': ' P1 ', 'account': ' CASH ', 'amount': 2}]
        expected = {
            'entries': [{'id': 'patched:p1', 'account': 'patched:cash', 'amount': 2}],
            'balances': {'patched:cash': 2},
        }
        encoded = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        with patch('project.policy.normalize', side_effect=lambda value: 'patched:' + normalize(value)) as patched:
            self.assertEqual(run(rows), expected)
            self.assertEqual(render(rows), encoded)
            self.assertEqual(run_many([rows]), [expected])
            self.assertEqual(render_many([rows]), encoded)
            self.assertEqual(compute(rows), expected)
            self.assertEqual(validate(rows), expected['entries'])
        self.assertEqual(patched.call_count, 12)

    def test_field_errors_precede_domain_errors(self):
        conflict = [
            {'id': 'p1', 'account': 'cash', 'amount': 1},
            {'id': 'P1', 'account': 'cash', 'amount': 2},
        ]
        for entry in (run, render):
            with self.subTest(entry=entry.__name__):
                with self.assertRaisesRegex(ValueError, '^ledger: duplicate id$'):
                    entry(conflict)
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    entry(conflict + [{'id': 'p2', 'account': 'cash', 'amount': True}])
        for entry in (run_many, render_many):
            with self.subTest(entry=entry.__name__):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    entry([[], conflict + [{}]])

    def test_input_validation(self):
        class IntSubclass(int):
            pass

        base = {'id': 'p1', 'account': 'cash', 'amount': 1}
        invalid = [None, [], {}, dict(base, extra=1)]
        for key in ('id', 'account'):
            invalid.extend(dict(base, **{key: value}) for value in (None, 1, '', ' \t\n'))
        invalid.extend(dict(base, amount=value) for value in (True, IntSubclass(1), 1.0, '1', None))
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^ledger: invalid row$'):
                    run([row])
        for entry in (run, render, compute, validate):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(entry=entry.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                        entry(rows)
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^ledger: batches must be a list$'):
                entry(())
            with self.assertRaisesRegex(TypeError, '^ledger: rows must be a list$'):
                entry([[], ()])

    def test_subclasses_order_and_unicode_rendering(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([
            Row(id=' B ', account=' Z ', amount=0),
            Row(id='Straße', account=' É\n" ', amount=-1),
        ])
        result = run(rows)
        self.assertEqual([row['id'] for row in result['entries']], ['b', 'strasse'])
        self.assertEqual(list(result['balances']), ['z', 'é\n"'])
        self.assertEqual(render(rows), json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n')
        self.assertIn('é', render(rows))

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [{'id': ' P1 ', 'account': ' CASH ', 'amount': 2}]
        original = copy.deepcopy(rows)
        expected = run(rows)
        results = run_many([rows, rows])
        results[0]['entries'][0]['account'] = 'changed'
        results[0]['entries'].append({})
        results[0]['balances']['cash'] = 99
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        invalid = rows + [{'id': 'p1', 'account': 'cash', 'amount': 3}]
        before_failure = copy.deepcopy(invalid)
        for entry in (run, render):
            with self.assertRaises(ValueError):
                entry(invalid)
        for entry in (run_many, render_many):
            with self.assertRaises(ValueError):
                entry([rows, invalid])
        self.assertEqual(invalid, before_failure)
        self.assertEqual(rows, original)

    def test_empty_and_batch_order(self):
        self.assertEqual(run([]), {'entries': [], 'balances': {}})
        self.assertEqual(render([]), '{"balances":{},"entries":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        batches = [
            [{'id': 'p1', 'account': 'cash', 'amount': 1}],
            [{'id': 'p1', 'account': 'cash', 'amount': 2}],
            [],
        ]
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))


if __name__ == '__main__':
    unittest.main()
