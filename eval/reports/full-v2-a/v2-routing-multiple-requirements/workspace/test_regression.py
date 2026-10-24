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


class RoutingRegressions(unittest.TestCase):
    def test_domain_edge(self):
        # A segment ancestor shadows /a/b, but must not shadow /ab.
        self.assertEqual(run([row('/a', priority=2), row('/a/b'), row('/ab')]),
                         {'rules': [row('/a', priority=2), row('/ab')],
                          'targets': ['svc']})

    def test_canonicalization_and_duplicate_order(self):
        rows = [row(' A///B/ ', ' Z ', 0), row('/a/b', ' Ä ', 0),
                row('//A/b/', ' A ', 0), row('/a/b', 'lowest', -1)]
        for permutation in itertools.permutations(rows):
            self.assertEqual(run(list(permutation)),
                             {'rules': [row('/a/b', 'a', 0)], 'targets': ['a']})
        self.assertEqual(normalize(' //Straße///B/ '), '/strasse/b')
        self.assertEqual(normalize(' /// '), '/')
        self.assertEqual(validate([row(' X/ ', ' Straße ')]),
                         [row('/x', 'strasse')])

    def test_complete_set_and_root_shadowing(self):
        rows = [row('/a/b', priority=-1), row('/a', priority=0),
                row('/', priority=1), row('/other', 'other', -2),
                row('/higher', priority=2)]
        self.assertEqual(run(rows), {
            'rules': [row('/higher', priority=2), row('/', priority=1),
                      row('/other', 'other', -2)],
            'targets': ['other', 'svc'],
        })

    def test_sorting_and_mapping_order(self):
        result = run([row('/b', 'z'), row('/a', 'a'), row('/long', 'b'),
                      row('/low', 'z', 0)])
        self.assertEqual([r['path'] for r in result['rules']],
                         ['/long', '/a', '/b', '/low'])
        self.assertEqual(result['targets'], ['a', 'b', 'z'])
        self.assertEqual(list(result), ['rules', 'targets'])
        self.assertEqual(list(result['rules'][0]), ['path', 'target', 'priority'])

    def test_validation_across_entry_points(self):
        class IntSubclass(int):
            pass

        invalid = [None, [], {}, row(' '), row('/a', ''), row(1),
                   row('/a', None), row('/a', priority=True),
                   row('/a', priority=IntSubclass(1)), row('/a', priority=1.0),
                   dict(row('/a'), extra=1)]
        for bad in invalid:
            rows = [row('/a'), row('/a', 'conflict'), bad]
            before = copy.deepcopy(rows)
            for call in (run, compute, validate, render,
                         lambda r: run_many([[row('/')], r]),
                         lambda r: render_many([[row('/')], r])):
                with self.subTest(bad=bad, call=call):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        call(rows)
                    self.assertEqual(rows, before)
        for bad in (None, (), {}, 'rows', iter([])):
            for call in (run, compute, validate, render):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    call(bad)
        for call in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                call([[], ()])
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                    call(bad)

    def test_subclasses_and_result_isolation(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(row(' A/ ', ' SVC '))])
        before = copy.deepcopy(rows)
        results = run_many(Rows([rows, rows]))
        results[0]['rules'][0]['target'] = 'changed'
        results[0]['rules'].append(row('/new'))
        results[0]['targets'].append('changed')
        expected = {'rules': [row('/a')], 'targets': ['svc']}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        validated = validate(rows)
        validated[0]['path'] = '/changed'
        self.assertEqual(rows, before)

    def test_render_and_batches(self):
        rows = [row(' /É/ ', ' 서비스\n"\\ ')]
        before = copy.deepcopy(rows)
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertIn('서비스', expected)
        self.assertEqual(render_many([rows, [], rows]),
                         expected + render([]) + expected)
        self.assertEqual(run_many([rows, [], rows]), [run(rows), run([]), run(rows)])
        self.assertEqual(rows, before)

    def test_empty_results(self):
        self.assertEqual(run([]), {'rules': [], 'targets': []})
        self.assertEqual(validate([]), [])
        self.assertEqual(render([]), '{"rules":[],"targets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        first, second = run_many([[], []])
        first['rules'].append(row('/new'))
        first['targets'].append('svc')
        self.assertEqual(second, {'rules': [], 'targets': []})


if __name__ == '__main__':
    unittest.main()
