import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Old ', 'value': -20},
            {'id': 'z', 'target': ' Shared ', 'value': 7},
            {'id': 'a', 'target': 'shared', 'value': -7},
            {'id': 'b', 'target': 'shared', 'value': -7},
            {'id': 'z', 'target': 'ignored', 'value': 6},
            {'id': 'a', 'target': 'shared', 'value': -7},
        ]
        expected = {'decisions': {'shared': {'rule': 'a', 'allow': False}}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'decisions': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_domain_ties_and_target_order(self) -> None:
        rows = [
            {'id': 'b', 'target': 'z', 'value': 9},
            {'id': 'a', 'target': 'z', 'value': 9},
            {'id': 'zero', 'target': 'a', 'value': 0},
            {'id': 'small', 'target': 'm', 'value': -3},
            {'id': 'huge', 'target': 'm', 'value': 10 ** 100},
        ]
        result = run(rows)
        self.assertEqual(list(result['decisions']), ['a', 'm', 'z'])
        self.assertEqual(result['decisions'], {
            'a': {'rule': 'zero', 'allow': False},
            'm': {'rule': 'huge', 'allow': True},
            'z': {'rule': 'a', 'allow': True},
        })
        self.assertEqual(list(result['decisions']['z']), ['rule', 'allow'])

    def test_canonical_validation_is_fresh_and_preserves_order(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([
            Row(id=Text(' STRAẞE / A  B '), target=Text(' CAFÉ/Δ '), value=-1),
            Row(id='strasse / a  b', target='elsewhere', value=-1),
        ])
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a  b', 'target': 'café/δ', 'value': -1},
            {'id': 'strasse / a  b', 'target': 'elsewhere', 'value': -1},
        ])
        self.assertEqual(policy.normalize(Text(' STRAẞE / A  B ')), 'strasse / a  b')
        self.assertEqual(rows, before)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        for api in (run, engine.compute):
            self.assertEqual(api(rows[:1]), {
                'decisions': {'café/δ': {'rule': 'strasse / a  b', 'allow': False}},
            })

    def test_invalid_rows_through_all_entry_points(self) -> None:
        class Integer(int):
            pass

        malformed = [None, [], {}, {'id': 'x', 'target': 't', 'value': 1, 'extra': 0}]
        for field, values in (
            ('id', ['', '  ', 1, None]),
            ('target', ['', '\t', 1, None]),
            ('value', [True, Integer(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'id': 'x', 'target': 't', 'value': 1}
                row[field] = value
                malformed.append(row)
        for row in malformed:
            rows = [{'id': 'ok', 'target': 't', 'value': 1}, row]
            before = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render,
                        lambda value: run_many([value]), lambda value: render_many([value])):
                with self.subTest(row=row, api=api):
                    with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_container_validation_and_empty_results(self) -> None:
        for api in (validation.validate, engine.compute, run, render):
            for value in (None, {}, (), 'rows'):
                with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                    api(value)
        for api in (run_many, render_many):
            for value in (None, {}, (), 'batches'):
                with self.assertRaisesRegex(TypeError, '^access-policy: batches must be a list$'):
                    api(value)
            with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                api([()])
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(run([]), {'decisions': {}})
        self.assertEqual(render([]), '{"decisions":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_ambiguity_and_structural_error_precedence(self) -> None:
        rows = [
            {'id': 'x', 'target': 'a', 'value': 1},
            {'id': ' X ', 'target': 'b', 'value': 1},
            {'id': 'x', 'target': 'c', 'value': 2},
        ]
        for api in (engine.compute, run, render,
                    lambda value: run_many([value]), lambda value: render_many([value])):
            with self.assertRaisesRegex(ValueError, '^access-policy: ambiguous id$'):
                api(rows)
            with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                api(rows + [{'id': 'bad'}])

    def test_selection_keeps_first_id_position(self) -> None:
        rows = [
            {'id': 'z', 'target': 'old', 'value': 1},
            {'id': 'a', 'target': 'other', 'value': 2},
            {'id': 'z', 'target': 'new', 'value': 3},
        ]
        with patch('project.engine.resolve', return_value={'decisions': {}}) as resolve:
            engine.compute(rows)
        self.assertEqual(resolve.call_args.args[0], [rows[2], rows[1]])

    def test_render_exact_unicode_json(self) -> None:
        rows = [{'id': ' É ', 'target': ' Δ / X  Y ', 'value': 2}]
        expected = '{"decisions":{"δ / x  y":{"allow":true,"rule":"é"}}}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render(rows), json.dumps(
            run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': 'x', 'target': 't', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['decisions']['t']['allow'] = False
        results[0]['decisions']['extra'] = {}
        expected = {'decisions': {'t': {'rule': 'x', 'allow': True}}}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)

    def test_runtime_compute_instrumentation(self) -> None:
        first = [{'id': 'a', 'target': 't', 'value': 1}]
        second = [{'id': 'b', 'target': 't', 'value': -1}]
        for api, argument, expected_calls in (
            (run, first, [first]), (render, first, [first]),
            (run_many, [first, second], [first, second]),
            (render_many, [first, second], [first, second]),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual([call.args[0] for call in compute.call_args_list], expected_calls)
        with patch.object(engine, 'compute', return_value={'instrumented': 'é'}) as compute:
            self.assertEqual(run(first), {'instrumented': 'é'})
            self.assertEqual(render(first), '{"instrumented":"é"}\n')
            self.assertEqual(compute.call_count, 2)

    def test_batches_stop_at_first_failure_without_mutation(self) -> None:
        first = [{'id': 'a', 'target': 't', 'value': 1}]
        ambiguous = [
            {'id': 'x', 'target': 't', 'value': 2},
            {'id': 'x', 'target': 'u', 'value': 2},
        ]
        batches = [first, ambiguous, [{'invalid': ['nested']}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^access-policy: ambiguous id$'):
                    api(batches)
                self.assertEqual([call.args[0] for call in compute.call_args_list], batches[:2])
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
