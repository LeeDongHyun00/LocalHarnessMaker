import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A_ONE ', 'target': ' Cmd_Name ', 'value': -3},
            {'id': 'a-one', 'target': 'cmd-name', 'value': -3},
            {'id': 'Z', 'target': 'CMD_NAME', 'value': -3},
            {'id': 'low', 'target': 'cmd-name', 'value': -4},
            {'id': 'other', 'target': 'a', 'value': 10 ** 100},
        ]
        result = project.run(rows)
        self.assertEqual(result, {
            'dispatch': {'a': 'other', 'cmd-name': 'z'},
            'shadowed': ['a-one', 'low'],
        })
        self.assertEqual(list(result), ['dispatch', 'shadowed'])
        self.assertEqual(list(result['dispatch']), ['a', 'cmd-name'])

    def test_normalization_and_validation_order(self) -> None:
        class Text(str):
            pass

        class Row(dict):
            pass

        class Rows(list):
            pass

        rows = Rows([
            Row(id=Text(' Straße_A / B '), target=Text(' X_Y / Ω '), value=1),
            Row(id=' STRASSE-A / B ', target='x-y / ω', value=1),
        ])
        canonical = validation.validate(rows)
        expected = {'id': 'strasse-a / b', 'target': 'x-y / ω', 'value': 1}
        self.assertEqual(canonical, [expected, expected])
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße_A / B ')), expected['id'])
        for api in (project.run, engine.compute):
            self.assertEqual(api(rows), {
                'dispatch': {'x-y / ω': 'strasse-a / b'}, 'shadowed': [],
            })
        self.assertEqual(json.loads(project.render(rows)), project.run(rows))

    def test_structural_errors(self) -> None:
        class Integer(int):
            pass

        valid = {'id': 'a', 'target': 'b', 'value': 1}
        malformed = [None, [], {}, {**valid, 'extra': 1},
                     {**valid, 'id': '  '}, {**valid, 'target': '\t'},
                     {**valid, 'id': 3}, {**valid, 'target': None},
                     {**valid, 'value': True}, {**valid, 'value': Integer(1)},
                     {**valid, 'value': 1.0}, {**valid, 'value': {}}]
        for api in (project.run, project.render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(api=api.__name__, rows=repr(rows)):
                    with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                        api(rows)
            for row in malformed:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api([valid, row])

    def test_duplicate_precedence_and_input_preservation(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'one', 'value': 1},
            {'id': 'a', 'target': 'two', 'value': 1},
        ]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (project.run, project.render, engine.compute):
            original = copy.deepcopy(rows)
            with self.assertRaisesRegex(ValueError, '^command-dispatch: duplicate id$'):
                api(rows)
            self.assertEqual(rows, original)
            bad_rows = rows + [{'id': 'later', 'target': 'bad', 'value': {'nested': []}}]
            original = copy.deepcopy(bad_rows)
            with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                api(bad_rows)
            self.assertEqual(bad_rows, original)

    def test_fresh_outputs(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' CMD ', 'value': 0},
            {'id': 'b', 'target': 'cmd', 'value': -1},
        ]
        original = copy.deepcopy(rows)
        first = project.run(rows)
        second = project.run(rows)
        first['dispatch']['cmd'] = 'changed'
        first['shadowed'].append('changed')
        expected = {'dispatch': {'cmd': 'a'}, 'shadowed': ['b']}
        self.assertEqual(second, expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(rows, original)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)

    def test_render_and_shared_compute_path(self) -> None:
        rows = [{'id': 'Ω', 'target': 'Z', 'value': -10 ** 100}]
        expected = project.run(rows)
        self.assertEqual(project.render(rows), json.dumps(
            expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        real_compute = engine.compute
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', wraps=real_compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('observed')) as compute:
                with self.assertRaisesRegex(ValueError, '^observed$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_empty_input(self) -> None:
        expected = {'dispatch': {}, 'shadowed': []}
        self.assertEqual(project.run([]), expected)
        self.assertEqual(engine.compute([]), expected)
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(project.render([]), '{"dispatch":{},"shadowed":[]}\n')
        first, second = project.run([]), project.run([])
        self.assertIsNot(first['dispatch'], second['dispatch'])
        self.assertIsNot(first['shadowed'], second['shadowed'])

    def test_batch_outer_inputs(self) -> None:
        for api in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([]), 1):
                with self.subTest(api=api.__name__, batches=repr(batches)):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^command-dispatch: batches must be a list$'):
                            api(batches)
                        compute.assert_not_called()

    def test_batch_empty_inputs(self) -> None:
        with patch.object(engine, 'compute') as compute:
            self.assertEqual(project.run_many([]), [])
            self.assertEqual(project.render_many([]), '')
            compute.assert_not_called()
        self.assertEqual(project.run_many([[], []]), [
            {'dispatch': {}, 'shadowed': []},
            {'dispatch': {}, 'shadowed': []},
        ])
        self.assertEqual(project.render_many([[], []]),
                         '{"dispatch":{},"shadowed":[]}\n' * 2)

    def test_batch_domain_and_render_order(self) -> None:
        class Batches(list):
            pass

        batches = Batches([
            [
                {'id': ' Straße_A / B ', 'target': ' Z_Ω / X ', 'value': -3},
                {'id': 'STRASSE-A / B', 'target': 'z-ω / x', 'value': -3},
                {'id': 'Ω', 'target': 'z-ω / x', 'value': -3},
                {'id': 'low', 'target': 'z-ω / x', 'value': -10 ** 100},
                {'id': 'a', 'target': ' A ', 'value': 10 ** 100},
            ],
            [],
            [{'id': 'a', 'target': 'another', 'value': 0}],
        ])
        original = copy.deepcopy(batches)
        expected = [
            {'dispatch': {'a': 'a', 'z-ω / x': 'ω'},
             'shadowed': ['low', 'strasse-a / b']},
            {'dispatch': {}, 'shadowed': []},
            {'dispatch': {'another': 'a'}, 'shadowed': []},
        ]
        actual = project.run_many(batches)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual[0]), ['dispatch', 'shadowed'])
        self.assertEqual(list(actual[0]['dispatch']), ['a', 'z-ω / x'])
        self.assertEqual(project.render_many(batches), ''.join(
            json.dumps(result, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':')) + '\n' for result in expected))
        self.assertEqual(batches, original)

    def test_batch_fresh_nested_results(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' CMD ', 'value': 0},
            {'id': 'b', 'target': 'cmd', 'value': -1},
        ]
        batches = [rows, rows, [], []]
        original = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        for index, result in enumerate(first):
            for other in first[index + 1:] + second:
                self.assertIsNot(result, other)
                self.assertIsNot(result['dispatch'], other['dispatch'])
                self.assertIsNot(result['shadowed'], other['shadowed'])
        first[0]['dispatch']['cmd'] = 'changed'
        first[0]['shadowed'].append('changed')
        first[2]['dispatch']['changed'] = 'changed'
        first[2]['shadowed'].append('changed')
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], second[3])
        self.assertEqual(project.run_many(batches), second)
        self.assertEqual(batches, original)

    def test_batch_shared_compute_path(self) -> None:
        batches = [[], [{'id': 'a', 'target': 'b', 'value': 1}], []]
        real_compute = engine.compute
        for api in (project.run_many, project.render_many):
            observed = []

            def compute_member(rows):
                observed.append(rows)
                return real_compute(rows)

            with patch.object(engine, 'compute', side_effect=compute_member) as compute:
                api(batches)
                self.assertEqual(compute.call_count, len(batches))
                self.assertEqual(len(observed), len(batches))
                for actual, expected in zip(observed, batches):
                    self.assertIs(actual, expected)

    def test_batch_errors_and_validation_precedence(self) -> None:
        valid = [{'id': 'a', 'target': 'b', 'value': 1}]
        duplicate = valid + [{'id': ' A ', 'target': 'other', 'value': 1}]
        invalid = {'id': 'bad', 'target': 'b', 'value': {'nested': []}}
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([invalid], ValueError, 'invalid row'),
            (duplicate, ValueError, 'duplicate id'),
            (duplicate + [invalid], ValueError, 'invalid row'),
        ]
        real_compute = engine.compute
        for api in (project.run_many, project.render_many):
            for failing, error_type, message in cases:
                for position in (0, 1):
                    batches = [valid] * position + [failing, [invalid]]
                    original = copy.deepcopy(batches)
                    with self.subTest(api=api.__name__, message=message, position=position):
                        with patch.object(engine, 'compute', wraps=real_compute) as compute:
                            with self.assertRaisesRegex(error_type, '^command-dispatch: ' + message + '$'):
                                api(batches)
                            self.assertEqual(compute.call_count, position + 1)
                            for call, member in zip(compute.call_args_list, batches):
                                self.assertIs(call.args[0], member)
                        self.assertEqual(batches, original)

    def test_batch_propagates_first_compute_exception(self) -> None:
        batches = [[], [], []]
        failure = RuntimeError('observed')
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', side_effect=[
                {'dispatch': {}, 'shadowed': []}, failure,
            ]) as compute:
                with self.assertRaises(RuntimeError) as caught:
                    api(batches)
                self.assertIs(caught.exception, failure)
                self.assertEqual(compute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
