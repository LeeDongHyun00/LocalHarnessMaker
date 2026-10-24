import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Late ', 'target': ' Room/北 ', 'value': 23},
            {'id': 'Early', 'target': 'room/北', 'value': 22},
            {'id': 'LATE', 'target': 'ROOM/北', 'value': 23},
        ]
        expected = {'rooms': {'room/北': [[22, 23, 'early'], [23, 24, 'late']]}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'rooms': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        with self.assertRaisesRegex(ValueError, '^calendar-windows: duplicate id$'):
            run(rows + [{'id': 'late', 'target': 'elsewhere', 'value': 23}])
        with self.assertRaisesRegex(ValueError, '^calendar-windows: overlap$'):
            run(rows + [{'id': 'another', 'target': 'room/北', 'value': 23}])

    def test_structural_validation_precedes_selection_and_domain(self) -> None:
        for prefix in (
            [{'id': 'a', 'target': 'r', 'value': 24}],
            [{'id': 'a', 'target': 'r', 'value': 1},
             {'id': 'a', 'target': 'r', 'value': 2}],
        ):
            rows = prefix + [{'id': 'bad', 'target': 'r', 'value': True}]
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(api=api, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid row$'):
                        api(rows)
        rows = [{'id': ' A ', 'target': ' R ', 'value': 10**100},
                {'id': 'a', 'target': 'r', 'value': -1}]
        self.assertEqual(validation.validate(rows), [
            {'id': 'a', 'target': 'r', 'value': 10**100},
            {'id': 'a', 'target': 'r', 'value': -1}])
        with self.assertRaisesRegex(ValueError, '^calendar-windows: duplicate id$'):
            run(rows)

    def test_invalid_hour_precedes_overlap(self) -> None:
        rows = [{'id': 'a', 'target': 'r', 'value': 1},
                {'id': 'b', 'target': 'r', 'value': 1}]
        for hour in (-1, 24, 10**100):
            with self.subTest(hour=hour):
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid hour$'):
                    run(rows + [{'id': 'c', 'target': 'r', 'value': hour}])

    def test_input_types_and_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        self.assertEqual(run(Rows([Row(id=Text(' A '), target=Text(' R '), value=0)])),
                         {'rooms': {'r': [[0, 1, 'a']]}})
        for rows in (None, (), {}, 'rows'):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: rows must be a list$'):
                    api(rows)
        for row in (None, [], {}, {'id': 'a', 'target': 'r', 'value': 0, 'extra': 1},
                    {'id': ' ', 'target': 'r', 'value': 0},
                    {'id': 'a', 'target': '\t', 'value': 0},
                    {'id': 1, 'target': 'r', 'value': 0},
                    {'id': 'a', 'target': None, 'value': 0},
                    {'id': 'a', 'target': 'r', 'value': Integer(1)},
                    {'id': 'a', 'target': 'r', 'value': True}):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid row$'):
                    run([row])

    def test_normalization_order_and_serialization(self) -> None:
        rows = [{'id': ' Straße/北 ', 'target': ' Z  /北 ', 'value': 2},
                {'id': 'B', 'target': ' A ', 'value': 5},
                {'id': 'C', 'target': 'a', 'value': 1}]
        self.assertEqual(policy.normalize(' Straße/北 '), 'strasse/北')
        expected = {'rooms': {'a': [[1, 2, 'c'], [5, 6, 'b']],
                              'z  /北': [[2, 3, 'strasse/北']]}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['rooms']), ['a', 'z  /北'])
        self.assertEqual(list(validation.validate(rows)[0]), ['id', 'target', 'value'])
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                                 separators=(',', ':')) + '\n')

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' R ', 'value': 1}]
        original = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['rooms']['r'][0][0] = 99
        self.assertEqual(outputs[1], {'rooms': {'r': [[1, 2, 'a']]}})
        self.assertEqual(run(rows), outputs[1])
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, original)
        for api in (run_many, render_many):
            batches = [rows, rows + [{'id': 'b', 'target': 'r', 'value': 1}]]
            before = copy.deepcopy(batches)
            with self.assertRaisesRegex(ValueError, '^calendar-windows: overlap$'):
                api(batches)
            self.assertEqual(batches, before)

    def test_batch_order_atomicity_and_dynamic_compute(self) -> None:
        rows = [{'id': 'a', 'target': 'r', 'value': 1}]
        other = [{'id': 'b', 'target': 's', 'value': 2}]
        compute = engine.compute
        for api, argument, calls in ((run, rows, [rows]), (render, rows, [rows]),
                                     (run_many, [rows, other], [rows, other]),
                                     (render_many, [rows, other], [rows, other])):
            with self.subTest(api=api):
                with patch.object(engine, 'compute', wraps=compute) as observed:
                    api(argument)
                self.assertEqual(observed.call_count, len(calls))
                self.assertEqual([call.args[0] for call in observed.call_args_list], calls)
        invalid_hour = [{'id': 'a', 'target': 'r', 'value': 24}]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=compute) as observed:
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid hour$'):
                    api([invalid_hour, [None]])
                self.assertEqual(observed.call_count, 1)
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: batches must be a list$'):
                    api(batches)

    def test_empty_results(self) -> None:
        self.assertEqual(run([]), {'rooms': {}})
        self.assertEqual(render([]), '{"rooms":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        outputs = run_many([[], []])
        outputs[0]['rooms']['new'] = []
        self.assertEqual(outputs[1], {'rooms': {}})


if __name__ == '__main__':
    unittest.main()
