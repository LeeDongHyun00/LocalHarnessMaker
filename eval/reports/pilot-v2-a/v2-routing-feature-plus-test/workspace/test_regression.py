import copy
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class BatchRegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run_many([[]]), [{'rules': [], 'targets': []}])
        self.assertEqual(render_many([[]]), '{"rules":[],"targets":[]}\n')
        rows = [
            {'path': ' //A/// ', 'target': ' First ', 'priority': 0},
            {'path': 'a/', 'target': ' Equal ', 'priority': 0},
            {'path': '///', 'target': ' ROOT ', 'priority': -1},
            {'path': '/B', 'target': ' Old ', 'priority': -2},
            {'path': ' b///', 'target': ' NEW ', 'priority': 0},
            {'path': '/Long/', 'target': ' FIRST ', 'priority': 0},
        ]
        expected = {
            'rules': [
                {'path': '/long', 'target': 'first', 'priority': 0},
                {'path': '/a', 'target': 'first', 'priority': 0},
                {'path': '/b', 'target': 'new', 'priority': 0},
                {'path': '/', 'target': 'root', 'priority': -1},
            ],
            'targets': ['first', 'new', 'root'],
        }
        self.assertEqual(run_many([rows, []]), [expected, {'rules': [], 'targets': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_results_are_independent_and_inputs_unchanged(self):
        rows = [{'path': ' //Straße/ ', 'target': ' SÉRVICE ', 'priority': 1}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        expected = run(rows)
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['rules'].append({})
        results[0]['targets'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)
        self.assertEqual(list(expected), ['rules', 'targets'])
        self.assertEqual(list(expected['rules'][0]), ['path', 'target', 'priority'])
        self.assertEqual(normalize(' //Straße/// '), '/strasse')

    def test_render_unicode_and_escaping(self):
        rows = [{'path': '/É', 'target': ' "É\\\nX" ', 'priority': 2}]
        expected = '{"rules":[{"path":"/é","priority":2,"target":"\\"é\\\\\\nx\\""}],"targets":["\\"é\\\\\\nx\\""]}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, rows]), expected + expected)

    def test_invalid_outer_batches(self):
        for api in (run_many, render_many):
            for value in (None, (), {}, 'rows', iter([])):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                        api(value)

    def test_invalid_members_and_failure_does_not_mutate(self):
        class IntSubclass(int):
            pass

        row = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid_rows = [
            None, {}, {**row, 'extra': 0},
            {'path': '/a', 'target': 'svc'},
            {**row, 'path': '  '}, {**row, 'path': 1},
            {**row, 'target': ''}, {**row, 'target': None},
            {**row, 'priority': True}, {**row, 'priority': 1.0},
            {**row, 'priority': IntSubclass(1)},
        ]
        # A later malformed row must still be rejected after a canonical tie.
        prefix = [row, {**row, 'path': '//A/', 'target': 'other'}]
        for invalid in invalid_rows:
            rows = prefix + [invalid]
            original = copy.deepcopy(rows)
            for api in (run, render, compute, validate):
                with self.subTest(api=api.__name__, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        api(rows)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    api([[row], rows])
            self.assertEqual(rows, original)
        for value in (None, (), {}, 'rows'):
            for api in (run, render, compute, validate):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api([[row], value])

    def test_list_and_dict_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path='a', target='Svc', priority=0)])
        self.assertEqual(run_many(Rows([rows])), [run(rows)])
        self.assertEqual(render_many(Rows([rows])), render(rows))


if __name__ == '__main__':
    unittest.main()
