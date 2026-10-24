import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def assert_error(self, api, rows, error_type, message):
        before = copy.deepcopy(rows)
        with self.assertRaises(error_type) as caught:
            api(rows)
        self.assertEqual(str(caught.exception), 'calendar-windows: ' + message)
        self.assertEqual(rows, before)

    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A_B ', 'target': ' Room_É ', 'value': 23},
            {'id': 'a-b', 'target': 'room-é', 'value': 23},
            {'id': 'earlier', 'target': 'ROOM_É', 'value': 22},
        ]
        self.assertEqual(run(rows), {'rooms': {'room-é': [[22, 23, 'earlier'], [23, 24, 'a-b']]}})
        self.assert_error(run, rows + [{'id': 'other', 'target': 'room-é', 'value': 23}], ValueError, 'overlap')
        self.assert_error(run, rows + [{'id': 'a-b', 'target': 'elsewhere', 'value': 23}], ValueError, 'duplicate id')

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass
        class Row(dict):
            pass
        class Text(str):
            pass
        rows = Rows([Row(id=Text(' STRAẞE_A / B '), target=Text(' Ω_ROOM / X '), value=999)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'strasse-a / b', 'target': 'ω-room / x', 'value': 999}])
        self.assertEqual(policy.normalize(' STRAẞE_A / B '), 'strasse-a / b')
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        repeated = validation.validate([rows[0], rows[0]])
        self.assertEqual(len(repeated), 2)
        self.assertIsNot(repeated[0], repeated[1])
        self.assertEqual(run(Rows([Row(id=Text(' A '), target=Text(' B '), value=0)])), {'rooms': {'b': [[0, 1, 'a']]}})

    def test_structural_errors(self) -> None:
        class Integer(int):
            pass
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(api=api.__name__, rows=type(rows)):
                    with self.assertRaises(TypeError) as caught:
                        api(rows)
                    self.assertEqual(str(caught.exception), 'calendar-windows: rows must be a list')
            invalid = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 0, 'extra': 0}]
            invalid += [{'id': i, 'target': t, 'value': v} for i, t, v in (
                (' ', 'r', 0), ('a', '\t', 0), (1, 'r', 0), ('a', None, 0),
                ('a', 'r', True), ('a', 'r', Integer(1)), ('a', 'r', 1.0),
            )]
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    self.assert_error(api, [row], ValueError, 'invalid row')

    def test_error_precedence(self) -> None:
        a = {'id': 'a', 'target': 'r', 'value': 0}
        duplicate = {'id': 'a', 'target': 's', 'value': 0}
        overlap = {'id': 'b', 'target': 'r', 'value': 0}
        bad_hour = {'id': 'c', 'target': 'r', 'value': 24}
        for api in (run, render, engine.compute):
            for prefix in ([a, duplicate], [a, overlap], [bad_hour]):
                self.assert_error(api, prefix + [{}], ValueError, 'invalid row')
            self.assert_error(api, [bad_hour, a, duplicate], ValueError, 'duplicate id')
            self.assert_error(api, [a, overlap, bad_hour], ValueError, 'invalid hour')
            self.assert_error(api, [a, overlap], ValueError, 'overlap')
            for hour in (-1, 24, 10 ** 100, -(10 ** 100)):
                self.assert_error(api, [{'id': 'x', 'target': 'r', 'value': hour}], ValueError, 'invalid hour')
        self.assertEqual(validation.validate([bad_hour, a, duplicate, overlap]), [bad_hour, a, duplicate, overlap])

    def test_order_and_independence(self) -> None:
        rows = [
            {'id': 'late', 'target': 'z', 'value': 23},
            {'id': 'early', 'target': 'z', 'value': 0},
            {'id': 'middle', 'target': 'a', 'value': 12},
        ]
        before = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        self.assertEqual(list(first), ['rooms'])
        self.assertEqual(list(first['rooms']), ['a', 'z'])
        self.assertEqual(first['rooms']['z'], [[0, 1, 'early'], [23, 24, 'late']])
        first['rooms']['z'][0][2] = 'changed'
        first['rooms']['a'].append([1, 2, 'new'])
        self.assertEqual(second, run(rows))
        self.assertEqual(rows, before)
        empty = run([])
        empty['rooms']['new'] = []
        self.assertEqual(run([]), {'rooms': {}})

    def test_render(self) -> None:
        rows = [{'id': ' É_A / X ', 'target': ' Ω_R ', 'value': 0}]
        self.assertEqual(render(rows), '{"rooms":{"ω-r":[[0,1,"é-a / x"]]}}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(render([]), '{"rooms":{}}\n')

    def test_compute_instrumentation(self) -> None:
        rows = [{'id': 'a', 'target': 'r', 'value': 0}]
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('calendar-windows: invalid hour')) as compute:
                self.assert_error(api, rows, ValueError, 'invalid hour')
                compute.assert_called_once_with(rows)

    def test_batch_outer_inputs(self) -> None:
        class Batches(list):
            pass
        for api in (run_many, render_many):
            for batches in (None, (), {}, '', iter([]), ([[]] for _ in range(1))):
                with self.subTest(api=api.__name__, outer=type(batches)):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaises(TypeError) as caught:
                            api(batches)
                        self.assertEqual(str(caught.exception), 'calendar-windows: batches must be a list')
                        compute.assert_not_called()
            with patch.object(engine, 'compute') as compute:
                self.assertEqual(api([]), [] if api is run_many else '')
                compute.assert_not_called()
            self.assertEqual(api(Batches([[]])), [{'rooms': {}}] if api is run_many else '{"rooms":{}}\n')

    def test_batch_composition(self) -> None:
        rows = [
            {'id': ' Late_A / X ', 'target': ' Z_ROOM ', 'value': 23},
            {'id': 'late-a / x', 'target': 'z-room', 'value': 23},
            {'id': ' Early ', 'target': 'z_room', 'value': 0},
            {'id': ' STRAẞE_A ', 'target': ' Ω_ROOM ', 'value': 12},
        ]
        batches = [rows, [], [{'id': 'late-a / x', 'target': 'z-room', 'value': 23}]]
        before = copy.deepcopy(batches)
        expected = [
            {'rooms': {'z-room': [[0, 1, 'early'], [23, 24, 'late-a / x']], 'ω-room': [[12, 13, 'strasse-a']]}},
            {'rooms': {}},
            {'rooms': {'z-room': [[23, 24, 'late-a / x']]}},
        ]
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(list(run_many(batches)[0]['rooms']), ['z-room', 'ω-room'])
        self.assertEqual(render_many(batches), ''.join(render(member) for member in batches))
        self.assertEqual(render_many(batches), ''.join(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for result in expected
        ))
        self.assertEqual(batches, before)

    def test_batch_policy_errors(self) -> None:
        a = {'id': ' A ', 'target': ' R ', 'value': 0}
        duplicate = {'id': 'a', 'target': 's', 'value': 0}
        overlap = {'id': 'b', 'target': 'r', 'value': 0}
        bad_hour = {'id': 'c', 'target': 'r', 'value': 24}
        cases = [(member, TypeError, 'rows must be a list') for member in (None, (), {}, 'rows')]
        invalid = [None, [], {}, {'id': 'a', 'target': 'r', 'value': True},
                   {'id': ' ', 'target': 'r', 'value': 0},
                   {'id': 'a', 'target': None, 'value': 0},
                   {'id': 'a', 'target': 'r', 'value': 0, 'extra': 1}]
        cases += [([row], ValueError, 'invalid row') for row in invalid]
        cases += [
            ([a, duplicate, {}], ValueError, 'invalid row'),
            ([a, overlap, {}], ValueError, 'invalid row'),
            ([bad_hour, {}], ValueError, 'invalid row'),
            ([bad_hour, a, duplicate], ValueError, 'duplicate id'),
            ([a, overlap, bad_hour], ValueError, 'invalid hour'),
            ([a, overlap], ValueError, 'overlap'),
            ([{'id': 'x', 'target': 'r', 'value': -1}], ValueError, 'invalid hour'),
        ]
        for api in (run_many, render_many):
            for member, error_type, message in cases:
                with self.subTest(api=api.__name__, member=member):
                    batches = [[a], member, [{}]]
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        self.assert_error(api, batches, error_type, message)
                        self.assertEqual(compute.call_count, 2)
                        self.assertIs(compute.call_args_list[0].args[0], batches[0])
                        self.assertIs(compute.call_args_list[1].args[0], member)

    def test_batch_compute_instrumentation(self) -> None:
        batches = [[], [{'id': 'a', 'target': 'r', 'value': 0}], []]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, member in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], member)
            for index in range(len(batches)):
                error = ValueError('calendar-windows: injected failure')
                effects = [{'rooms': {}} for _ in range(index)] + [error]
                with patch.object(engine, 'compute', side_effect=effects) as compute:
                    before = copy.deepcopy(batches)
                    with self.assertRaises(ValueError) as caught:
                        api(batches)
                    self.assertIs(caught.exception, error)
                    self.assertEqual(compute.call_count, index + 1)
                    self.assertEqual(batches, before)

    def test_batch_nested_independence(self) -> None:
        rows = [{'id': 'a', 'target': 'r', 'value': 0}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        self.assertIsNot(first[0], first[1])
        self.assertIsNot(first[0]['rooms'], first[1]['rooms'])
        self.assertIsNot(first[0]['rooms']['r'], first[1]['rooms']['r'])
        self.assertIsNot(first[0]['rooms']['r'][0], first[1]['rooms']['r'][0])
        first[0]['rooms']['r'][0][2] = 'changed'
        first[0]['rooms']['r'].append([1, 2, 'new'])
        first[2]['rooms']['new'] = []
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], {'rooms': {}})
        self.assertEqual(second, run_many(batches))
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
