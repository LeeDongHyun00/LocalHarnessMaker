import copy
import json
import unittest
from unittest.mock import patch

from project import engine, render, render_many, run, run_many
from project.domain import resolve
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'Old', 'value': 100},
            {'id': 'b', 'target': 'New', 'value': -5},
            {'id': 'a', 'target': ' New ', 'value': -5},
            {'id': 'c', 'target': 'Old', 'value': -100},
        ]
        expected = {'dispatch': {'new': 'b', 'old': 'c'}, 'shadowed': ['a']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dispatch': {}, 'shadowed': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_validation_is_structural_and_preserves_encounter_order(self) -> None:
        rows = [
            {'id': ' Z ', 'target': 'Straße / X', 'value': 10**100},
            {'id': 'z', 'target': ' Different ', 'value': -(10**100)},
            {'id': ' A ', 'target': ' Internal  Spaces ', 'value': 0},
        ]
        canonical = validate(rows)
        self.assertEqual(canonical, [
            {'id': 'z', 'target': 'strasse / x', 'value': 10**100},
            {'id': 'z', 'target': 'different', 'value': -(10**100)},
            {'id': 'a', 'target': 'internal  spaces', 'value': 0},
        ])
        self.assertEqual(normalize('  Straße / X  '), 'strasse / x')
        for original, result in zip(rows, canonical):
            self.assertIsNot(original, result)
        # Selection retains the original position even when both fields change.
        with patch.object(engine, 'resolve', wraps=resolve) as resolver:
            engine.compute(rows)
        self.assertEqual(resolver.call_args.args[0], canonical[1:])

    def test_row_types_and_errors(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        self.assertEqual(run(ListSubclass([
            DictSubclass(id=StringSubclass(' X '), target=StringSubclass(' Y '), value=1)
        ])), {'dispatch': {'y': 'x'}, 'shadowed': []})
        for api in (validate, engine.compute, run, render):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                        api(rows)
        invalid_rows = [
            None, [], {}, {'id': 'x', 'target': 'y'},
            {'id': 'x', 'target': 'y', 'value': 1, 'extra': None},
            {'id': ' ', 'target': 'y', 'value': 1},
            {'id': 'x', 'target': '\t', 'value': 1},
            {'id': 1, 'target': 'y', 'value': 1},
            {'id': 'x', 'target': None, 'value': 1},
        ] + [{'id': 'x', 'target': 'y', 'value': value}
             for value in (True, IntSubclass(1), 1.0, '1', None)]
        for api in (validate, engine.compute, run, render):
            for row in invalid_rows:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api([row])

    def test_full_validation_precedes_selection(self) -> None:
        rows = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'a', 'target': 'y', 'value': 2},
            {'id': 'bad', 'target': 'z', 'value': False},
        ]
        before = copy.deepcopy(rows)
        with patch.object(engine, 'resolve') as resolver:
            with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                run(rows)
        resolver.assert_not_called()
        self.assertEqual(rows, before)

    def test_order_unicode_and_serialization(self) -> None:
        rows = [
            {'id': 'β', 'target': ' Ω / Z ', 'value': -1},
            {'id': 'a', 'target': ' Alpha  X ', 'value': 0},
            {'id': 'z', 'target': 'Ω / Z', 'value': -1},
            {'id': 'b', 'target': 'Alpha  X', 'value': -1},
        ]
        result = run(rows)
        self.assertEqual(result, {'dispatch': {'alpha  x': 'a', 'ω / z': 'β'}, 'shadowed': ['b', 'z']})
        self.assertEqual(list(result), ['dispatch', 'shadowed'])
        self.assertEqual(list(result['dispatch']), ['alpha  x', 'ω / z'])
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')) + '\n')

    def test_empty_and_independent_results(self) -> None:
        self.assertEqual(run([]), {'dispatch': {}, 'shadowed': []})
        self.assertEqual(render([]), '{"dispatch":{},"shadowed":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [{'id': 'a', 'target': 'x', 'value': 1},
                {'id': 'b', 'target': 'x', 'value': 0}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        expected = copy.deepcopy(outputs[1])
        outputs[0]['dispatch']['x'] = 'changed'
        outputs[0]['shadowed'].append('changed')
        self.assertEqual(outputs[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        canonical = validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)

    def test_dynamic_compute_once_per_member(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        empty = []
        for api, argument, calls in (
            (run, rows, [rows]), (render, rows, [rows]),
            (run_many, [rows, empty], [rows, empty]),
            (render_many, [rows, empty], [rows, empty]),
        ):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                self.assertEqual(compute.call_count, len(calls))
                for actual, expected in zip(compute.call_args_list, calls):
                    self.assertIs(actual.args[0], expected)

    def test_batch_failure_order_and_atomicity(self) -> None:
        valid = [{'id': 'a', 'target': 'x', 'value': -1}]
        invalid = [{'id': 'a', 'target': 'x', 'value': 1, 'nested': {'items': []}}]
        batches = [valid, invalid, None]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertEqual(batches, before)
                with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                    api([None, invalid])
                for outer in (None, (), {}, 'batches'):
                    with self.assertRaisesRegex(TypeError, '^command-dispatch: batches must be a list$'):
                        api(outer)


if __name__ == '__main__':
    unittest.main()
