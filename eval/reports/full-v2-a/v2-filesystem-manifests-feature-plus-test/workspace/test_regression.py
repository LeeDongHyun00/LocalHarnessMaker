import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def assert_error(self, exception: type[Exception], message: str, call, argument) -> None:
        with self.assertRaises(exception) as caught:
            call(argument)
        self.assertEqual(str(caught.exception), 'filesystem-manifests: ' + message)

    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Dir/FILE ', 'target': ' OLD ', 'value': -1},
            {'id': 'dir/file', 'target': ' New ', 'value': 7},
            {'id': 'DIR/FILE', 'target': 'new', 'value': 7},
        ]
        expected = {'files': {'dir/file': {'digest': 'new', 'size': 7}}, 'bytes': 7}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'files': {}, 'bytes': 0}])
        self.assertEqual(project.render_many([rows, []]), project.render(rows) + project.render([]))

    def test_validation_precedes_selection_and_domain(self) -> None:
        ambiguous = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'a', 'target': 'y', 'value': 1},
        ]
        for prefix in (ambiguous, [{'id': '../a', 'target': 'x', 'value': -1}]):
            rows = prefix + [{'id': 'bad', 'target': 'x', 'value': True}]
            for call in (project.run, project.render, engine.compute, validation.validate):
                self.assert_error(ValueError, 'invalid row', call, rows)

    def test_ambiguity_is_encountered_before_later_replacement(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'x', 'value': 2},
            {'id': 'a', 'target': 'y', 'value': 2},
            {'id': 'a', 'target': 'z', 'value': 3},
        ]
        self.assert_error(ValueError, 'ambiguous id', project.run, rows)
        rows[1]['value'] = 1
        self.assertEqual(project.run(rows)['files']['a'], {'digest': 'z', 'size': 3})

    def test_structural_types(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'x'},
                   {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0}]
        for field, values in (('id', [None, 1, '', ' \t']),
                              ('target', [None, 1, '', ' \n']),
                              ('value', [True, False, Integer(1), 1.0, '1', None])):
            for value in values:
                row = {'id': 'a', 'target': 'x', 'value': 1}
                row[field] = value
                invalid.append(row)
        for row in invalid:
            self.assert_error(ValueError, 'invalid row', validation.validate, [row])
        for value in (None, (), {}, 'rows', iter([])):
            self.assert_error(TypeError, 'rows must be a list', project.run, value)

    def test_subclasses_unicode_and_unbounded_sizes(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text('  Straße/ A  B\\C  '), target=Text('  Δ/Ä  '), value=10**100)])
        expected = {'files': {'strasse/ a  b\\c': {'digest': 'δ/ä', 'size': 10**100}}, 'bytes': 10**100}
        self.assertEqual(policy.normalize(Text('  Straße/ A  B\\C  ')), 'strasse/ a  b\\c')
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many(Rows([rows])), [expected])
        self.assertEqual(json.loads(project.render_many(Rows([rows]))), expected)

    def test_validation_only_canonicalizes_and_copies(self) -> None:
        rows = [{'id': ' ../A ', 'target': ' X ', 'value': -1},
                {'id': '../a', 'target': 'y', 'value': -1}]
        original = copy.deepcopy(rows)
        result = validation.validate(rows)
        self.assertEqual(result, [{'id': '../a', 'target': 'x', 'value': -1},
                                  {'id': '../a', 'target': 'y', 'value': -1}])
        self.assertEqual(rows, original)
        self.assertIsNot(result, rows)
        for source, canonical in zip(rows, result):
            self.assertIsNot(source, canonical)
            self.assertEqual(list(canonical), ['id', 'target', 'value'])

    def test_path_rules_and_error_priority(self) -> None:
        for name in ('/a', 'a/', 'a//b', '.', '..', './a', 'a/../b', 'a/./b'):
            self.assert_error(ValueError, 'invalid path', project.run,
                              [{'id': name, 'target': 'x', 'value': -1}])
        self.assert_error(ValueError, 'negative size', project.run,
                          [{'id': 'a', 'target': 'x', 'value': -1}])
        self.assert_error(ValueError, 'invalid path', project.run,
                          [{'id': 'a', 'target': 'x', 'value': -1},
                           {'id': 'b/..', 'target': 'x', 'value': 0}])
        self.assertEqual(project.run([{'id': 'a\\..\\b', 'target': 'x', 'value': 0}])['bytes'], 0)

    def test_output_order_and_serialization(self) -> None:
        rows = [{'id': name, 'target': ' Ä ', 'value': value}
                for name, value in [('z', 1), ('B', 2), ('a', 3), ('z', 4)]]
        result = project.run(rows)
        self.assertEqual(list(result), ['files', 'bytes'])
        self.assertEqual(list(result['files']), ['a', 'b', 'z'])
        self.assertEqual(list(result['files']['a']), ['digest', 'size'])
        self.assertEqual(project.render(rows),
                         '{"bytes":9,"files":{"a":{"digest":"ä","size":3},'
                         '"b":{"digest":"ä","size":2},"z":{"digest":"ä","size":4}}}\n')

    def test_empty_inputs(self) -> None:
        self.assertEqual(project.run([]), {'files': {}, 'bytes': 0})
        self.assertEqual(project.render([]), '{"bytes":0,"files":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')

    def test_output_independence_and_success_immutability(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [] , []]
        original = copy.deepcopy(batches)
        results = project.run_many(batches)
        project.render_many(batches)
        self.assertEqual(batches, original)
        later = project.run(rows)
        results[0]['files']['a']['size'] = 99
        results[2]['files']['new'] = {}
        self.assertEqual(results[1], later)
        self.assertEqual(results[3], {'files': {}, 'bytes': 0})
        self.assertEqual(project.run(rows), later)
        self.assertEqual(batches, original)

    def test_batches_outer_type(self) -> None:
        for call in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                self.assert_error(TypeError, 'batches must be a list', call, batches)

    def test_failure_is_atomic_and_stops_at_first_member(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        cases = [([{'id': '../b', 'target': 'x', 'value': -1}], ValueError, 'invalid path'),
                 ([{'id': 'b', 'target': 'x', 'value': -1}], ValueError, 'negative size'),
                 ([{}], ValueError, 'invalid row'),
                 ([{'id': 'b', 'target': 'x', 'value': 1},
                   {'id': 'b', 'target': 'y', 'value': 1}], ValueError, 'ambiguous id'),
                 (None, TypeError, 'rows must be a list')]
        for bad, exception, message in cases:
            for call in (project.run_many, project.render_many):
                batches = [good, bad, [{}]]
                original = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    self.assert_error(exception, message, call, batches)
                    self.assertEqual(compute.call_count, 2)
                    self.assertIs(compute.call_args_list[0].args[0], good)
                    self.assertIs(compute.call_args_list[1].args[0], bad)
                self.assertEqual(batches, original)

    def test_all_facades_resolve_compute_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        sentinel = {'files': {'instrumented': {'digest': 'x', 'size': 2}}, 'bytes': 2}
        encoded = json.dumps(sentinel, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        with patch.object(engine, 'compute', return_value=sentinel) as compute:
            self.assertEqual(project.run(rows), sentinel)
            self.assertEqual(project.render(rows), encoded)
            self.assertEqual(project.run_many([rows, []]), [sentinel, sentinel])
            self.assertEqual(project.render_many([rows, []]), encoded * 2)
            self.assertEqual(compute.call_count, 6)


if __name__ == '__main__':
    unittest.main()
