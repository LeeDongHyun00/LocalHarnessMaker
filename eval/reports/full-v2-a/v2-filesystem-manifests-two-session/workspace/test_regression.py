import copy
import json
import unittest
from unittest.mock import call, patch

from project import engine, render, render_many, run, run_many
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def assert_error(self, rows, message, error=ValueError):
        before = copy.deepcopy(rows)
        for api in (run, render, engine.compute):
            with self.subTest(api=api.__name__, message=message):
                with self.assertRaises(error) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'filesystem-manifests: ' + message)
                self.assertEqual(rows, before)
        for api in (run_many, render_many):
            batches = [[], rows, []]
            with self.subTest(api=api.__name__, message=message):
                with self.assertRaises(error) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception), 'filesystem-manifests: ' + message)
                self.assertEqual(batches, [[], before, []])

    def test_domain_edge(self):
        rows = [
            {'id': ' DIR/File_A ', 'target': ' SHA_Ä ', 'value': 7},
            {'id': 'dir/file-a', 'target': 'sha-ä', 'value': 7},
            {'id': 'a', 'target': 'Other', 'value': 3},
        ]
        self.assertEqual(run(rows), {
            'files': {'a': {'digest': 'other', 'size': 3},
                      'dir/file-a': {'digest': 'sha-ä', 'size': 7}},
            'bytes': 10,
        })
        self.assertEqual(list(run(rows)['files']), ['a', 'dir/file-a'])

    def test_structure_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        for rows in (None, (), {}, 'rows', iter([])):
            # Iterators are not deepcopyable; these inputs cannot be mutated here.
            for api in (run, render, engine.compute, validate):
                with self.assertRaises(TypeError) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'filesystem-manifests: rows must be a list')
        for row in (None, [], {}, {'id': 'a', 'target': 'b'},
                    {'id': 'a', 'target': 'b', 'value': 1, 'extra': []},
                    {'id': ' ', 'target': 'b', 'value': 1},
                    {'id': 'a', 'target': '\t', 'value': 1},
                    {'id': 1, 'target': 'b', 'value': 1},
                    {'id': 'a', 'target': None, 'value': 1}):
            self.assert_error([row], 'invalid row')
        for value in (True, False, Integer(1), 1.0, '1', None):
            self.assert_error([{'id': 'a', 'target': 'b', 'value': value}], 'invalid row')
        rows = Rows([Row(id=Text(' A_B '), target=Text(' STRASSE_ẞ '), value=10**100)])
        self.assertEqual(run(rows)['files']['a-b'], {'digest': 'strasse-ss', 'size': 10**100})

    def test_validation_is_fresh_ordered_and_domain_free(self):
        rows = [{'id': ' Z ', 'target': ' A_B ', 'value': -1},
                {'id': 'z', 'target': 'other', 'value': 2},
                {'id': '../x', 'target': 'x', 'value': 0}]
        before = copy.deepcopy(rows)
        canonical = validate(rows)
        self.assertEqual(canonical, [
            {'id': 'z', 'target': 'a-b', 'value': -1},
            {'id': 'z', 'target': 'other', 'value': 2},
            {'id': '../x', 'target': 'x', 'value': 0}])
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, before)
        self.assertIsNot(canonical[1], validate(rows)[1])
        self.assertEqual(normalize(' A_B/ Straße \\ Ω '), 'a-b/ strasse \\ ω')

    def test_error_precedence(self):
        duplicate = [{'id': 'A', 'target': 'x', 'value': -1},
                     {'id': 'a', 'target': 'y', 'value': 2}]
        self.assert_error(duplicate + [{}], 'invalid row')
        self.assert_error([{'id': '../bad', 'target': 'x', 'value': -1}, {}], 'invalid row')
        self.assert_error(duplicate, 'duplicate id')
        self.assert_error([{'id': 'a', 'target': 'x', 'value': -1},
                           {'id': '../bad', 'target': 'x', 'value': 0}], 'invalid path')

    def test_paths_and_sizes(self):
        for name in ('/a', 'a/', 'a//b', '.', '..', 'a/./b', 'a/../b'):
            self.assert_error([{'id': name, 'target': 'x', 'value': 1}], 'invalid path')
        self.assert_error([{'id': 'valid', 'target': 'x', 'value': -10**100}], 'negative size')
        for name in ('a\\b', 'a b', 'é/文件', '...'):
            self.assertIn(name, run([{'id': name, 'target': '/ LABEL_Ω /', 'value': 0}])['files'])

    def test_empty_and_output_independence(self):
        self.assertEqual(run([]), {'files': {}, 'bytes': 0})
        self.assertEqual(render([]), '{"bytes":0,"files":{}}\n')
        rows = [{'id': ' B ', 'target': ' Ω ', 'value': 2}]
        before = copy.deepcopy(rows)
        first, second = run(rows), run(rows)
        self.assertEqual(list(first), ['files', 'bytes'])
        self.assertEqual(list(first['files']['b']), ['digest', 'size'])
        first['files']['b']['size'] = 99
        self.assertEqual(second['files']['b']['size'], 2)
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), second)

    def test_render_and_runtime_compute(self):
        rows = [{'id': 'Ω_A', 'target': 'É', 'value': 3}]
        self.assertEqual(render(rows), '{"bytes":3,"files":{"ω-a":{"digest":"é","size":3}}}\n')
        self.assertEqual(json.loads(render(rows)), run(rows))
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('sentinel')) as compute:
                with self.assertRaisesRegex(ValueError, '^sentinel$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_outer_inputs_and_empty(self):
        class Batches(list):
            pass

        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.subTest(api=api.__name__, batches=type(batches)):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaises(TypeError) as caught:
                            api(batches)
                        self.assertEqual(str(caught.exception),
                                         'filesystem-manifests: batches must be a list')
                        compute.assert_not_called()
            with patch.object(engine, 'compute') as compute:
                self.assertEqual(api(Batches()), [] if api is run_many else '')
                compute.assert_not_called()
        self.assertEqual(run_many(Batches([[]])), [{'files': {}, 'bytes': 0}])
        self.assertEqual(render_many(Batches([[]])), '{"bytes":0,"files":{}}\n')

    def test_batch_results_and_render_order(self):
        batches = [[{'id': ' Z/File_A ', 'target': ' SHA_ẞ ', 'value': 7},
                    {'id': 'z/file-a', 'target': 'sha-ss', 'value': 7},
                    {'id': 'a b', 'target': 'É', 'value': 2}],
                   [], [{'id': 'a\\b', 'target': 'Ω', 'value': 0}]]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows) for rows in batches])
        self.assertEqual(list(results[0]), ['files', 'bytes'])
        self.assertEqual(list(results[0]['files']), ['a b', 'z/file-a'])
        self.assertEqual(list(results[0]['files']['z/file-a']), ['digest', 'size'])
        rendered = render_many(batches)
        self.assertEqual(rendered, ''.join(render(rows) for rows in batches))
        self.assertTrue(rendered.endswith('\n'))
        self.assertEqual([json.loads(line) for line in rendered.splitlines()], results)
        self.assertEqual(batches, before)

    def test_batch_nested_independence(self):
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first, second = run_many(batches), run_many(batches)
        first[0]['files']['a']['digest'] = 'changed'
        first[0]['files']['extra'] = {'digest': 'x', 'size': 2}
        first[2]['files']['new'] = {'digest': 'x', 'size': 0}
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], {'files': {}, 'bytes': 0})
        self.assertEqual(second, run_many(batches))
        self.assertEqual(batches, before)
        self.assertIs(batches[0], batches[1])

    def test_batch_runtime_compute_once_in_encounter_order(self):
        batches = [[{'id': 'z', 'target': 'x', 'value': 2}],
                   [], [{'id': 'a', 'target': 'y', 'value': 1}]]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_args_list, [call(rows) for rows in batches])
                for invocation, rows in zip(compute.call_args_list, batches):
                    self.assertIs(invocation.args[0], rows)

    def test_batch_first_failure_is_atomic(self):
        cases = [
            (None, TypeError, 'rows must be a list'),
            ([{}], ValueError, 'invalid row'),
            ([{'id': 'a', 'target': 'x', 'value': 1},
              {'id': 'A', 'target': 'y', 'value': 1}], ValueError, 'duplicate id'),
            ([{'id': '../a', 'target': 'x', 'value': 0}], ValueError, 'invalid path'),
            ([{'id': 'a', 'target': 'x', 'value': -1}], ValueError, 'negative size'),
        ]
        for api in (run_many, render_many):
            for bad, error, message in cases:
                batches = [[{'id': 'ok', 'target': 'x', 'value': 1}], bad, [{}]]
                before = copy.deepcopy(batches)
                with self.subTest(api=api.__name__, message=message):
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaises(error) as caught:
                            api(batches)
                        self.assertEqual(str(caught.exception), 'filesystem-manifests: ' + message)
                        self.assertEqual(compute.call_args_list,
                                         [call(batches[0]), call(batches[1])])
                    self.assertEqual(batches, before)
            batches = [[], [], []]
            before = copy.deepcopy(batches)
            sentinel = ValueError('sentinel')
            with patch.object(engine, 'compute', side_effect=[{'files': {}, 'bytes': 0},
                                                            sentinel]) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertIs(caught.exception, sentinel)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
