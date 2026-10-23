import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class RoutingRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'path': ' //Straße///A/ ', 'target': ' First ', 'priority': 0},
            {'path': '/STRASSE/a', 'target': 'Second', 'priority': 0},
            {'path': '/strasse//a/', 'target': ' Winner ', 'priority': 1},
            {'path': '/STRASSE/A/', 'target': 'Later', 'priority': 1},
        ]
        self.assertEqual(run(rows), {
            'rules': [{'path': '/strasse/a', 'target': 'winner', 'priority': 1}],
            'targets': ['winner'],
        })
        self.assertEqual(normalize(' ///Straße///A// '), '/strasse/a')
        self.assertEqual(normalize(' /// '), '/')

    def test_order_and_targets(self):
        rows = [
            {'path': path, 'target': target, 'priority': priority}
            for path, target, priority in [
                ('/', ' Z ', -1), ('b', 'B', 0), ('a', 'B', 0),
                ('long', 'A', 0), ('top', 'Z', 2),
            ]
        ]
        result = run(rows)
        self.assertEqual(list(result), ['rules', 'targets'])
        self.assertEqual([r['path'] for r in result['rules']],
                         ['/top', '/long', '/a', '/b', '/'])
        self.assertEqual(result['targets'], ['a', 'b', 'z'])
        self.assertEqual(list(result['rules'][0]), ['path', 'target', 'priority'])

    def test_invalid_inputs_across_entry_points(self):
        class IntSubclass(int):
            pass

        good = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid = [None, [], {}, {**good, 'extra': 1}]
        for field, values in [
            ('path', [None, 1, '', ' \t\n']),
            ('target', [None, [], '', ' \t\n']),
            ('priority', [True, False, 1.0, '1', IntSubclass(1)]),
        ]:
            invalid.extend({**good, field: value} for value in values)
        for field in good:
            invalid.append({k: v for k, v in good.items() if k != field})
        for api in (run, compute, validate, render):
            for outer in (None, {}, (), 'rows', iter([])):
                with self.subTest(api=api.__name__, outer=type(outer)):
                    with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                        api(outer)
            for bad in invalid:
                # Canonical duplicates must not prevent validation of later rows.
                rows = [good, {**good, 'target': 'other'}, bad]
                before = copy.deepcopy(rows)
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_allowed_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' A// ', target=' SVC ', priority=-2)])
        before = copy.deepcopy(rows)
        expected = {'rules': [{'path': '/a', 'target': 'svc', 'priority': -2}],
                    'targets': ['svc']}
        for api in (run, compute):
            result = api(rows)
            self.assertEqual(result, expected)
            result['rules'][0]['path'] = '/changed'
            result['rules'].append({})
            result['targets'].append('changed')
            self.assertEqual(api(rows), expected)
            self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['target'] = 'changed'
        self.assertEqual(rows, before)

    def test_render_and_batches(self):
        rows = [{'path': ' //É/// ', 'target': 'Svc"\n\\雪', 'priority': 0}]
        expected = json.dumps(run(rows), sort_keys=True, ensure_ascii=False,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render(rows).count('\n'), 1)
        self.assertIn('雪', render(rows))
        batches = [rows, [], rows]
        before = copy.deepcopy(batches)
        results = run_many(batches)
        self.assertEqual(results, [run(rows), run([]), run(rows)])
        self.assertEqual(render_many(batches), expected + render([]) + expected)
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['targets'].clear()
        self.assertEqual(results[2], run(rows))
        self.assertEqual(run_many(batches), [run(rows), run([]), run(rows)])
        self.assertEqual(batches, before)

    def test_batch_errors_and_empty_inputs(self):
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for outer in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    api(outer)
            for member, error, message in [
                (None, TypeError, 'routing: rows must be a list'),
                ([{}], ValueError, 'routing: invalid row'),
            ]:
                batches = [[{'path': '/a', 'target': 'svc', 'priority': 1}], member]
                before = copy.deepcopy(batches)
                with self.assertRaisesRegex(error, '^' + message + '$'):
                    api(batches)
                self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
