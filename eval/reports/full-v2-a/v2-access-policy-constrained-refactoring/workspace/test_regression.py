import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation
from project.api import _legacy_render, _legacy_run


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B ', 'target': ' Z ', 'value': 9},
            {'id': 'b', 'target': 'z', 'value': 9},
            {'id': 'C', 'target': 'z', 'value': -9},
            {'id': 'A', 'target': 'Z', 'value': -9},
            {'id': 'zero', 'target': 'a', 'value': 0},
            {'id': 'weak', 'target': 'z', 'value': -8},
        ]
        expected = {'decisions': {
            'a': {'rule': 'zero', 'allow': False},
            'z': {'rule': 'a', 'allow': False},
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['decisions']), ['a', 'z'])
        self.assertEqual(list(run(rows)['decisions']['z']), ['rule', 'allow'])
        self.assertEqual(run_many([rows, []]), [expected, {'decisions': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation_order(self) -> None:
        rows = [
            {'id': ' Straße / A ', 'target': ' É / X  Y ', 'value': 2},
            {'id': ' Z ', 'target': ' Other ', 'value': -3},
            {'id': 'STRASSE / a', 'target': 'é / x  y', 'value': 2},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a', 'target': 'é / x  y', 'value': 2},
            {'id': 'z', 'target': 'other', 'value': -3},
            {'id': 'strasse / a', 'target': 'é / x  y', 'value': 2},
        ])
        self.assertEqual(policy.normalize(' Straße / A '), 'strasse / a')
        self.assertIsNot(canonical[0], canonical[2])
        for actual, original in zip(canonical, rows):
            self.assertIsNot(actual, original)
        expected = {'decisions': {
            'other': {'rule': 'z', 'allow': False},
            'é / x  y': {'rule': 'strasse / a', 'allow': True},
        }}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows]), serialized)

    def test_structural_validation_precedes_duplicates(self) -> None:
        conflict = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'A', 'target': 'y', 'value': 1},
        ]
        self.assertEqual(len(validation.validate(conflict)), 2)
        for api in (run, render, engine.compute, _legacy_run, _legacy_render):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^access-policy: duplicate id$'):
                    api(conflict)
                with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                    api(conflict + [{'id': 'bad'}])
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                    api([conflict + [{}]])

    def test_invalid_structures(self) -> None:
        class IntSubclass(int):
            pass

        invalid = [None, [], {},
                   {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0}]
        for field, values in (
            ('id', ['', ' \t\n', None, 1]),
            ('target', ['', ' \t\n', None, 1]),
            ('value', [True, False, IntSubclass(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'id': 'a', 'target': 'x', 'value': 1}
                row[field] = value
                invalid.append(row)
        for row in invalid:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                        api([row])
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                    api([[row]])

    def test_outer_types_and_empty_inputs(self) -> None:
        for value in (None, (), {}, 'rows', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                        api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^access-policy: batches must be a list$'):
                    api(value)
        self.assertEqual(run([]), {'decisions': {}})
        self.assertEqual(engine.compute([]), {'decisions': {}})
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(render([]), '{"decisions":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_subclasses_and_unbounded_integers(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([
            Row(id=Text(' A '), target=Text(' X '), value=10 ** 100),
            Row(id='b', target='x', value=-(10 ** 101)),
        ])
        expected = {'decisions': {'x': {'rule': 'b', 'allow': False}}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render_many(Rows([rows])), render(rows))

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        batches = [rows, rows]
        first, second = run_many(batches)
        subsequent = run(rows)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        first['decisions']['x']['rule'] = 'changed'
        first['decisions']['new'] = {}
        self.assertEqual(second, {'decisions': {'x': {'rule': 'a', 'allow': True}}})
        self.assertEqual(subsequent, second)
        self.assertEqual(run(rows), second)
        self.assertIsNot(subsequent['decisions']['x'], second['decisions']['x'])
        self.assertEqual(rows, before)
        render_many(batches)
        self.assertEqual(rows, before)
        malformed = rows + [{'id': 'bad', 'target': 'x', 'value': {'nested': []}}]
        failing = [rows, malformed, rows]
        snapshot = copy.deepcopy(failing)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                api(failing)
            self.assertEqual(failing, snapshot)

    def test_runtime_compute_delegation(self) -> None:
        batches = [[{'id': 'a', 'target': 'x', 'value': 1}], []]
        for api in (run, render, _legacy_run, _legacy_render):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(batches[0])
                    compute.assert_called_once_with(batches[0])
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(batches)
                    self.assertEqual(compute.call_count, 2)
                    self.assertIs(compute.call_args_list[0].args[0], batches[0])
                    self.assertIs(compute.call_args_list[1].args[0], batches[1])

    def test_batch_failure_order_and_exception_identity(self) -> None:
        conflict = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'a', 'target': 'x', 'value': 2},
        ]
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^access-policy: duplicate id$'):
                        api([[], conflict, [{}]])
                    self.assertEqual(compute.call_count, 2)
                error = ValueError('instrumented error')
                with patch.object(engine, 'compute', side_effect=error) as compute:
                    with self.assertRaises(ValueError) as caught:
                        api([[], []])
                    self.assertIs(caught.exception, error)
                    compute.assert_called_once_with([])


if __name__ == '__main__':
    unittest.main()
