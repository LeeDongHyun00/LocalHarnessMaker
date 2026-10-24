import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Straße / X ', 'value': -4},
            {'id': 'a', 'target': 'STRASSE / x', 'value': -4},
            {'id': 'Z', 'target': 'strasse / X', 'value': -4},
            {'id': 'b', 'target': 'strasse / x', 'value': -5},
            {'id': 'solo', 'target': ' A  / 한 ', 'value': -(10**100)},
        ]
        expected = {
            'dispatch': {'a  / 한': 'solo', 'strasse / x': 'z'},
            'shadowed': ['a', 'b'],
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dispatch': {}, 'shadowed': []}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"dispatch":{},"shadowed":[]}\n')
        self.assertEqual(list(run(rows)), ['dispatch', 'shadowed'])
        self.assertEqual(list(run(rows)['dispatch']), ['a  / 한', 'strasse / x'])

    def test_validation_is_canonical_and_does_not_select(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' Straße / 한 '), value=1),
                     {'id': 'a', 'target': 'other', 'value': 2}])
        expected = [{'id': 'a', 'target': 'strasse / 한', 'value': 1},
                    {'id': 'a', 'target': 'other', 'value': 2}]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Straße / 한  X '), 'strasse / 한  x')
        with self.assertRaisesRegex(ValueError, '^command-dispatch: duplicate id$'):
            run(rows)

    def test_structural_errors_precede_duplicates(self) -> None:
        class Integer(int):
            pass

        bad_rows = [None, {}, {'id': ' ', 'target': 'x', 'value': 0},
                    {'id': 'x', 'target': '', 'value': 0},
                    {'id': 1, 'target': 'x', 'value': 0},
                    {'id': 'x', 'target': None, 'value': 0},
                    {'id': 'x', 'target': 'x', 'value': True},
                    {'id': 'x', 'target': 'x', 'value': Integer(1)},
                    {'id': 'x', 'target': 'x', 'value': 1, 'extra': []}]
        duplicate = [{'id': 'A', 'target': 'x', 'value': 1},
                     {'id': ' a ', 'target': 'y', 'value': 2}]
        for bad in bad_rows:
            rows = duplicate + [bad]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate,
                        lambda rows: run_many([rows]),
                        lambda rows: render_many([rows])):
                with self.subTest(bad=bad, api=api):
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_list_contracts_and_empty_inputs(self) -> None:
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                    api(rows)
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^command-dispatch: batches must be a list$'):
                    api(batches)
        self.assertEqual(run([]), {'dispatch': {}, 'shadowed': []})
        self.assertEqual(render([]), '{"dispatch":{},"shadowed":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1},
                {'id': 'b', 'target': 'x', 'value': 2}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['dispatch']['x'] = 'changed'
        outputs[0]['shadowed'].append('changed')
        expected = {'dispatch': {'x': 'b'}, 'shadowed': ['a']}
        self.assertEqual(outputs[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)

    def test_compute_is_resolved_at_runtime_once_per_member(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 1}]
        second = [{'id': 'b', 'target': 'y', 'value': 2}]
        original = engine.compute
        for api, argument, members in (
            (run, first, [first]), (render, first, [first]),
            (run_many, [first, second], [first, second]),
            (render_many, [first, second], [first, second]),
        ):
            with patch.object(engine, 'compute', wraps=original) as observed:
                api(argument)
                self.assertEqual(observed.call_count, len(members))
                for call, member in zip(observed.call_args_list, members):
                    self.assertIs(call.args[0], member)

    def test_batches_stop_at_first_failure(self) -> None:
        valid = [{'id': 'a', 'target': 'x', 'value': 1}]
        duplicate = valid + [{'id': 'a', 'target': 'y', 'value': 1}]
        batches = [valid, duplicate, [None]]
        before = copy.deepcopy(batches)
        original = engine.compute
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=original) as observed:
                with self.assertRaisesRegex(ValueError, '^command-dispatch: duplicate id$'):
                    api(batches)
                self.assertEqual(observed.call_count, 2)
                self.assertIs(observed.call_args_list[1].args[0], duplicate)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
