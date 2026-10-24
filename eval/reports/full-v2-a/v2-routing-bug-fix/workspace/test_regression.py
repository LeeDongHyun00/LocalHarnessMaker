import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'path': ' //Straße///A/ ', 'target': ' First ', 'priority': 0},
            {'path': '/STRASSE/a', 'target': 'Second', 'priority': 0},
            {'path': '////', 'target': ' ROOT ', 'priority': -1},
        ]
        self.assertEqual(run(rows), {
            'rules': [
                {'path': '/strasse/a', 'target': 'first', 'priority': 0},
                {'path': '/', 'target': 'root', 'priority': -1},
            ],
            'targets': ['first', 'root'],
        })
        self.assertEqual(normalize(' //Straße///A/ '), '/strasse/a')
        self.assertEqual(normalize('////'), '/')

    def test_selection_and_order(self):
        rows = [
            {'path': 'B', 'target': 'discarded', 'priority': -1},
            {'path': '/b/', 'target': 'Z', 'priority': 2},
            {'path': 'a', 'target': 'Z', 'priority': 2},
            {'path': 'long', 'target': 'A', 'priority': 2},
            {'path': 'x', 'target': 'B', 'priority': 3},
        ]
        result = run(rows)
        self.assertEqual([row['path'] for row in result['rules']], ['/x', '/long', '/a', '/b'])
        self.assertEqual(result['targets'], ['a', 'b', 'z'])
        self.assertEqual(list(result), ['rules', 'targets'])
        self.assertEqual(compute(rows), result)

    def test_invalid_fields_and_shapes(self):
        class IntSubclass(int):
            pass

        invalid_rows = [
            None, [], {},
            {'path': '/a', 'target': 'svc'},
            {'path': '/a', 'target': 'svc', 'priority': 1, 'extra': 2},
        ]
        for field, values in (
            ('path', [None, 1, '', '  ']),
            ('target', [None, [], '', '\t']),
            ('priority', [True, False, IntSubclass(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'path': '/a', 'target': 'svc', 'priority': 1}
                row[field] = value
                invalid_rows.append(row)
        for row in invalid_rows:
            before = copy.deepcopy(row)
            for function in (run, compute, validate, render):
                with self.subTest(row=row, function=function.__name__):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        function([row])
            self.assertEqual(row, before)
        for value in (None, (), {}, '', iter([])):
            for function in (run, compute, validate, render):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    function(value)

    def test_validate_all_fields_before_normalization(self):
        rows = [
            {'path': 'A', 'target': 'one', 'priority': 1},
            {'path': '/a', 'target': 'two', 'priority': 1},
            {'path': '/bad', 'target': 'three', 'priority': True},
        ]
        with patch('project.policy.normalize', side_effect=AssertionError('too early')):
            for function in (run, render, validate):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    function(rows)

    def test_allowed_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' A/ ', target=' SVC ', priority=0)])
        before = copy.deepcopy(rows)
        result = run(rows)
        normalized = validate(rows)
        self.assertIsNot(result['rules'][0], rows[0])
        self.assertIsNot(normalized[0], rows[0])
        result['rules'][0]['path'] = '/changed'
        result['targets'].append('changed')
        normalized[0]['target'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), {'rules': [{'path': '/a', 'target': 'svc', 'priority': 0}], 'targets': ['svc']})

    def test_unicode_rendering(self):
        rows = [{'path': ' /Ä/ ', 'target': '한글 "\\\n', 'priority': -2}]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertTrue(render(rows).endswith('\n'))
        self.assertFalse(render(rows).endswith('\n\n'))
        self.assertEqual(json.loads(render(rows)), run(rows))

    def test_batches_and_empty_inputs(self):
        rows = [{'path': ' A ', 'target': ' SVC ', 'priority': 0}]
        batches = [rows, [], rows]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows), run([]), run(rows)])
        self.assertEqual(render_many(batches), render(rows) + render([]) + render(rows))
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['targets'].clear()
        self.assertEqual(results[2], run(rows))
        self.assertEqual(batches, before)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        self.assertIsNot(run([])['rules'], run([])['rules'])
        self.assertIsNot(run([])['targets'], run([])['targets'])

    def test_batch_failure_is_atomic(self):
        rows = [{'path': ' A ', 'target': ' SVC ', 'priority': 0}]
        for bad, error, message in (
            (None, TypeError, 'routing: rows must be a list'),
            ([{'path': '/bad', 'target': '', 'priority': 1}], ValueError, 'routing: invalid row'),
        ):
            batches = [rows, bad, rows]
            before = copy.deepcopy(batches)
            for function in (run_many, render_many):
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    function(batches)
                self.assertEqual(batches, before)
            self.assertEqual(run_many([rows]), [run(rows)])
        for value in (None, (), {}, ''):
            for function in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    function(value)


if __name__ == '__main__':
    unittest.main()
