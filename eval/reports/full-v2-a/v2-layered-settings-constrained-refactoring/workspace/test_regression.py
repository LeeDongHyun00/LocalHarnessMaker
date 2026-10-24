import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Theme ', 'value': -3},
            {'id': 'z', 'target': 'theme', 'value': -3},
            {'id': 'B', 'target': 'THEME', 'value': -2},
            {'id': 'a', 'target': 'theme', 'value': -2},
            {'id': 'Huge', 'target': ' A / Straße ', 'value': 10**100},
        ]
        expected = {'settings': {'a / strasse': 'huge', 'theme': 'a'}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['settings']), ['a / strasse', 'theme'])
        self.assertEqual(run_many([rows, []]), [expected, {'settings': {}}])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render_many([rows, []]), encoded + '{"settings":{}}\n')

    def test_validation_precedes_duplicate_selection(self) -> None:
        rows = [{'id': 'A', 'target': 'x', 'value': 1},
                {'id': 'a', 'target': 'y', 'value': 2}]
        self.assertEqual(len(validation.validate(rows)), 2)
        for call in (run, render, engine.compute):
            with self.subTest(call=call):
                with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                    call(rows)
                with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                    call(rows + [{'id': 'bad', 'target': 'x', 'value': True}])

    def test_structure_and_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        good = Rows([Row(id=Text(' A '), target=Text(' X '), value=-10**100)])
        self.assertEqual(run(good), {'settings': {'x': 'a'}})
        self.assertEqual(policy.normalize(Text(' É / Straße  X ')), 'é / strasse  x')
        bad_rows = [None, [], {}, {'id': '', 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': '  ', 'value': 1},
                    {'id': 1, 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': None, 'value': 1},
                    {'id': 'a', 'target': 'x', 'value': True},
                    {'id': 'a', 'target': 'x', 'value': Integer(1)},
                    {'id': 'a', 'target': 'x', 'value': 1.0},
                    {'id': 'a', 'target': 'x', 'value': 1, 'extra': {}}]
        for row in bad_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                    run([row])
        for rows in (None, (), {}, 'rows'):
            for call in (run, render, validation.validate, engine.compute):
                with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                    call(rows)

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        results = run_many([rows, rows])
        results[0]['settings']['x'] = 'changed'
        self.assertEqual(results[1], {'settings': {'x': 'a'}})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        malformed = rows + [{'id': 'b', 'target': 'x', 'value': 2, 'extra': {'nested': []}}]
        snapshot = copy.deepcopy(malformed)
        for call in (run, render, run_many, render_many):
            with self.assertRaises(ValueError):
                call([rows, malformed] if call in (run_many, render_many) else malformed)
            self.assertEqual(malformed, snapshot)
            self.assertEqual(rows, before)

    def test_render_and_empty_inputs(self) -> None:
        rows = [{'id': ' É ', 'target': ' Ω / X ', 'value': 0}]
        self.assertEqual(render(rows), '{"settings":{"ω / x":"é"}}\n')
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(run([]), {'settings': {}})
        self.assertEqual(render([]), '{"settings":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for call in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^layered-settings: batches must be a list$'):
                    call(batches)

    def test_compute_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        original = engine.compute
        for call, argument, expected_calls in (
            (run, rows, [rows]), (render, rows, [rows]),
            (run_many, [rows, []], [rows, []]),
            (render_many, [rows, []], [rows, []]),
        ):
            with self.subTest(call=call):
                with patch.object(engine, 'compute', wraps=original) as compute:
                    call(argument)
                    self.assertEqual(compute.call_count, len(expected_calls))
                    self.assertEqual([c.args[0] for c in compute.call_args_list], expected_calls)

    def test_batches_stop_at_first_failure(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        duplicate = good + [{'id': 'a', 'target': 'y', 'value': 1}]
        batches = [good, duplicate, [None]]
        before = copy.deepcopy(batches)
        for call in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                    call(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
