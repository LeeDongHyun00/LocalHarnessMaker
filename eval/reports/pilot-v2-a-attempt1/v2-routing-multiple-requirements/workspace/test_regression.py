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
        rows = [row('/a', priority=3), row('/a/b', priority=2),
                row('/ab', priority=2), row('/a/c', 'other', 1)]
        self.assertEqual(run(rows), {
            'rules': [row('/a', priority=3), row('/ab', priority=2),
                      row('/a/c', 'other', 1)],
            'targets': ['other', 'svc'],
        })

    def test_canonical_duplicates_are_order_independent(self):
        rows = [row(' A///B/ ', ' Z ', 2), row('/a/b', ' Ä ', 2),
                row('/A/B/', ' A ', 2), row('/a/b', 'zero', 0)]
        expected = {'rules': [row('/a/b', 'a', 2)], 'targets': ['a']}
        for permutation in itertools.permutations(rows):
            self.assertEqual(run(list(permutation)), expected)
        self.assertEqual(normalize(' //Straße///X/ '), '/strasse/x')
        self.assertEqual(normalize(' //// '), '/')
        self.assertEqual(validate([row(' A//B/ ', ' X//Y/ ')]),
                         [row('/a/b', 'x//y/')])

    def test_root_shadowing_and_priority(self):
        rows = [row('/', priority=0), row('/a', priority=0),
                row('/a/b', priority=-1), row('/c', priority=1),
                row('/d', 'other', -2)]
        self.assertEqual(run(rows), {
            'rules': [row('/c', priority=1), row('/', priority=0),
                      row('/d', 'other', -2)],
            'targets': ['other', 'svc'],
        })

    def test_sorting(self):
        rows = [row('/b'), row('/a'), row('/long'), row('/z', priority=2)]
        self.assertEqual(run(rows)['rules'],
                         [row('/z', priority=2), row('/long'), row('/a'), row('/b')])

    def test_validation_errors_across_entry_points(self):
        class IntSubclass(int):
            pass

        bad_rows = [None, [], {}, {'path': '/a', 'target': 'svc'},
                    dict(row('/a'), extra=1), row(' '), row('/a', ''),
                    row(1), row('/a', None), row('/a', priority=True),
                    row('/a', priority=IntSubclass(1)), row('/a', priority=1.0)]
        for bad in bad_rows:
            # A conflicting prefix must not hide a later field error.
            rows = [row('/a'), row('/A/'), bad]
            for call in (run, compute, validate, render):
                with self.subTest(bad=bad, call=call):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        call(rows)
            for call in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                    call([[row('/valid')], rows])
        for value in (None, (), {}, 'rows', iter([])):
            for call in (run, compute, validate, render):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    call(value)
        for call in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                call([[], None])

    def test_list_and_dict_subclasses(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(row('/a'))])
        self.assertEqual(run(rows), {'rules': [row('/a')], 'targets': ['svc']})
        self.assertEqual(run_many(Rows([rows])), [run(rows)])

    def test_fresh_results_and_no_input_mutation(self):
        rows = [row(' A/ ', ' SVC ')]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['rules'].append(row('/extra'))
        results[0]['targets'].append('extra')
        expected = {'rules': [row('/a')], 'targets': ['svc']}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['path'] = '/changed'
        self.assertEqual(rows, before)
        invalid = rows + [row('/bad', priority=False)]
        invalid_before = copy.deepcopy(invalid)
        for call in (run, render, validate, compute):
            with self.assertRaises(ValueError):
                call(invalid)
            self.assertEqual(invalid, invalid_before)
        for call in (run_many, render_many):
            with self.assertRaises(ValueError):
                call([rows, invalid])
            self.assertEqual(rows, before)
            self.assertEqual(invalid, invalid_before)

    def test_render_and_batch_order(self):
        rows = [row(' /한글/ ', ' SÉRVICE"\nLINE ')]
        expected = ('{"rules":[{"path":"/한글","priority":1,'
                    '"target":"sérvice\\"\\nline"}],'
                    '"targets":["sérvice\\"\\nline"]}\n')
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))
        batches = [rows, [], [row('/z')]]
        self.assertEqual(run_many(batches), [run(batch) for batch in batches])
        self.assertEqual(render_many(batches), ''.join(render(batch) for batch in batches))

    def test_empty_and_outer_validation(self):
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for value in (None, (), {}, 'batches', iter([])):
            for call in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    call(value)


if __name__ == '__main__':
    unittest.main()
