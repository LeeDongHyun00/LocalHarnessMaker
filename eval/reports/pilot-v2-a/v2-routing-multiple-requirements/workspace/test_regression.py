import copy
import itertools
import json
import unittest

from project import render, render_many, run, run_many
from project.engine import compute
from project.policy import normalize
from project.validation import validate


def row(path, target='svc', priority=1):
    return {'path': path, 'target': target, 'priority': priority}


class RoutingRegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        # Equal-priority ancestors shadow descendants, but not sibling prefixes.
        self.assertEqual(run([row('/a'), row('/a/b'), row('/ab')]),
                         {'rules': [row('/ab'), row('/a')], 'targets': ['svc']})

    def test_canonicalization_and_duplicate_order(self):
        rows = [row(' A///B/ ', ' Z '), row('/a/b', ' Ä '),
                row('/A//B/', ' A '), row('/a/b', 'loser', 0)]
        for permutation in itertools.permutations(rows):
            self.assertEqual(run(list(permutation)),
                             {'rules': [row('/a/b', 'a')], 'targets': ['a']})
        self.assertEqual(normalize(' //// '), '/')
        self.assertEqual(validate([row(' STRASSE/// ', ' Straße ')]),
                         [row('/strasse', 'strasse')])

    def test_complete_ancestor_set_and_sorting(self):
        rows = [row('/', 'svc', 0), row('/a', 'svc', 0),
                row('/a/b', 'svc', -1), row('/a/c', 'other', 0),
                row('/deep/x', 'svc', 2), row('/zz', 'z', 2),
                row('/aa', 'a', 2)]
        expected = {'rules': [row('/deep/x', 'svc', 2), row('/aa', 'a', 2),
                              row('/zz', 'z', 2), row('/a/c', 'other', 0),
                              row('/', 'svc', 0)],
                    'targets': ['a', 'other', 'svc', 'z']}
        self.assertEqual(compute(rows), expected)
        self.assertEqual(run(list(reversed(rows))), expected)
        self.assertEqual(list(expected), list(run(rows)))

    def test_validation_across_entry_points(self):
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {}, row('  '), row('/a', ''),
                        row(3), row('/a', None), row('/a', priority=True),
                        row('/a', priority=IntSubclass(1)),
                        row('/a', priority=1.0),
                        dict(row('/a'), extra=1)]
        for invalid in invalid_rows:
            rows = [row('/a', 'z'), row('/a', 'a'), invalid]
            before = copy.deepcopy(rows)
            for call in (validate, compute, run, render,
                         lambda rows: run_many([[], rows]),
                         lambda rows: render_many([[], rows])):
                with self.subTest(invalid=invalid, call=call):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        call(rows)
                    self.assertEqual(rows, before)
        for value in (None, (), {}, 'rows'):
            for call in (validate, compute, run, render):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    call(value)
            for call in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    call(value)
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    call([[], value])

    def test_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(row(' /A/ ', ' SVC '))])
        before = copy.deepcopy(rows)
        expected = {'rules': [row('/a')], 'targets': ['svc']}
        results = run_many([rows, rows])
        self.assertEqual(results, [expected, expected])
        self.assertIsNot(results[0]['rules'][0], rows[0])
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['targets'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        validated = validate(rows)
        validated[0]['path'] = 'changed'
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['rules'].append(row('/a'))
        self.assertEqual(empty[1], {'rules': [], 'targets': []})

    def test_render_and_batch_order(self):
        rows = [row('/Straße', ' 한글"\\\n ')]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertIn('한글', expected)
        self.assertEqual(render_many([rows, [], rows]),
                         expected + render([]) + expected)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run([]), {'rules': [], 'targets': []})


if __name__ == '__main__':
    unittest.main()
