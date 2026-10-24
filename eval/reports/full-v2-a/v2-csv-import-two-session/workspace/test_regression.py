import copy
import json
import unittest
from unittest.mock import call, patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First_ID ', 'target': ' Z_COL ', 'value': 0},
            {'id': 'second', 'target': 'A', 'value': -7},
            {'id': 'FIRST-id', 'target': 'z-col', 'value': 0},
            {'id': 'third', 'target': 'Z_COL', 'value': 10**100},
        ]
        result = project.run(rows)
        self.assertEqual(result, {
            'columns': ['a', 'z-col'],
            'data': [[-7], [0, 10**100]],
            'ids': [['second'], ['first-id', 'third']],
        })
        self.assertEqual(list(result), ['columns', 'data', 'ids'])

    def test_normalization_and_validation_only(self) -> None:
        value = '  STRAẞE_A / B  '
        expected = 'strasse-a / b'
        self.assertEqual(policy.normalize(value), expected)
        rows = [
            {'id': value, 'target': value, 'value': 1},
            {'id': value, 'target': 'other', 'value': 2},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': expected, 'target': expected, 'value': 1},
            {'id': expected, 'target': 'other', 'value': 2},
        ])
        self.assertIsNot(canonical, rows)
        for original, fresh in zip(rows, canonical):
            self.assertIsNot(original, fresh)
            self.assertEqual(list(fresh), ['id', 'target', 'value'])
        for entry in (project.run, project.render, engine.compute):
            with self.subTest(entry=entry):
                with self.assertRaisesRegex(ValueError, '^csv-import: duplicate id$'):
                    entry(rows)

    def test_structural_errors_take_precedence(self) -> None:
        rows = [
            {'id': 'x', 'target': 'a', 'value': 1},
            {'id': 'X', 'target': 'b', 'value': 2},
            {'id': 'bad', 'target': 'a', 'value': True},
        ]
        for entry in (project.run, project.render, engine.compute, validation.validate):
            with self.subTest(entry=entry):
                before = copy.deepcopy(rows)
                with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                    entry(rows)
                self.assertEqual(rows, before)

    def test_invalid_inputs(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, [], {},
                     {'id': 'x', 'target': 'a', 'value': 1, 'extra': 1},
                     {'id': ' ', 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': '\t', 'value': 1},
                     {'id': 1, 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': None, 'value': 1}]
        malformed += [{'id': 'x', 'target': 'a', 'value': v}
                      for v in (True, IntSubclass(1), 1.0, '1', None)]
        for entry in (project.run, project.render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(entry=entry, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                        entry(rows)
            for row in malformed:
                with self.subTest(entry=entry, row=row):
                    with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                        entry([row])

    def test_allowed_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' X_Y '), target=Text(' A_B '), value=-1)])
        self.assertEqual(project.run(rows), {
            'columns': ['a-b'], 'data': [[-1]], 'ids': [['x-y']]})

    def test_empty_and_independent_outputs(self) -> None:
        self.assertEqual(project.run([]), {'columns': [], 'data': [], 'ids': []})
        rows = [{'id': 'x', 'target': 'a', 'value': 1}]
        before = copy.deepcopy(rows)
        first = project.run(rows)
        second = project.run(rows)
        first['columns'].append('changed')
        first['data'][0].append(2)
        first['ids'][0].append('changed')
        self.assertEqual(rows, before)
        self.assertEqual(second, {'columns': ['a'], 'data': [[1]], 'ids': [['x']]})
        self.assertEqual(project.run(rows), second)
        empty = project.run([])
        empty['columns'].append('changed')
        self.assertEqual(empty['data'], [])
        self.assertEqual(empty['ids'], [])
        self.assertEqual(project.run([]), {'columns': [], 'data': [], 'ids': []})

    def test_render_exact_unicode_json(self) -> None:
        rows = [{'id': 'É_ID', 'target': '서울', 'value': -2}]
        self.assertEqual(project.render(rows),
                         '{"columns":["서울"],"data":[[-2]],"ids":[["é-id"]]}\n')
        self.assertEqual(project.render(rows), json.dumps(
            project.run(rows), ensure_ascii=False, sort_keys=True,
            separators=(',', ':')) + '\n')

    def test_compute_resolved_at_call_time_once(self) -> None:
        for entry in (project.run, project.render):
            with self.subTest(entry=entry):
                rows = []
                with patch.object(engine, 'compute', return_value={'z': {'b': 1, 'a': 2}}) as compute:
                    result = entry(rows)
                    compute.assert_called_once_with(rows)
                    self.assertIs(compute.call_args.args[0], rows)
                    if entry is project.render:
                        self.assertEqual(result, '{"z":{"a":2,"b":1}}\n')
                    else:
                        self.assertEqual(result, {'z': {'b': 1, 'a': 2}})

    def test_batch_outer_inputs_and_empty(self) -> None:
        for entry in (project.run_many, project.render_many):
            with self.subTest(entry=entry):
                for batches in (None, (), {}, 'batches', iter([]), 0):
                    with self.subTest(batches=batches):
                        with patch.object(engine, 'compute') as compute:
                            with self.assertRaisesRegex(TypeError, '^csv-import: batches must be a list$'):
                                entry(batches)
                            compute.assert_not_called()
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(entry([]), [] if entry is project.run_many else '')
                    compute.assert_not_called()

    def test_batch_policies_order_and_exact_render(self) -> None:
        class Batches(list):
            pass

        class Rows(list):
            pass

        batches = Batches([
            Rows([
                {'id': ' STRAẞE_ID ', 'target': ' Z_COL ', 'value': 0},
                {'id': 'other', 'target': 'A', 'value': -7},
                {'id': 'strasse-id', 'target': 'z-col', 'value': 0},
                {'id': 'last', 'target': 'Z_COL', 'value': 10**100},
            ]),
            [{'id': 'STRAẞE_ID', 'target': '서울', 'value': -2}],
            [],
        ])
        before = copy.deepcopy(batches)
        expected = [
            {'columns': ['a', 'z-col'], 'data': [[-7], [0, 10**100]],
             'ids': [['other'], ['strasse-id', 'last']]},
            {'columns': ['서울'], 'data': [[-2]], 'ids': [['strasse-id']]},
            {'columns': [], 'data': [], 'ids': []},
        ]
        results = project.run_many(batches)
        self.assertEqual(results, expected)
        for result in results:
            self.assertEqual(list(result), ['columns', 'data', 'ids'])
        expected_render = ''.join(json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for result in expected)
        self.assertEqual(project.render_many(batches), expected_render)
        self.assertEqual(project.render_many(batches), ''.join(project.render(rows) for rows in batches))
        self.assertEqual(batches, before)

    def test_batch_nested_results_are_independent(self) -> None:
        rows = [{'id': ' X_ID ', 'target': ' A_COL ', 'value': 1}]
        empty = []
        batches = [rows, rows, empty, empty]
        before = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        for key in ('columns', 'data', 'ids'):
            self.assertIsNot(first[0][key], first[1][key])
            self.assertIsNot(first[2][key], first[3][key])
        for key in ('data', 'ids'):
            self.assertIsNot(first[0][key][0], first[1][key][0])
            first[0][key][0].append('changed')
        first[0]['columns'].append('changed')
        for key in ('columns', 'data', 'ids'):
            first[2][key].append('changed')
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], second[3])
        self.assertEqual(project.run_many(batches), second)
        self.assertEqual(batches, before)

    def test_batch_compute_resolved_once_per_member_in_order(self) -> None:
        batches = [[], [{'id': 'x', 'target': 'a', 'value': 1}], []]
        for entry in (project.run_many, project.render_many):
            with self.subTest(entry=entry):
                values = [{'z': 3}, {'서울': -1}, {'a': 0}]
                with patch.object(engine, 'compute', side_effect=values) as compute:
                    result = entry(batches)
                self.assertEqual(compute.call_args_list, [call(rows) for rows in batches])
                for invocation, rows in zip(compute.call_args_list, batches):
                    self.assertIs(invocation.args[0], rows)
                self.assertEqual(result, values if entry is project.run_many else
                                 '{"z":3}\n{"서울":-1}\n{"a":0}\n')

    def test_batch_first_failure_and_input_preservation(self) -> None:
        valid = [{'id': 'ok', 'target': 'a', 'value': 1}]
        duplicate = [
            {'id': 'X_ID', 'target': 'a', 'value': 1},
            {'id': ' x-id ', 'target': 'b', 'value': 2},
        ]
        malformed = {'id': 'bad', 'target': 'a', 'value': True}
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([malformed], ValueError, 'invalid row'),
            (duplicate, ValueError, 'duplicate id'),
            (duplicate + [malformed], ValueError, 'invalid row'),
        ]
        for entry in (project.run_many, project.render_many):
            for failing, error, message in cases:
                with self.subTest(entry=entry, failing=failing):
                    batches = [valid, failing, None]
                    before = copy.deepcopy(batches)
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaisesRegex(error, '^csv-import: ' + message + '$'):
                            entry(batches)
                        self.assertEqual(compute.call_count, 2)
                        self.assertIs(compute.call_args_list[0].args[0], valid)
                        self.assertIs(compute.call_args_list[1].args[0], failing)
                    self.assertEqual(batches, before)

    def test_batch_propagates_original_failure_atomically(self) -> None:
        batches = [[], [], []]
        for entry in (project.run_many, project.render_many):
            for failure_index in (0, 1):
                with self.subTest(entry=entry, failure_index=failure_index):
                    error = RuntimeError('sentinel')
                    effects = [{'columns': [], 'data': [], 'ids': []}] * failure_index + [error]
                    with patch.object(engine, 'compute', side_effect=effects) as compute:
                        with self.assertRaises(RuntimeError) as caught:
                            entry(batches)
                        self.assertIs(caught.exception, error)
                        self.assertEqual(compute.call_count, failure_index + 1)
                    self.assertEqual(batches, [[], [], []])


if __name__ == '__main__':
    unittest.main()
