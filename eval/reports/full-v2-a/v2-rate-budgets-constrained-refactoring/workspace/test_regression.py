import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Shared ', 'value': 40},
            {'id': 'a', 'target': 'shared', 'value': 40},
            {'id': 'B', 'target': 'SHARED', 'value': 60},
        ]
        expected = {'remaining': {'shared': 0}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'remaining': {}}])
        self.assertEqual(render_many([rows, []]),
                         '{"remaining":{"shared":0}}\n{"remaining":{}}\n')

    def test_normalization_and_order(self) -> None:
        rows = [
            {'id': ' Straße ', 'target': ' Ω / A  B ', 'value': 0},
            {'id': 'Other', 'target': ' alpha ', 'value': 100},
        ]
        self.assertEqual(policy.normalize(' Straße / Ω  X '), 'strasse / ω  x')
        canonical = validation.validate(rows)
        self.assertEqual([r['id'] for r in canonical], ['strasse', 'other'])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        result = run(rows)
        self.assertEqual(list(result['remaining']), ['alpha', 'ω / a  b'])
        self.assertEqual(render(rows), json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')

    def test_structural_validation_precedes_policy(self) -> None:
        for prefix in (
            [{'id': 'a', 'target': 'x', 'value': 101}],
            [{'id': 'a', 'target': 'x', 'value': 60},
             {'id': 'b', 'target': 'x', 'value': 60}],
            [{'id': 'a', 'target': 'x', 'value': 1},
             {'id': 'A', 'target': 'y', 'value': 1}],
        ):
            rows = prefix + [{'id': 'bad', 'target': 'x', 'value': True}]
            for api in (run, render, engine.compute):
                with self.subTest(api=api.__name__, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                        api(rows)

    def test_validation_types_and_unbounded_integers(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        valid = Rows([Row(id=Text(' A '), target=Text(' X '), value=1)])
        self.assertEqual(run(valid), {'remaining': {'x': 99}})
        for bad in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^rate-budgets: rows must be a list$'):
                run(bad)
        for bad in (True, Integer(1), 1.0, '1', None):
            with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                run([{'id': 'a', 'target': 'x', 'value': bad}])
        for row in ({}, {'id': '', 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': '  ', 'value': 1},
                    {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0}, []):
            with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                run([row])
        huge = [{'id': 'a', 'target': 'x', 'value': 10 ** 1000}]
        self.assertEqual(validation.validate(huge), huge)
        with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
            run(huge)

    def test_domain_errors(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 'x', 'value': -1}], 'invalid cost'),
            ([{'id': 'a', 'target': 'x', 'value': 101}], 'invalid cost'),
            ([{'id': 'a', 'target': 'x', 'value': 60},
              {'id': 'b', 'target': 'x', 'value': 60}], 'exhausted'),
            ([{'id': 'a', 'target': 'x', 'value': 1},
              {'id': 'A', 'target': 'x', 'value': 2}], 'duplicate id'),
        ]
        for rows, message in cases:
            self.assertEqual(validation.validate(rows), [
                {'id': r['id'].casefold(), 'target': r['target'], 'value': r['value']}
                for r in rows])
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^rate-budgets: ' + message + '$'):
                    api(rows)

    def test_fresh_outputs_and_no_mutation(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['remaining']['x'] = -1
        self.assertEqual(results[1], {'remaining': {'x': 99}})
        self.assertEqual(run(rows), results[1])
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        self.assertEqual(validation.validate(rows)[0]['id'], 'a')
        bad = rows + [{'id': 'b', 'target': 'x', 'value': {'nested': []}}]
        before = copy.deepcopy(bad)
        for api in (run, render, run_many, render_many):
            with self.assertRaises(ValueError):
                api([rows, bad] if api in (run_many, render_many) else bad)
            self.assertEqual(bad, before)
            self.assertEqual(rows, original)

    def test_compute_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        for api, argument, count in (
            (run, rows, 1), (render, rows, 1),
            (run_many, [rows, [], rows], 3),
            (render_many, [rows, [], rows], 3),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                self.assertEqual(compute.call_args_list[0].args, (rows,))

    def test_batch_failure_order_and_empty_inputs(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 101}]
        batches = [first, None]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
                    api(batches)
                self.assertEqual(compute.call_count, 1)
            for bad in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^rate-budgets: batches must be a list$'):
                    api(bad)
        self.assertEqual(run([]), {'remaining': {}})
        self.assertEqual(render([]), '{"remaining":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
