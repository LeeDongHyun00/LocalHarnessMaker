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
            {'path': ' A///B/ ', 'target': ' Old ', 'priority': -2},
            {'path': '/a/b', 'target': ' First ', 'priority': 0},
            {'path': '//A/B//', 'target': ' Tied ', 'priority': 0},
            {'path': '/z', 'target': ' Z ', 'priority': 0},
            {'path': '/a', 'target': ' A ', 'priority': 0},
            {'path': '///', 'target': ' Root ', 'priority': -1},
        ]
        self.assertEqual(run(rows), {
            'rules': [
                {'path': '/a/b', 'target': 'first', 'priority': 0},
                {'path': '/a', 'target': 'a', 'priority': 0},
                {'path': '/z', 'target': 'z', 'priority': 0},
                {'path': '/', 'target': 'root', 'priority': -1},
            ],
            'targets': ['a', 'first', 'root', 'z'],
        })

    def test_runtime_policy(self):
        rows = [{'path': '/A', 'target': ' SVC//X ', 'priority': 1}]
        expected = {'rules': [{'path': '/patched', 'target': 'svc//x', 'priority': 1}],
                    'targets': ['svc//x']}
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        with patch('project.policy.normalize', return_value='/patched') as mocked:
            self.assertEqual(run(rows), expected)
            self.assertEqual(render(rows), encoded)
            self.assertEqual(run_many([rows]), [expected])
            self.assertEqual(render_many([rows]), encoded)
            self.assertEqual(mocked.call_args_list, [unittest.mock.call('/A')] * 4)

    def test_validation_and_precedence(self):
        class IntSubclass(int):
            pass

        valid = {'path': '/a', 'target': 'svc', 'priority': 0}
        invalid_rows = [None, {}, dict(valid, extra=1)]
        for key, values in [('path', [None, 1, '', '  ']),
                            ('target', [None, 1, '', '  ']),
                            ('priority', [True, 1.0, IntSubclass(1)])]:
            invalid_rows.extend(dict(valid, **{key: value}) for value in values)
        for bad in invalid_rows:
            rows = [valid, dict(valid, target='other'), bad]
            for entry in (run, render, compute, validate):
                with self.subTest(bad=bad, entry=entry.__name__):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        entry(rows)
            with patch('project.policy.normalize', side_effect=RuntimeError('domain')):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    run(rows)
        for entry in (run, render, compute, validate):
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                entry(())
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                entry(())
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                entry([[valid], ()])

    def test_fresh_results_and_atomic_failure(self):
        rows = [{'path': ' A/ ', 'target': ' SVC ', 'priority': 1}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        expected = copy.deepcopy(results[1])
        results[0]['rules'][0]['path'] = '/changed'
        results[0]['targets'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                entry([rows, [{}]])
        self.assertEqual(rows, original)

    def test_render_and_empty_inputs(self):
        rows = [{'path': '/Ü', 'target': ' 雪"\\\nX ', 'priority': -1}]
        encoded = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, [], rows]), encoded + render([]) + encoded)
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_allowed_subclasses_and_normalize(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' Straße//X/ ', target=' STRASSE ', priority=-3)])
        self.assertEqual(compute(rows)['rules'],
                         [{'path': '/strasse/x', 'target': 'strasse', 'priority': -3}])
        self.assertEqual(validate(rows), compute(rows)['rules'])
        self.assertEqual(normalize(' /// '), '/')


if __name__ == '__main__':
    unittest.main()
