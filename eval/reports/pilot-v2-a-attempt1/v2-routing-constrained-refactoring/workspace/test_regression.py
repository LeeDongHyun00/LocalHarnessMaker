import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RoutingRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'path': ' A//B/ ', 'target': 'First', 'priority': -1},
            {'path': '/a/b', 'target': 'Winner', 'priority': 0},
            {'path': '//A/B//', 'target': 'Equal', 'priority': 0},
            {'path': '///', 'target': ' ROOT ', 'priority': 0},
            {'path': '/c', 'target': 'C', 'priority': 0},
            {'path': '/b', 'target': 'B', 'priority': 0},
        ]
        self.assertEqual(run(rows), {
            'rules': [
                {'path': '/a/b', 'target': 'winner', 'priority': 0},
                {'path': '/b', 'target': 'b', 'priority': 0},
                {'path': '/c', 'target': 'c', 'priority': 0},
                {'path': '/', 'target': 'root', 'priority': 0},
            ],
            'targets': ['b', 'c', 'root', 'winner'],
        })

    def test_runtime_policy_patch(self):
        rows = [{'path': ' /Original// ', 'target': ' Target// ', 'priority': 1}]
        expected = {'rules': [{'path': '/patched', 'target': 'target//', 'priority': 1}],
                    'targets': ['target//']}
        serialized = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        with patch('project.policy.normalize', return_value='/patched') as patched:
            self.assertEqual(run(rows), expected)
            self.assertEqual(render(rows), serialized)
            self.assertEqual(run_many([rows, rows]), [expected, expected])
            self.assertEqual(render_many([rows, rows]), serialized * 2)
            self.assertEqual(compute(rows), expected)
            self.assertEqual(validate(rows), expected['rules'])
            self.assertEqual(patched.call_args_list, [unittest.mock.call(' /Original// ')] * 8)

    def test_field_validation(self):
        class IntSubclass(int):
            pass

        valid = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid = [None, [], {}, {**valid, 'extra': 1}]
        for key in valid:
            invalid.append({k: v for k, v in valid.items() if k != key})
        for key in ('path', 'target'):
            for value in (None, 1, '', ' \t\n'):
                invalid.append({**valid, key: value})
        for value in (True, False, IntSubclass(1), 1.0, '1', None):
            invalid.append({**valid, 'priority': value})
        for row in invalid:
            rows = [valid, {**valid, 'target': 'conflict'}, row]
            before = copy.deepcopy(rows)
            for api in (run, render, compute, validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    api([[valid], rows])
                self.assertEqual(rows, before)

    def test_input_shapes_and_empty_results(self):
        for value in (None, {}, (), 'rows', 1):
            for api in (run, render, compute, validate):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    api(value)
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api([[], value])
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_results_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' A//B/ ', target=' SVC ', priority=-2)])
        before = copy.deepcopy(rows)
        expected = run(rows)
        result = run_many(Rows([rows, rows]))
        result[0]['rules'][0]['target'] = 'changed'
        result[0]['rules'].append({})
        result[0]['targets'].append('changed')
        self.assertEqual(result[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['path'] = '/changed'
        self.assertEqual(rows, before)

    def test_unicode_json_and_batch_order(self):
        first = [{'path': ' //Straße/// ', 'target': ' 한글"\n ', 'priority': 2}]
        second = [{'path': '/', 'target': 'Other', 'priority': 0}]
        self.assertEqual(normalize(' //Straße/// '), '/strasse')
        serialized = render(first)
        self.assertEqual(serialized, json.dumps(run(first), sort_keys=True,
                                              separators=(',', ':'), ensure_ascii=False) + '\n')
        self.assertIn('한글', serialized)
        self.assertEqual(run_many([first, second]), [run(first), run(second)])
        self.assertEqual(render_many([first, second]), render(first) + render(second))


if __name__ == '__main__':
    unittest.main()
