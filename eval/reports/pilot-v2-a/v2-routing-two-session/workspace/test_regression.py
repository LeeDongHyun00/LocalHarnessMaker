import copy
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RoutingRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'path': ' A//B/ ', 'target': ' First ', 'priority': 0},
            {'path': '/a/b', 'target': 'Equal', 'priority': 0},
            {'path': '//A//B//', 'target': ' Winner ', 'priority': 2},
            {'path': '/a/b/', 'target': 'Later', 'priority': 2},
            {'path': '////', 'target': ' ROOT ', 'priority': -1},
            {'path': '/zz', 'target': 'Z', 'priority': 2},
            {'path': '/aa', 'target': 'Winner', 'priority': 2},
        ]
        self.assertEqual(run(rows), {
            'rules': [
                {'path': '/a/b', 'target': 'winner', 'priority': 2},
                {'path': '/aa', 'target': 'winner', 'priority': 2},
                {'path': '/zz', 'target': 'z', 'priority': 2},
                {'path': '/', 'target': 'root', 'priority': -1},
            ],
            'targets': ['root', 'winner', 'z'],
        })

    def test_invalid_inputs(self):
        class IntSubclass(int):
            pass

        valid = {'path': '/a', 'target': 'svc', 'priority': 1}
        for entrypoint in (run, render, compute, validate):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(entrypoint=entrypoint, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                        entrypoint(rows)
            invalid_rows = [None, [], {}, dict(valid, extra=1)]
            for key in valid:
                missing = dict(valid)
                del missing[key]
                invalid_rows.append(missing)
            for key in ('path', 'target'):
                for value in (None, 1, '', ' \t\n '):
                    invalid_rows.append(dict(valid, **{key: value}))
            for value in (True, False, 1.0, '1', None, IntSubclass(1)):
                invalid_rows.append(dict(valid, priority=value))
            for row in invalid_rows:
                with self.subTest(entrypoint=entrypoint, row=row):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        entrypoint([valid, row])

    def test_validation_precedes_domain_processing(self):
        rows = [
            {'path': '/A', 'target': 'one', 'priority': 1},
            {'path': '/a/', 'target': 'two', 'priority': 1},
            {'path': '/bad', 'target': '', 'priority': 1},
        ]
        for entrypoint in (run, render, compute, validate):
            with patch('project.policy.normalize', side_effect=AssertionError('too early')):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    entrypoint(rows)

    def test_subclasses_and_normalization(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' STRAẞE///A/ ', target=' Straße// ', priority=-2)])
        expected = [{'path': '/strasse/a', 'target': 'strasse//', 'priority': -2}]
        self.assertEqual(validate(rows), expected)
        self.assertEqual(compute(rows)['rules'], expected)
        self.assertEqual(normalize(' /// '), '/')

    def test_immutability_and_fresh_results(self):
        rows = [{'path': ' A/ ', 'target': ' SVC ', 'priority': 1}]
        original = copy.deepcopy(rows)
        result = run(rows)
        result['rules'][0]['path'] = '/changed'
        result['rules'].append({})
        result['targets'].append('changed')
        self.assertEqual(rows, original)
        self.assertEqual(run(rows), {
            'rules': [{'path': '/a', 'target': 'svc', 'priority': 1}],
            'targets': ['svc'],
        })
        validated = validate(rows)
        validated[0]['target'] = 'changed'
        self.assertEqual(rows, original)
        invalid = rows + [{'path': '/bad', 'target': [], 'priority': 0}]
        before = copy.deepcopy(invalid)
        with self.assertRaises(ValueError):
            run(invalid)
        self.assertEqual(invalid, before)

    def test_render_exact_bytes(self):
        rows = [{'path': '/É', 'target': ' A"\nB\\ ', 'priority': 0}]
        self.assertEqual(render(rows),
                         '{"rules":[{"path":"/é","priority":0,"target":"a\\"\\nb\\\\"}],"targets":["a\\"\\nb\\\\"]}\n')

    def test_empty_results(self):
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        first, second = run([]), run([])
        self.assertIsNot(first['rules'], second['rules'])
        self.assertIsNot(first['targets'], second['targets'])

    def test_batch_outer_inputs(self):
        for entrypoint in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([])):
                with self.subTest(entrypoint=entrypoint, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                        entrypoint(batches)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_results_and_rendering(self):
        class Batches(list):
            pass

        batches = Batches([
            [{'path': ' A//B/ ', 'target': ' First ', 'priority': 0},
             {'path': '/a/b', 'target': 'Winner', 'priority': 2},
             {'path': '//A//B//', 'target': 'Later', 'priority': 2},
             {'path': '/', 'target': 'Root', 'priority': -1}],
            [],
            [{'path': '/É', 'target': ' A"\nB\\ ', 'priority': 0}],
        ])
        before = copy.deepcopy(batches)
        expected = [run(rows) for rows in batches]
        results = run_many(batches)
        self.assertEqual(results, expected)
        self.assertEqual(list(results[0]), ['rules', 'targets'])
        self.assertEqual(list(results[0]['rules'][0]), ['path', 'target', 'priority'])
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(render_many([[]]), '{"rules":[],"targets":[]}\n')
        self.assertEqual(batches, before)

    def test_batch_member_errors_and_immutability(self):
        valid = [{'path': ' A/ ', 'target': ' SVC ', 'priority': 1}]
        invalid = [dict(valid[0], priority=True)]
        for entrypoint in (run_many, render_many):
            for member, error, message in (
                (None, TypeError, 'routing: rows must be a list'),
                ((), TypeError, 'routing: rows must be a list'),
                (invalid, ValueError, 'routing: invalid row'),
            ):
                for batches in ([member, valid], [valid, member, valid]):
                    before = copy.deepcopy(batches)
                    with self.subTest(entrypoint=entrypoint, batches=batches):
                        with self.assertRaisesRegex(error, '^' + message + '$'):
                            entrypoint(batches)
                        self.assertEqual(batches, before)

    def test_batch_validation_precedes_domain_processing(self):
        rows = [{'path': '/A', 'target': 'svc', 'priority': 1},
                {'path': '/bad', 'target': '', 'priority': 1}]
        for entrypoint in (run_many, render_many):
            with patch('project.policy.normalize', side_effect=AssertionError('too early')):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    entrypoint([rows])

    def test_batch_results_are_independent(self):
        rows = [{'path': ' A/ ', 'target': ' SVC ', 'priority': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        expected = copy.deepcopy(first)
        second = run_many(batches)
        first[0]['rules'][0]['path'] = '/changed'
        first[0]['rules'].append({})
        first[0]['targets'].append('changed')
        first[2]['rules'].append({})
        first[2]['targets'].append('changed')
        self.assertEqual(first[1], expected[1])
        self.assertEqual(first[3], expected[3])
        self.assertEqual(second, expected)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
