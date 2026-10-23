import copy
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


class BatchRegressionTests(unittest.TestCase):
    def test_batch_edge(self):
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [
            {'path': ' //A/// ', 'target': ' First ', 'priority': 0},
            {'path': '/a/', 'target': 'winner', 'priority': 2},
            {'path': 'a', 'target': 'tie', 'priority': 2},
            {'path': '////', 'target': ' Root ', 'priority': -1},
        ]
        expected = {'rules': [
            {'path': '/a', 'target': 'winner', 'priority': 2},
            {'path': '/', 'target': 'root', 'priority': -1},
        ], 'targets': ['root', 'winner']}
        self.assertEqual(run_many([[], rows]), [
            {'rules': [], 'targets': []}, expected])
        self.assertEqual(render_many([[], rows]), render([]) + render(rows))

    def test_ordering_and_unicode_rendering(self):
        rows = [
            {'path': '/Z', 'target': 'É"\\', 'priority': 3},
            {'path': '/BB/', 'target': 'Other', 'priority': 3},
            {'path': '/AA', 'target': 'OTHER', 'priority': 3},
            {'path': '/longer', 'target': 'Low', 'priority': -2},
        ]
        result = run(rows)
        self.assertEqual([r['path'] for r in result['rules']],
                         ['/aa', '/bb', '/z', '/longer'])
        self.assertEqual(result['targets'], ['low', 'other', 'é"\\'])
        expected = json.dumps(result, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render_many([rows, []]), expected + render([]))
        self.assertEqual(compute(rows), result)
        self.assertEqual(normalize(' ///Straße//A/// '), '/strasse/a')

    def test_invalid_outer_and_member_shapes(self):
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, batches=batches):
                    with self.assertRaisesRegex(
                            TypeError, '^routing: batches must be a list$'):
                        api(batches)
            with self.assertRaisesRegex(TypeError,
                                        '^routing: rows must be a list$'):
                api([[], ()])
        for api in (run, render, compute, validate):
            with self.assertRaisesRegex(TypeError,
                                        '^routing: rows must be a list$'):
                api(())

    def test_field_errors_after_duplicate_paths(self):
        class IntSubclass(int):
            pass

        good = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid = [None, {}, dict(good, extra=1),
                   {'path': '/a', 'target': 'svc'},
                   dict(good, path='  '), dict(good, target='\t'),
                   dict(good, path=1), dict(good, target=[]),
                   dict(good, priority=True), dict(good, priority=1.0),
                   dict(good, priority=IntSubclass(1))]
        for bad in invalid:
            rows = [good, dict(good, target='conflict'), bad]
            before = copy.deepcopy(rows)
            for api in (run, render, validate):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError,
                                                '^routing: invalid row$'):
                        api(rows)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError,
                                            '^routing: invalid row$'):
                    api([[good], rows, []])
            self.assertEqual(rows, before)

    def test_fresh_results_and_unchanged_inputs(self):
        rows = [{'path': ' A// ', 'target': ' SVC ', 'priority': 1}]
        before = copy.deepcopy(rows)
        batches = [rows, rows, [], []]
        results = run_many(batches)
        expected = run(rows)
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['rules'].append({})
        results[0]['targets'].append('changed')
        results[2]['rules'].append({})
        self.assertEqual(results[1], expected)
        self.assertEqual(results[3], {'rules': [], 'targets': []})
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(rows, before)
        normalized = validate(rows)
        normalized[0]['path'] = '/changed'
        self.assertEqual(rows, before)

    def test_list_and_dict_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' A ', target=' SVC ', priority=0)])
        expected = {'rules': [{'path': '/a', 'target': 'svc', 'priority': 0}],
                    'targets': ['svc']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render_many(Rows([rows])), render(rows))


if __name__ == '__main__':
    unittest.main()
