import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z_ALLOW ', 'target': ' Shared_Resource ', 'value': 7},
            {'id': 'z-allow', 'target': 'shared-resource', 'value': 7},
            {'id': 'B_DENY', 'target': 'SHARED_RESOURCE', 'value': -7},
            {'id': 'A_DENY', 'target': 'shared-resource', 'value': -7},
            {'id': 'zero', 'target': 'earlier', 'value': 0},
        ]
        result = project.run(rows)
        self.assertEqual(result, {'decisions': {
            'earlier': {'rule': 'zero', 'allow': False},
            'shared-resource': {'rule': 'a-deny', 'allow': False},
        }})
        self.assertEqual(list(result['decisions']), ['earlier', 'shared-resource'])
        self.assertEqual(list(result['decisions']['earlier']), ['rule', 'allow'])

    def test_normalization_and_canonical_order(self) -> None:
        rows = [
            {'id': ' STRAßE_A/B  C ', 'target': ' Ω_A/B  C ', 'value': 3},
            {'id': 'straße-a/b  c', 'target': 'ω-a/b  c', 'value': 3},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(policy.normalize(rows[0]['id']), 'strasse-a/b  c')
        self.assertEqual(canonical, [
            {'id': 'strasse-a/b  c', 'target': 'ω-a/b  c', 'value': 3},
            {'id': 'strasse-a/b  c', 'target': 'ω-a/b  c', 'value': 3},
        ])
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], rows[0])
        expected = {'decisions': {'ω-a/b  c': {'rule': 'strasse-a/b  c', 'allow': True}}}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(json.loads(project.render(rows)), expected)

    def test_invalid_inputs_and_error_precedence(self) -> None:
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {}, {'id': 'x', 'target': 'y', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, IntSubclass(1), 1.0, '1'])]:
            for value in values:
                row = {'id': 'x', 'target': 'y', 'value': 1}
                row[field] = value
                invalid_rows.append(row)
        for api in (project.run, project.render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                        api(rows)
            for row in invalid_rows:
                rows = [{'id': 'same', 'target': 'r', 'value': 1},
                        {'id': 'same', 'target': 'r', 'value': 2}, row]
                before = copy.deepcopy(rows)
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_duplicates_are_selected_after_validation(self) -> None:
        rows = [{'id': ' A_B ', 'target': 'resource', 'value': 1},
                {'id': 'a-b', 'target': 'other', 'value': 1}]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (project.run, project.render, engine.compute):
            before = copy.deepcopy(rows)
            with self.assertRaisesRegex(ValueError, '^access-policy: duplicate id$'):
                api(rows)
            self.assertEqual(rows, before)

    def test_subclasses_and_unbounded_integers(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        rows = ListSubclass([
            DictSubclass(id=StrSubclass(' DENY '), target=StrSubclass(' R '), value=-(10 ** 100)),
            {'id': 'allow', 'target': 'r', 'value': 10 ** 101},
        ])
        self.assertEqual(project.run(rows), {'decisions': {'r': {'rule': 'allow', 'allow': True}}})

    def test_empty_and_independent_outputs(self) -> None:
        self.assertEqual(project.run([]), {'decisions': {}})
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(project.render([]), '{"decisions":{}}\n')
        rows = [{'id': ' A ', 'target': ' R ', 'value': 1}]
        before = copy.deepcopy(rows)
        first = project.run(rows)
        second = project.run(rows)
        first['decisions']['r']['rule'] = 'changed'
        first['decisions']['new'] = {}
        self.assertEqual(second, {'decisions': {'r': {'rule': 'a', 'allow': True}}})
        self.assertEqual(project.run(rows), second)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)

    def test_render_and_dynamic_engine_path(self) -> None:
        rows = [{'id': ' Ω ', 'target': ' Z ', 'value': 1}]
        expected = project.run(rows)
        self.assertEqual(project.render(rows), json.dumps(
            expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        original = engine.compute
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('access-policy: invalid row')) as compute:
                with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_outer_validation_and_empty_inputs(self) -> None:
        class ListSubclass(list):
            pass

        for api in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([]), 0):
                with self.subTest(api=api.__name__, batches=batches):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^access-policy: batches must be a list$'):
                            api(batches)
                        compute.assert_not_called()
            for batches in ([], ListSubclass()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(api(batches), [] if api is project.run_many else '')
                    compute.assert_not_called()
        rows = [{'id': 'a', 'target': 'r', 'value': 1}]
        self.assertEqual(project.run_many(ListSubclass([rows])), [project.run(rows)])
        self.assertEqual(project.render_many(ListSubclass([rows])), project.render(rows))

    def test_batch_policies_order_and_render_format(self) -> None:
        batches = [
            [
                {'id': ' Z_ALLOW ', 'target': ' Shared_Resource ', 'value': 7},
                {'id': 'z-allow', 'target': 'shared-resource', 'value': 7},
                {'id': 'B_DENY', 'target': 'SHARED_RESOURCE', 'value': -7},
                {'id': 'A_DENY', 'target': 'shared-resource', 'value': -7},
                {'id': 'zero', 'target': 'earlier', 'value': 0},
            ],
            [],
            [
                {'id': ' STRAßE_A/B  C ', 'target': ' Ω_A/B  C ', 'value': 10 ** 101},
                {'id': 'straße-a/b  c', 'target': 'ω-a/b  c', 'value': 10 ** 101},
                {'id': 'deny', 'target': 'ω-a/b  c', 'value': -(10 ** 100)},
            ],
            [{'id': 'zero', 'target': 'earlier', 'value': 1}],
        ]
        before = copy.deepcopy(batches)
        expected = [
            {'decisions': {
                'earlier': {'rule': 'zero', 'allow': False},
                'shared-resource': {'rule': 'a-deny', 'allow': False},
            }},
            {'decisions': {}},
            {'decisions': {'ω-a/b  c': {'rule': 'strasse-a/b  c', 'allow': True}}},
            {'decisions': {'earlier': {'rule': 'zero', 'allow': True}}},
        ]
        actual = project.run_many(batches)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual[0]['decisions']), ['earlier', 'shared-resource'])
        self.assertEqual(list(actual[0]['decisions']['earlier']), ['rule', 'allow'])
        self.assertEqual(actual, [project.run(rows) for rows in batches])
        rendered = project.render_many(batches)
        self.assertEqual(rendered, ''.join(project.render(rows) for rows in batches))
        self.assertEqual(rendered, ''.join(json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for result in expected))
        self.assertEqual(rendered.count('\n'), len(batches))
        self.assertEqual(batches, before)

    def test_batch_results_have_independent_nested_state(self) -> None:
        rows = [{'id': ' A ', 'target': ' R ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        self.assertIsNot(first[0], first[1])
        self.assertIsNot(first[0]['decisions'], first[1]['decisions'])
        self.assertIsNot(first[0]['decisions']['r'], first[1]['decisions']['r'])
        self.assertIsNot(first[2]['decisions'], first[3]['decisions'])
        first[0]['decisions']['r']['rule'] = 'changed'
        first[0]['decisions']['new'] = {}
        first[2]['decisions']['new'] = {}
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], {'decisions': {}})
        self.assertEqual(second, project.run_many(batches))
        self.assertEqual(batches, before)

    def test_batch_dynamic_engine_path_once_per_member(self) -> None:
        batches = [[], [{'id': 'a', 'target': 'r', 'value': 1}], []]
        original = engine.compute
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, rows in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], rows)

    def test_batch_first_failure_is_atomic_and_preserves_errors(self) -> None:
        class IntSubclass(int):
            pass

        conflicts = [{'id': ' A_B ', 'target': 'r', 'value': 1},
                     {'id': 'a-b', 'target': 'r', 'value': 2}]
        invalid_rows = [None, [], {}, {'id': 'x', 'target': 'y', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, IntSubclass(1), 1.0, '1'])]:
            for value in values:
                row = {'id': 'x', 'target': 'y', 'value': 1}
                row[field] = value
                invalid_rows.append(row)
        failures = [(rows, TypeError, 'rows must be a list') for rows in (None, (), {}, 'rows')]
        failures.append((conflicts, ValueError, 'duplicate id'))
        # Full structural validation must beat the earlier duplicate conflict.
        failures.extend((conflicts + [row], ValueError, 'invalid row') for row in invalid_rows)
        original = engine.compute
        for api in (project.run_many, project.render_many):
            for failing_rows, error_type, message in failures:
                for position in (0, 1, 2):
                    batches = [[] for _ in range(position)] + [failing_rows, None]
                    before = copy.deepcopy(batches)
                    with self.subTest(api=api.__name__, message=message, position=position):
                        with patch.object(engine, 'compute', wraps=original) as compute:
                            with self.assertRaisesRegex(error_type, '^access-policy: ' + message + '$'):
                                api(batches)
                            self.assertEqual(compute.call_count, position + 1)
                            for call, rows in zip(compute.call_args_list, batches):
                                self.assertIs(call.args[0], rows)
                        self.assertEqual(batches, before)

    def test_batch_engine_exception_propagates_unchanged(self) -> None:
        for api in (project.run_many, project.render_many):
            batches = [[], [], []]
            before = copy.deepcopy(batches)
            error = ValueError('access-policy: invalid row')
            with patch.object(engine, 'compute', side_effect=[{'decisions': {}}, error]) as compute:
                with self.assertRaises(ValueError) as raised:
                    api(batches)
                self.assertIs(raised.exception, error)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
