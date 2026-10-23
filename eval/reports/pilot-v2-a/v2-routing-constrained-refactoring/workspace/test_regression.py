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
            {'path': ' //A/// ', 'target': ' FIRST ', 'priority': -1},
            {'path': '/a', 'target': 'second', 'priority': -1},
            {'path': 'a/', 'target': 'winner', 'priority': 0},
            {'path': '//A', 'target': 'equal', 'priority': 0},
            {'path': '///', 'target': 'ROOT', 'priority': 0},
            {'path': '/BB/', 'target': 'Long', 'priority': 0},
            {'path': '/aa', 'target': 'Long', 'priority': 0},
        ]
        self.assertEqual(run(rows), {
            'rules': [
                {'path': '/aa', 'target': 'long', 'priority': 0},
                {'path': '/bb', 'target': 'long', 'priority': 0},
                {'path': '/a', 'target': 'winner', 'priority': 0},
                {'path': '/', 'target': 'root', 'priority': 0},
            ],
            'targets': ['long', 'root', 'winner'],
        })

    def test_runtime_policy_for_all_entry_points(self):
        rows = [{'path': ' //A/ ', 'target': ' //SVC/ ', 'priority': 1}]
        expected = {'rules': [{'path': '/patched', 'target': '//svc/', 'priority': 1}],
                    'targets': ['//svc/']}
        with patch('project.policy.normalize', return_value='/patched') as policy:
            self.assertEqual(run(rows), expected)
            self.assertEqual(json.loads(render(rows)), expected)
            self.assertEqual(run_many([rows]), [expected])
            self.assertEqual(json.loads(render_many([rows])), expected)
            self.assertEqual(compute(rows), expected)
            self.assertEqual(validate(rows), expected['rules'])
        self.assertEqual(policy.call_count, 6)
        policy.assert_called_with(' //A/ ')
        self.assertEqual(normalize(' //Straße///X/ '), '/strasse/x')

    def test_validation_and_precedence(self):
        class IntSubclass(int):
            pass

        good = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid = [None, {}, dict(good, extra=1),
                   {'path': '/a', 'priority': 1},
                   dict(good, path=' '), dict(good, target='\t'),
                   dict(good, path=1), dict(good, target=None),
                   dict(good, priority=True), dict(good, priority=IntSubclass(1)),
                   dict(good, priority=1.0)]
        for bad in invalid:
            rows = [good, dict(good, target='conflict'), bad]
            before = copy.deepcopy(rows)
            with self.subTest(bad=bad):
                with patch('project.policy.normalize', side_effect=RuntimeError('domain')) as policy:
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        run(rows)
                    policy.assert_not_called()
                self.assertEqual(rows, before)
        for entry in (run, render, compute, validate):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    entry(rows)

    def test_batches_and_fresh_results(self):
        rows = [{'path': '/A', 'target': 'SVC', 'priority': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['targets'].append('changed')
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, before)
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        for entry in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                entry(())
            with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                entry([rows, [{}]])
            self.assertEqual(rows, before)
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                entry([rows, None])
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run([]), {'rules': [], 'targets': []})

    def test_json_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' /É/ ', target=' S"VC\n\\É ', priority=-2)])
        expected = {'rules': [{'path': '/é', 'target': 's"vc\n\\é', 'priority': -2}],
                    'targets': ['s"vc\n\\é']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False,
                                                 sort_keys=True, separators=(',', ':')) + '\n')


if __name__ == '__main__':
    unittest.main()
