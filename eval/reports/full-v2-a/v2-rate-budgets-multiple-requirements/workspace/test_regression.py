import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'obsolete', 'value': 10**100},
            {'id': 'b', 'target': ' BÜCKET / One ', 'value': 75},
            {'id': 'a', 'target': ' büCKET / one ', 'value': 25},
        ]
        expected = {'remaining': {'bücket / one': 0}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'remaining': {}}])
        self.assertEqual(
            render_many([rows, []]),
            '{"remaining":{"bücket / one":0}}\n{"remaining":{}}\n',
        )

    def test_final_revision_can_lower_cost_and_move_bucket(self) -> None:
        rows = [
            {'id': 'a', 'target': 'old', 'value': 100},
            {'id': 'b', 'target': 'new', 'value': 90},
            {'id': 'a', 'target': 'new', 'value': 5},
        ]
        self.assertEqual(run(rows), {'remaining': {'new': 5}})

    def test_validation_is_structural_and_fresh(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([
            Row(id=Text(' Straße / A  B '), target=Text(' Ω / X '), value=-10**100),
            Row(id='strasse / a  b', target='other', value=4),
        ])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a  b', 'target': 'ω / x', 'value': -10**100},
            {'id': 'strasse / a  b', 'target': 'other', 'value': 4},
        ])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / A  B ')), 'strasse / a  b')
        self.assertEqual(run(rows), {'remaining': {'other': 96}})

    def test_invalid_structure_precedes_domain_errors(self) -> None:
        class Integer(int):
            pass

        malformed = [
            None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 0},
            {'id': '', 'target': 'b', 'value': 1},
            {'id': 'a', 'target': ' \t', 'value': 1},
            {'id': 1, 'target': 'b', 'value': 1},
            {'id': 'a', 'target': None, 'value': 1},
            {'id': 'a', 'target': 'b', 'value': True},
            {'id': 'a', 'target': 'b', 'value': Integer(1)},
            {'id': 'a', 'target': 'b', 'value': 1.0},
            {'id': 'a', 'target': 'b', 'value': {'nested': []}},
        ]
        for bad in malformed:
            rows = [
                {'id': 'a', 'target': 'b', 'value': 101},
                {'id': 'a', 'target': 'c', 'value': -1}, bad,
            ]
            original = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, original)

    def test_cost_errors_precede_aggregation(self) -> None:
        for cost in (-10**100, -1, 101, 10**100):
            rows = [
                {'id': 'a', 'target': 'b', 'value': 100},
                {'id': 'b', 'target': 'b', 'value': 1},
                {'id': 'c', 'target': 'c', 'value': cost},
            ]
            for api in (run, render):
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
                    api(rows)
        with self.assertRaisesRegex(ValueError, '^rate-budgets: exhausted$'):
            run([{'id': 'a', 'target': 'b', 'value': 100},
                 {'id': 'b', 'target': 'b', 'value': 1}])

    def test_output_order_serialization_and_independence(self) -> None:
        rows = [{'id': 'a', 'target': ' Ω ', 'value': 0},
                {'id': 'b', 'target': ' A / B ', 'value': 100}]
        original = copy.deepcopy(rows)
        result = run(rows)
        self.assertEqual(list(result['remaining']), ['a / b', 'ω'])
        self.assertEqual(render(rows), json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        batches = run_many([rows, rows])
        batches[0]['remaining']['ω'] = -1
        result['remaining'].clear()
        self.assertEqual(batches[1], {'remaining': {'a / b': 0, 'ω': 100}})
        self.assertEqual(run(rows), batches[1])
        self.assertEqual(rows, original)

    def test_empty_and_outer_types(self) -> None:
        self.assertEqual(run([]), {'remaining': {}})
        self.assertEqual(render([]), '{"remaining":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for value in (None, (), {}, 'rows', 1):
            for api in (validation.validate, engine.compute, run, render):
                with self.assertRaisesRegex(TypeError, '^rate-budgets: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^rate-budgets: batches must be a list$'):
                    api(value)

    def test_batch_failure_is_ordered_and_atomic(self) -> None:
        good = [{'id': 'a', 'target': 'b', 'value': 1}]
        bad = [{'id': 'a', 'target': 'b', 'value': 101}]
        batches = [good, bad, [{'nested': {'list': []}}]]
        original = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, original)

    def test_every_facade_resolves_compute_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, count in (
            (run, rows, 1), (render, rows, 1),
            (run_many, [rows, rows], 2), (render_many, [rows, rows], 2),
        ):
            with patch.object(engine, 'compute', return_value={'instrumented': {}}) as compute:
                result = api(argument)
                self.assertEqual(compute.call_count, count)
                if api is run:
                    self.assertEqual(result, {'instrumented': {}})
                elif api is render:
                    self.assertEqual(result, '{"instrumented":{}}\n')
                elif api is run_many:
                    self.assertEqual(result, [{'instrumented': {}}, {'instrumented': {}}])
                else:
                    self.assertEqual(result, '{"instrumented":{}}\n' * 2)


if __name__ == '__main__':
    unittest.main()
