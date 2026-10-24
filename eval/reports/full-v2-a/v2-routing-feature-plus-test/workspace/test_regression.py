import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class BatchTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'path': ' A///B/ ', 'target': ' First ', 'priority': -1},
            {'path': '/a/b', 'target': ' Winner ', 'priority': 0},
            {'path': '//A/B//', 'target': 'Tie', 'priority': 0},
            {'path': ' /// ', 'target': ' ROOT ', 'priority': 0},
            {'path': '/z', 'target': ' Z ', 'priority': 0},
            {'path': '/a', 'target': ' Z ', 'priority': 0},
        ]
        expected = {'rules': [
            {'path': '/a/b', 'target': 'winner', 'priority': 0},
            {'path': '/a', 'target': 'z', 'priority': 0},
            {'path': '/z', 'target': 'z', 'priority': 0},
            {'path': '/', 'target': 'root', 'priority': 0},
        ], 'targets': ['root', 'winner', 'z']}
        empty = {'rules': [], 'targets': []}
        before = copy.deepcopy(rows)
        self.assertEqual(run_many([[], rows]), [empty, expected])
        self.assertEqual(render_many([[], rows]), render([]) + render(rows))
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), expected)
        self.assertEqual(compute(rows), expected)
        self.assertEqual(list(run(rows)), ['rules', 'targets'])
        self.assertEqual(list(run(rows)['rules'][0]), ['path', 'target', 'priority'])
        self.assertEqual(normalize(' //A///B/ '), '/a/b')

    def test_validation_and_atomic_failure(self):
        class IntSubclass(int):
            pass

        valid = {'path': '/a', 'target': 'svc', 'priority': 1}
        # A later field error must still be found after a duplicate path.
        duplicate = dict(valid, target='other')
        invalid_rows = [
            None, {}, dict(valid, extra=1),
            {'path': '/a', 'target': 'svc'},
            dict(valid, path='  '), dict(valid, target=' '),
            dict(valid, path=1), dict(valid, target=None),
            dict(valid, priority=True), dict(valid, priority=1.0),
            dict(valid, priority=IntSubclass(1)),
        ]
        for bad in invalid_rows:
            rows = [valid, duplicate, bad]
            before = copy.deepcopy(rows)
            for api, argument in ((run, rows), (render, rows),
                                  (compute, rows), (validate, rows),
                                  (run_many, [[valid], rows]),
                                  (render_many, [[valid], rows])):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        api(argument)
                    self.assertEqual(rows, before)
        for bad in (None, (), {}, 'rows', iter([])):
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    api(bad)
            for api in (run, render, compute, validate):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api(bad)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    api([[], bad])

    def test_fresh_results_and_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' /A/ ', target=' SVC ', priority=1)])
        before = copy.deepcopy(rows)
        results = run_many(Rows([rows, rows]))
        expected = {'rules': [{'path': '/a', 'target': 'svc', 'priority': 1}],
                    'targets': ['svc']}
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['rules'].append({})
        results[0]['targets'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['target'] = 'changed'
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['rules'].append({})
        empty[0]['targets'].append('changed')
        self.assertEqual(empty[1], {'rules': [], 'targets': []})

    def test_unicode_json(self):
        rows = [{'path': ' STRASSE//É/ ', 'target': ' Straße\n"\\ ', 'priority': -2}]
        expected = {'rules': [{'path': '/strasse/é', 'target': 'strasse\n"\\',
                               'priority': -2}], 'targets': ['strasse\n"\\']}
        text = json.dumps(expected, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False) + '\n'
        self.assertEqual(render(rows), text)
        self.assertEqual(render_many([rows, [], rows]), text + render([]) + text)
        self.assertEqual(run_many([rows]), [expected])


if __name__ == '__main__':
    unittest.main()
