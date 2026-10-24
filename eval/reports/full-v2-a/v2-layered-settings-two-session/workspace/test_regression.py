import copy
import json
import unittest
from unittest.mock import call, patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z_ID ', 'target': ' B_Set ', 'value': -2},
            {'id': 'z-id', 'target': 'b-set', 'value': -2},
            {'id': 'a', 'target': 'B_SET', 'value': -2},
            {'id': 'low', 'target': 'b-set', 'value': -9},
            {'id': 'other', 'target': 'a', 'value': -(10 ** 100)},
        ]
        result = run(rows)
        self.assertEqual(result, {'settings': {'a': 'other', 'b-set': 'a'}})
        self.assertEqual(list(result['settings']), ['a', 'b-set'])
        self.assertEqual(run([
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'z', 'target': 'x', 'value': 10 ** 100},
        ]), {'settings': {'x': 'z'}})

    def test_normalization_and_validation_order(self) -> None:
        rows = [
            {'id': ' STRAẞE_A / B ', 'target': ' Ω_X / Y ', 'value': 4},
            {'id': 'strasse-a / b', 'target': 'ω-x / y', 'value': 4},
        ]
        expected = {'id': 'strasse-a / b', 'target': 'ω-x / y', 'value': 4}
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [expected, expected])
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' STRAẞE_A / B '), expected['id'])
        for api in (run, engine.compute):
            self.assertEqual(api(rows), {'settings': {'ω-x / y': 'strasse-a / b'}})
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_invalid_rows_and_containers(self) -> None:
        class IntSubclass(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'x'},
                   {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0}]
        for field, values in (('id', ['', '  ', 1, None]),
                              ('target', ['', '\t', False]),
                              ('value', [True, IntSubclass(1), 1.0, '1', None])):
            for value in values:
                row = {'id': 'a', 'target': 'x', 'value': 1}
                row[field] = value
                invalid.append(row)
        for api in (validation.validate, engine.compute, run, render):
            for value in (None, (), {}, 'rows', iter([])):
                with self.subTest(api=api.__name__, container=type(value)):
                    with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                        api(value)
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                        api([row])

    def test_allowed_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        self.assertEqual(run(Rows([Row(id=Text(' A_B '), target=Text(' X_Y '), value=0)])),
                         {'settings': {'x-y': 'a-b'}})

    def test_duplicate_errors_and_structural_precedence(self) -> None:
        rows = [{'id': ' A ', 'target': 'x', 'value': 1},
                {'id': 'a', 'target': 'y', 'value': 1}]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                api(rows)
            with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                api([rows[0], dict(rows[0], value=2)])
            with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                api(rows + [{'id': 'bad', 'target': 'x', 'value': False}])

    def test_no_mutation_and_output_independence(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        original = copy.deepcopy(rows)
        first, second = run(rows), run(rows)
        first['settings']['x'] = 'changed'
        self.assertEqual(second, {'settings': {'x': 'a'}})
        self.assertEqual(run(rows), second)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        broken = rows + [{'id': 'bad', 'target': 'x', 'value': {'nested': []}}]
        before = copy.deepcopy(broken)
        for api in (validation.validate, engine.compute, run, render):
            with self.assertRaises(ValueError):
                api(broken)
            self.assertEqual(broken, before)

    def test_empty_and_render_contract(self) -> None:
        self.assertEqual(run([]), {'settings': {}})
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(render([]), '{"settings":{}}\n')
        rows = [{'id': 'É', 'target': 'Ω', 'value': 1}]
        self.assertEqual(render(rows), '{"settings":{"ω":"é"}}\n')
        empty = run([])
        empty['settings']['new'] = 'value'
        self.assertEqual(run([]), {'settings': {}})

    def test_shared_compute_is_resolved_at_call_time(self) -> None:
        rows = []
        for api in (run, render):
            with patch.object(engine, 'compute', return_value={'z': {'β': 1, 'a': 2}, 'a': []}) as compute:
                result = api(rows)
                compute.assert_called_once_with(rows)
                if api is render:
                    self.assertEqual(result, '{"a":[],"z":{"a":2,"β":1}}\n')
            with patch.object(engine, 'compute', side_effect=ValueError('layered-settings: invalid row')) as compute:
                with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_outer_inputs_and_empty(self) -> None:
        class Batches(list):
            pass

        for api in (run_many, render_many):
            for value in (None, (), {}, 'batches', iter([])):
                with self.subTest(api=api.__name__, outer=type(value)):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^layered-settings: batches must be a list$'):
                            api(value)
                        compute.assert_not_called()
            for empty in ([], Batches()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(api(empty), [] if api is run_many else '')
                    compute.assert_not_called()
        self.assertEqual(run_many(Batches([[], []])), [{'settings': {}}, {'settings': {}}])
        self.assertEqual(render_many(Batches([[], []])), '{"settings":{}}\n' * 2)

    def test_batch_day_one_policies_and_rendering(self) -> None:
        batches = [[
            {'id': ' Z_ID ', 'target': ' Ω_X / Y ', 'value': -2},
            {'id': 'z-id', 'target': 'ω-x / y', 'value': -2},
            {'id': ' STRAẞE_A / B ', 'target': 'Ω_X / Y', 'value': -2},
            {'id': 'low', 'target': 'ω-x / y', 'value': -9},
            {'id': 'other', 'target': ' A ', 'value': -(10 ** 100)},
        ], [], [{'id': 'z-id', 'target': 'a', 'value': 10 ** 100}]]
        expected = [
            {'settings': {'a': 'other', 'ω-x / y': 'strasse-a / b'}},
            {'settings': {}},
            {'settings': {'a': 'z-id'}},
        ]
        actual = run_many(batches)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual[0]['settings']), ['a', 'ω-x / y'])
        self.assertEqual(actual, [run(rows) for rows in batches])
        self.assertEqual(render_many(batches),
                         '{"settings":{"a":"other","ω-x / y":"strasse-a / b"}}\n'
                         '{"settings":{}}\n{"settings":{"a":"z-id"}}\n')
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))

    def test_batch_member_errors_and_structural_precedence(self) -> None:
        duplicate = [{'id': ' A ', 'target': 'x', 'value': 1},
                     {'id': 'a', 'target': 'y', 'value': 1}]
        cases = [(None, TypeError, 'rows must be a list'),
                 ((), TypeError, 'rows must be a list'),
                 ([{}], ValueError, 'invalid row'),
                 ([{'id': 'a', 'target': 'x', 'value': True}], ValueError, 'invalid row'),
                 (duplicate, ValueError, 'duplicate id'),
                 (duplicate + [{}], ValueError, 'invalid row')]
        for api in (run_many, render_many):
            for member, error_type, message in cases:
                with self.subTest(api=api.__name__, member=member):
                    batches = [[], member, []]
                    before = copy.deepcopy(batches)
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaisesRegex(error_type, '^layered-settings: ' + message + '$'):
                            api(batches)
                        self.assertEqual(compute.call_args_list, [call(batches[0]), call(member)])
                    self.assertEqual(batches, before)

    def test_batch_shared_compute_order_and_atomic_failure(self) -> None:
        batches = [[], [{'id': 'a', 'target': 'x', 'value': 1}], []]
        results = [{'z': {'β': 1, 'a': 2}, 'a': []}, {'settings': {}}, {'settings': {'x': 'a'}}]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', side_effect=copy.deepcopy(results)) as compute:
                actual = api(batches)
                self.assertEqual(compute.call_args_list, [call(rows) for rows in batches])
                for recorded, rows in zip(compute.call_args_list, batches):
                    self.assertIs(recorded.args[0], rows)
                expected = (results if api is run_many else
                            '{"a":[],"z":{"a":2,"β":1}}\n{"settings":{}}\n{"settings":{"x":"a"}}\n')
                self.assertEqual(actual, expected)
            for failure_index in range(len(batches)):
                error = ValueError('layered-settings: invalid row')
                effects = copy.deepcopy(results[:failure_index]) + [error]
                with patch.object(engine, 'compute', side_effect=effects) as compute:
                    with self.assertRaises(ValueError) as caught:
                        api(batches)
                    self.assertIs(caught.exception, error)
                    self.assertEqual(compute.call_args_list,
                                     [call(rows) for rows in batches[:failure_index + 1]])

    def test_batch_no_mutation_and_nested_independence(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first, second = run_many(batches), run_many(batches)
        first[0]['settings']['x'] = 'changed'
        first[2]['settings']['new'] = 'value'
        self.assertEqual(first[1], {'settings': {'x': 'a'}})
        self.assertEqual(first[3], {'settings': {}})
        self.assertEqual(second, [run(rows) for rows in batches])
        self.assertEqual(run_many(batches), second)
        render_many(batches)
        self.assertEqual(batches, before)
        broken = batches + [[{'id': 'bad', 'target': 'x', 'value': {'nested': []}}]]
        before = copy.deepcopy(broken)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                api(broken)
            self.assertEqual(broken, before)


if __name__ == '__main__':
    unittest.main()
