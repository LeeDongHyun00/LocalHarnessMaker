import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Straße/B ', 'target': ' HASH ', 'value': 7},
            {'id': 'strasse/b', 'target': 'hash', 'value': 7},
            {'id': 'a\\b', 'target': 'Other Digest', 'value': 2},
        ]
        expected = {'files': {
            'a\\b': {'digest': 'other digest', 'size': 2},
            'strasse/b': {'digest': 'hash', 'size': 7},
        }, 'bytes': 9}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['files']), ['a\\b', 'strasse/b'])
        self.assertEqual(run_many([rows, []]), [expected, {'files': {}, 'bytes': 0}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"bytes":0,"files":{}}\n')

    def test_structural_validation_precedes_selection_and_domain(self) -> None:
        bad = {'id': 'late', 'target': 'hash', 'value': True}
        for earlier in (
            [{'id': '../bad', 'target': 'hash', 'value': -1}],
            [{'id': 'same', 'target': 'one', 'value': 0},
             {'id': 'same', 'target': 'two', 'value': 0}],
        ):
            rows = earlier + [bad]
            for api in (run, render, engine.compute):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid row$'):
                        api(rows)

    def test_validation_only_canonicalizes(self) -> None:
        rows = [{'id': ' ../A ', 'target': ' X Y ', 'value': -1},
                {'id': '../a', 'target': 'different', 'value': 2}]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': '../a', 'target': 'x y', 'value': -1}, rows[1]])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical[1], rows[1])
        self.assertEqual(rows, before)
        self.assertEqual(policy.normalize(' É / X  Y '), 'é / x  y')

    def test_row_types(self) -> None:
        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        rows = ListSubclass([DictSubclass(id=StringSubclass(' A '),
                                         target=StringSubclass(' H '), value=10**100)])
        self.assertEqual(run(rows)['bytes'], 10**100)
        for value in (None, (), {}, 'rows'):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^filesystem-manifests: rows must be a list$'):
                    api(value)
        invalid = [None, {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': {}},
                   {'id': ' ', 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': '\t', 'value': 1},
                   {'id': 1, 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': None, 'value': 1}]
        invalid.extend({'id': 'a', 'target': 'b', 'value': value}
                       for value in (True, IntSubclass(1), 1.0, '1'))
        for row in invalid:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid row$'):
                    run([row])

    def test_domain_errors_and_precedence(self) -> None:
        for name in ('/a', 'a/', 'a//b', '.', '..', 'a/./b', 'a/../b'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid path$'):
                    run([{'id': 'valid', 'target': 'h', 'value': -1},
                         {'id': name, 'target': 'h', 'value': 0}])
        with self.assertRaisesRegex(ValueError, '^filesystem-manifests: negative size$'):
            run([{'id': 'valid', 'target': 'h', 'value': -1}])
        for changed in ({'id': '../a', 'target': 'other', 'value': -1},
                        {'id': '../a', 'target': 'h', 'value': 0}):
            with self.assertRaisesRegex(ValueError, '^filesystem-manifests: duplicate id$'):
                run([{'id': '../a', 'target': 'h', 'value': -1}, changed])

    def test_output_independence_and_input_preservation(self) -> None:
        rows = [{'id': 'a', 'target': 'h', 'value': 3}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['files']['a']['size'] = 99
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, original)
        empty = run_many([[], []])
        empty[0]['files']['new'] = {}
        self.assertEqual(empty[1], {'files': {}, 'bytes': 0})
        invalid = [rows[0], {'id': 'bad', 'target': 'h', 'value': 1, 'extra': {'x': []}}]
        before = copy.deepcopy(invalid)
        for api in (run, render):
            with self.assertRaises(ValueError):
                api(invalid)
            self.assertEqual(invalid, before)

    def test_batch_atomicity_and_call_time_dispatch(self) -> None:
        first = [{'id': 'a', 'target': 'h', 'value': 1}]
        failing = [{'id': '/bad', 'target': 'h', 'value': 1}]
        batches = [first, failing, None]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^filesystem-manifests: invalid path$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], first)
                self.assertIs(compute.call_args_list[1].args[0], failing)
            self.assertEqual(batches, before)
        for api, argument, count in ((run, first, 1), (render, first, 1),
                                     (run_many, [first, first], 2),
                                     (render_many, [first, first], 2)):
            with patch.object(engine, 'compute', return_value={'instrumented': 'é'}) as compute:
                result = api(argument)
                self.assertEqual(compute.call_count, count)
                if api is run:
                    self.assertEqual(result, {'instrumented': 'é'})
                elif api is render:
                    self.assertEqual(result, '{"instrumented":"é"}\n')
                elif api is run_many:
                    self.assertEqual(result, [{'instrumented': 'é'}] * 2)
                else:
                    self.assertEqual(result, '{"instrumented":"é"}\n' * 2)

    def test_empty_and_outer_types(self) -> None:
        self.assertEqual(run([]), {'files': {}, 'bytes': 0})
        self.assertEqual(render([]), '{"bytes":0,"files":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for value in (None, (), {}, ''):
                with self.assertRaisesRegex(TypeError, '^filesystem-manifests: batches must be a list$'):
                    api(value)


if __name__ == '__main__':
    unittest.main()
