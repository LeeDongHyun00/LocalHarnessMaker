import copy
import json
import unittest
from unittest.mock import call, patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Leaf_ß ', 'target': ' Mid ', 'value': 8},
            {'id': 'MID', 'target': ' Root ', 'value': 4},
            {'id': 'ROOT', 'target': 'root', 'value': 0},
            {'id': 'leaf-ss', 'target': 'mid', 'value': 8},
            {'id': ' Other ', 'target': 'OTHER', 'value': 10**100},
        ]
        expected = {'dirty': ['leaf-ss', 'mid', 'root'], 'clean': ['other']}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(engine.compute(rows), expected)

    def test_normalization_and_canonical_validation(self) -> None:
        rows = [
            {'id': ' Straße_X / Y ', 'target': ' STRASSE_X / Y ', 'value': -2},
            {'id': 'STRASSE-X / Y', 'target': 'different', 'value': 3},
        ]
        self.assertEqual(policy.normalize(' Straße_X / Y '), 'strasse-x / y')
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse-x / y', 'target': 'strasse-x / y', 'value': -2},
            {'id': 'strasse-x / y', 'target': 'different', 'value': 3},
        ])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(project.run([rows[0] | {'value': 1}]),
                         {'dirty': [], 'clean': ['strasse-x / y']})

    def test_structural_errors_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, {}, {'id': 'x', 'target': 'x'},
                     {'id': 'x', 'target': 'x', 'value': 1, 'extra': 1}]
        for field, values in [('id', ['', '  ', 1, None]),
                              ('target', ['', '\t', 1, None]),
                              ('value', [True, 1.0, IntSubclass(1), None])]:
            for value in values:
                malformed.append({'id': 'x', 'target': 'x', 'value': 1} | {field: value})
        prior_errors = [
            [{'id': 'x', 'target': 'x', 'value': -1}],
            [{'id': 'x', 'target': 'absent', 'value': 1}],
            [{'id': 'x', 'target': 'y', 'value': 1},
             {'id': 'y', 'target': 'x', 'value': 1}],
            [{'id': 'x', 'target': 'x', 'value': 1},
             {'id': 'X', 'target': 'x', 'value': 2}],
        ]
        for api in (project.run, project.render, engine.compute, validation.validate):
            for bad in malformed:
                for prior in prior_errors:
                    with self.subTest(api=api.__name__, bad=bad, prior=prior):
                        with self.assertRaisesRegex(ValueError, '^cache-invalidation: invalid row$'):
                            api(prior + [bad])
            for bad in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^cache-invalidation: rows must be a list$'):
                    api(bad)

    def test_supported_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' X_Y '), target=Text('x-y'), value=1)])
        self.assertEqual(project.run(rows), {'dirty': [], 'clean': ['x-y']})

    def test_domain_error_order(self) -> None:
        cycle = [{'id': 'a', 'target': 'b', 'value': 1},
                 {'id': 'b', 'target': 'a', 'value': 1}]
        missing = {'id': 'c', 'target': 'absent', 'value': 1}
        negative = {'id': 'd', 'target': 'd', 'value': -10**100}
        duplicate = {'id': 'A', 'target': 'a', 'value': 1}
        cases = [(cycle, 'cycle'), (cycle + [missing], 'missing dependency'),
                 (cycle + [missing, negative], 'negative generation'),
                 (cycle + [missing, negative, duplicate], 'duplicate id')]
        for api in (project.run, project.render, engine.compute):
            for rows, message in cases:
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^cache-invalidation: ' + message + '$'):
                        api(rows)

    def test_empty_and_output_independence(self) -> None:
        first = project.run([])
        second = project.run([])
        self.assertEqual(first, {'dirty': [], 'clean': []})
        self.assertEqual(list(first), ['dirty', 'clean'])
        self.assertIsNot(first['dirty'], first['clean'])
        first['dirty'].append('changed')
        self.assertEqual(second, {'dirty': [], 'clean': []})
        self.assertEqual(project.run([]), second)
        self.assertEqual(project.render([]), '{"clean":[],"dirty":[]}\n')

    def test_inputs_unchanged_on_success_and_failure(self) -> None:
        cases = [
            [{'id': ' X ', 'target': 'x', 'value': 0}],
            [{'id': 'x', 'target': 'x', 'value': -1}],
            [{'id': 'x', 'target': 'absent', 'value': 1}],
            [{'id': 'x', 'target': 'y', 'value': 1}, {'id': 'y', 'target': 'x', 'value': 1}],
            [{'id': 'x', 'target': 'x', 'value': 1}, {'id': 'X', 'target': 'x', 'value': 2}],
            [{'id': 'x', 'target': 'x', 'value': {'nested': [1, 2]}}],
        ]
        for api in (project.run, project.render, engine.compute, validation.validate):
            for rows in cases:
                original = copy.deepcopy(rows)
                try:
                    result = api(rows)
                except ValueError:
                    pass
                else:
                    if isinstance(result, dict):
                        result['dirty'].append('changed')
                    elif isinstance(result, list):
                        result[0]['id'] = 'changed'
                self.assertEqual(rows, original)

    def test_render_and_runtime_instrumentation(self) -> None:
        rows = [{'id': ' 한_글 ', 'target': '한-글', 'value': 1}]
        expected = {'dirty': [], 'clean': ['한-글']}
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                result = api(rows)
                compute.assert_called_once_with(rows)
                if api is project.render:
                    self.assertEqual(result, json.dumps(expected, ensure_ascii=False,
                                     sort_keys=True, separators=(',', ':')) + '\n')
                else:
                    self.assertEqual(result, expected)
        nested = {'z': [{'z': 1, 'a': {'z': 2, 'a': 3}}], 'a': []}
        with patch.object(engine, 'compute', return_value=nested) as compute:
            self.assertEqual(project.render(rows), '{"a":[],"z":[{"a":{"a":3,"z":2},"z":1}]}\n')
            compute.assert_called_once_with(rows)

    def test_long_dependency_chain(self) -> None:
        rows = [{'id': str(i), 'target': str(i + 1), 'value': 1} for i in range(2000)]
        rows.append({'id': '2000', 'target': '2000', 'value': 0})
        self.assertEqual(project.run(rows), {'dirty': sorted(str(i) for i in range(2001)), 'clean': []})

    def test_batch_composition_and_order(self) -> None:
        batches = [
            [{'id': ' Leaf_ß / Z ', 'target': ' Root ', 'value': 5},
             {'id': 'ROOT', 'target': 'root', 'value': 0},
             {'id': 'leaf-ss / z', 'target': 'root', 'value': 5},
             {'id': ' 한_글 ', 'target': '한-글', 'value': 1}],
            [],
            [{'id': ' Z ', 'target': 'z', 'value': 1},
             {'id': 'A', 'target': 'a', 'value': 1}],
        ]
        expected = [
            {'dirty': ['leaf-ss / z', 'root'], 'clean': ['한-글']},
            {'dirty': [], 'clean': []},
            {'dirty': [], 'clean': ['a', 'z']},
        ]
        original = copy.deepcopy(batches)
        self.assertEqual(project.run_many(batches), expected)
        self.assertEqual(project.render_many(batches),
                         ''.join(project.render(rows) for rows in batches))
        self.assertEqual(project.render_many(batches),
                         ''.join(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                            separators=(',', ':')) + '\n'
                                 for result in expected))
        self.assertEqual(batches, original)

    def test_batch_outer_validation_and_subclasses(self) -> None:
        class Batches(list):
            pass

        for api, empty in ((project.run_many, []), (project.render_many, '')):
            for batches in ([], Batches()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(api(batches), empty)
                    compute.assert_not_called()
            for bad in (None, (), {}, 'batches', iter([]), 1):
                with patch.object(engine, 'compute') as compute:
                    with self.assertRaisesRegex(TypeError, '^cache-invalidation: batches must be a list$'):
                        api(bad)
                    compute.assert_not_called()
            batches = Batches([Batches([{'id': ' X_Y ', 'target': 'x-y', 'value': 1}])])
            expected = [{'dirty': [], 'clean': ['x-y']}]
            self.assertEqual(api(batches), expected if api is project.run_many
                             else '{"clean":["x-y"],"dirty":[]}\n')

    def test_batch_runtime_compute_path(self) -> None:
        batches = [[{'id': ' X ', 'target': 'x', 'value': 1}], [], []]
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_args_list, [call(rows) for rows in batches])
                for invocation, rows in zip(compute.call_args_list, batches):
                    self.assertIs(invocation.args[0], rows)
        nested = {'z': [{'z': 1, 'a': {'z': 2, 'a': 3}}], 'a': []}
        with patch.object(engine, 'compute', return_value=nested) as compute:
            self.assertEqual(project.render_many([[], []]),
                             '{"a":[],"z":[{"a":{"a":3,"z":2},"z":1}]}\n' * 2)
            self.assertEqual(compute.call_count, 2)

    def test_batch_first_failure_and_input_preservation(self) -> None:
        cycle = [{'id': 'a', 'target': 'b', 'value': 1},
                 {'id': 'b', 'target': 'a', 'value': 1}]
        missing = {'id': 'c', 'target': 'absent', 'value': 1}
        negative = {'id': 'd', 'target': 'd', 'value': -1}
        duplicate = {'id': 'A', 'target': 'a', 'value': 1}
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            (cycle, ValueError, 'cycle'),
            (cycle + [missing], ValueError, 'missing dependency'),
            (cycle + [missing, negative], ValueError, 'negative generation'),
            (cycle + [missing, negative, duplicate], ValueError, 'duplicate id'),
            (cycle + [missing, negative, duplicate, {'nested': [1, 2]}],
             ValueError, 'invalid row'),
            ([{'id': 'x', 'target': 'x', 'value': True}], ValueError, 'invalid row'),
        ]
        for api in (project.run_many, project.render_many):
            for bad, error, message in cases:
                for position in (0, 1, 2):
                    batches = [[{'id': ' X ', 'target': 'x', 'value': 1}]
                               for _ in range(position)] + [bad, None]
                    original = copy.deepcopy(batches)
                    with self.subTest(api=api.__name__, message=message, position=position):
                        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                            with self.assertRaisesRegex(error, '^cache-invalidation: ' + message + '$'):
                                api(batches)
                            self.assertEqual(compute.call_args_list,
                                             [call(rows) for rows in batches[:position + 1]])
                        self.assertEqual(batches, original)

    def test_batch_exception_propagation(self) -> None:
        for api in (project.run_many, project.render_many):
            error = RuntimeError('compute failed')
            with patch.object(engine, 'compute', side_effect=[{'dirty': [], 'clean': []}, error]) as compute:
                with self.assertRaises(RuntimeError) as caught:
                    api([[], [], []])
                self.assertIs(caught.exception, error)
                self.assertEqual(compute.call_count, 2)

    def test_batch_nested_result_independence(self) -> None:
        rows = [{'id': ' X ', 'target': 'x', 'value': 0},
                {'id': 'Y', 'target': 'y', 'value': 1}]
        batches = [rows, rows, [], []]
        original = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        states = [result for results in (first, second) for result in results]
        self.assertEqual(len({id(result) for result in states}), len(states))
        nested = [values for result in states for values in result.values()]
        self.assertEqual(len({id(values) for values in nested}), len(nested))
        first[0]['dirty'].append('changed')
        first[0]['clean'].clear()
        self.assertEqual(first[1], {'dirty': ['x'], 'clean': ['y']})
        self.assertEqual(second, project.run_many(batches))
        self.assertEqual(batches, original)


if __name__ == '__main__':
    unittest.main()
