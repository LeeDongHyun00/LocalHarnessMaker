import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Booking ', 'target': 'Old', 'value': 99},
            {'id': 'neighbor', 'target': 'Room', 'value': 5},
            {'id': 'BOOKING', 'target': ' ROOM ', 'value': 4},
        ]
        expected = {'rooms': {'room': [[4, 5, 'booking'], [5, 6, 'neighbor']]}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'rooms': {}}])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + '{"rooms":{}}\n')

    def test_obsolete_clash_and_room_are_discarded(self) -> None:
        rows = [
            {'id': 'a', 'target': 'room', 'value': 2},
            {'id': 'b', 'target': 'room', 'value': 2},
            {'id': 'A', 'target': 'new', 'value': 1},
        ]
        self.assertEqual(project.run(rows), {'rooms': {
            'new': [[1, 2, 'a']], 'room': [[2, 3, 'b']]}})

    def test_structural_validation_precedes_selection_and_domain(self) -> None:
        for first_hour in (2, 10**100):
            rows = [
                {'id': 'a', 'target': 'room', 'value': first_hour},
                {'id': 'a', 'target': 'room', 'value': 3},
                {'id': 'broken', 'target': 'room', 'value': True},
            ]
            for api in (project.run, project.render, engine.compute):
                with self.subTest(api=api.__name__, hour=first_hour):
                    with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid row$'):
                        api(rows)

    def test_validation_keeps_all_revisions_and_unbounded_integers(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' ROOM ', 'value': 10**100},
            {'id': 'a', 'target': 'elsewhere', 'value': -10**100},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a', 'target': 'room', 'value': 10**100},
            {'id': 'a', 'target': 'elsewhere', 'value': -10**100},
        ])
        self.assertIsNot(canonical, rows)
        self.assertTrue(all(a is not b for a, b in zip(canonical, rows)))
        with patch.object(engine, 'resolve', return_value={}) as resolve:
            engine.compute(rows + [{'id': 'b', 'target': 'x', 'value': 1},
                                   {'id': 'A', 'target': 'y', 'value': 2}])
        self.assertEqual([row['id'] for row in resolve.call_args.args[0]], ['a', 'b'])
        self.assertEqual(resolve.call_args.args[0][0]['target'], 'y')

    def test_normalization_and_rendering(self) -> None:
        rows = [
            {'id': ' STRAẞE / A  B ', 'target': ' Ω / Z  Z ', 'value': 23},
            {'id': 'second', 'target': ' A ', 'value': 0},
        ]
        expected = {'rooms': {'a': [[0, 1, 'second']],
                              'ω / z  z': [[23, 24, 'strasse / a  b']]}}
        self.assertEqual(policy.normalize(' STRAẞE / A  B '), 'strasse / a  b')
        for api in (project.run, engine.compute):
            self.assertEqual(api(rows), expected)
        self.assertEqual(list(project.run(rows)['rooms']), ['a', 'ω / z  z'])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), serialized)
        self.assertEqual(project.run_many([rows]), [expected])
        self.assertEqual(project.render_many([rows]), serialized)

    def test_hours_and_overlap_precedence(self) -> None:
        clash = [{'id': key, 'target': 'Room', 'value': 3} for key in ('a', 'b')]
        for api in (project.run, project.render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^calendar-windows: overlap$'):
                api(clash)
            for hour in (-1, 24, 10**100):
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid hour$'):
                    api(clash + [{'id': 'c', 'target': 'other', 'value': hour}])

    def test_row_types_and_exact_schema(self) -> None:
        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        class DictSubclass(dict):
            pass

        class ListSubclass(list):
            pass

        valid = {'id': 'a', 'target': 'room', 'value': 0}
        accepted = ListSubclass([DictSubclass(id=StringSubclass(' A '),
                                             target=StringSubclass(' ROOM '), value=0)])
        self.assertEqual(project.run(accepted), {'rooms': {'room': [[0, 1, 'a']]}})
        bad_rows = [None, [], {}, {**valid, 'extra': 1},
                    {key: value for key, value in valid.items() if key != 'id'}]
        for field, values in [('id', ['', ' \t', 1, None]),
                              ('target', ['', '\n', 1, None]),
                              ('value', [True, False, IntSubclass(1), 1.0, '1', None])]:
            bad_rows.extend({**valid, field: value} for value in values)
        for row in bad_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid row$'):
                    validation.validate([row])
        for rows in (None, (), {}, 'rows', iter([])):
            for api in (project.run, project.render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: rows must be a list$'):
                    api(rows)

    def test_empty_and_outer_types(self) -> None:
        self.assertEqual(project.run([]), {'rooms': {}})
        self.assertEqual(project.render([]), '{"rooms":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        for api in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: batches must be a list$'):
                    api(batches)

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' ROOM ', 'value': 1}]
        original = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        subsequent = project.run(rows)
        outputs[0]['rooms']['room'][0][0] = 9
        outputs[0]['rooms']['room'].append([5, 6, 'extra'])
        self.assertEqual(outputs[1], subsequent)
        self.assertEqual(rows, original)
        project.render_many([rows, rows])
        self.assertEqual(rows, original)
        bad = rows + [{'id': 'bad', 'target': 'room', 'value': {'nested': []}}]
        snapshot = copy.deepcopy(bad)
        for api in (project.run, project.render):
            with self.assertRaises(ValueError):
                api(bad)
            self.assertEqual(bad, snapshot)

    def test_shared_compute_once_per_member_and_atomic_failure(self) -> None:
        good = [{'id': 'a', 'target': 'r', 'value': 1}]
        invalid_hour = [{'id': 'b', 'target': 'r', 'value': 24}]
        invalid_row = [{'id': 'c'}]
        for api in (project.run, project.render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(good)
                self.assertEqual(compute.call_count, 1)
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api([good, good, []])
                self.assertEqual(compute.call_count, 3)
            batches = [good, invalid_hour, invalid_row]
            snapshot = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid hour$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], invalid_hour)
            self.assertEqual(batches, snapshot)


if __name__ == '__main__':
    unittest.main()
