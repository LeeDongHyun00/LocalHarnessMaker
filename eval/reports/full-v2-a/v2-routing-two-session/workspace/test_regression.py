import copy
import json
import unittest

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self):
        rows = [
            {'path': ' A///B/ ', 'target': ' First ', 'priority': 0},
            {'path': '/a/b', 'target': ' Winner ', 'priority': 2},
            {'path': '//A/B//', 'target': ' Tie ', 'priority': 2},
            {'path': ' /// ', 'target': ' ROOT ', 'priority': -1},
        ]
        self.assertEqual(project.run(rows), {
            'rules': [
                {'path': '/a/b', 'target': 'winner', 'priority': 2},
                {'path': '/', 'target': 'root', 'priority': -1},
            ],
            'targets': ['root', 'winner'],
        })

    def test_ordering_and_target_normalization(self):
        rows = [
            {'path': path, 'target': target, 'priority': priority}
            for path, target, priority in [
                ('/z', ' SVC// ', 1), ('/bb', 'Straße', 1),
                ('/aa', 'STRASSE', 1), ('/x', ' SVC// ', 2),
            ]
        ]
        result = project.run(rows)
        self.assertEqual([r['path'] for r in result['rules']], ['/x', '/aa', '/bb', '/z'])
        self.assertEqual(result['targets'], ['strasse', 'svc//'])
        self.assertEqual(list(result), ['rules', 'targets'])
        self.assertTrue(all(list(row) == ['path', 'target', 'priority'] for row in result['rules']))

    def test_validation_errors_and_precedence(self):
        class IntSubclass(int):
            pass

        valid = {'path': '/a', 'target': 'svc', 'priority': 1}
        invalid = [None, {}, dict(valid, extra=1)]
        for key in valid:
            missing = dict(valid)
            del missing[key]
            invalid.append(missing)
        for key in ('path', 'target'):
            invalid.extend(dict(valid, **{key: value}) for value in (None, 1, '', ' \t\n'))
        invalid.extend(dict(valid, priority=value) for value in (True, False, IntSubclass(1), 1.0, '1', None))
        for row in invalid:
            # The preceding canonical collision must not mask a later bad row.
            rows = [valid, dict(valid, path='//A/', target='other'), row]
            original = copy.deepcopy(rows)
            for call in (project.run, project.render, engine.compute, validation.validate):
                with self.subTest(row=row, call=call.__name__):
                    with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                        call(rows)
                    self.assertEqual(rows, original)
        for rows in (None, (), {}, 'rows', iter([])):
            for call in (project.run, project.render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                    call(rows)

    def test_batch_outer_validation_and_empty(self):
        for call in (project.run_many, project.render_many):
            for batches in (None, (), {}, 'batches', iter([]), 1):
                with self.subTest(call=call.__name__, batches=batches):
                    with self.assertRaisesRegex(TypeError, '^routing: batches must be a list$'):
                        call(batches)
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')

    def test_batch_order_policy_and_render(self):
        batches = [
            [
                {'path': ' A///B/ ', 'target': ' First ', 'priority': 0},
                {'path': '/a/b', 'target': ' Winner ', 'priority': 2},
                {'path': '//A/B//', 'target': ' Tie ', 'priority': 2},
                {'path': ' /// ', 'target': ' ROOT ', 'priority': -1},
            ],
            [],
            [{'path': '/É/"', 'target': '雪\n"\\', 'priority': -2}],
        ]
        original = copy.deepcopy(batches)
        results = project.run_many(batches)
        self.assertEqual(results, [project.run(rows) for rows in batches])
        self.assertEqual(list(results[0]), ['rules', 'targets'])
        self.assertEqual(list(results[0]['rules'][0]), ['path', 'target', 'priority'])
        rendered = project.render_many(batches)
        self.assertEqual(rendered, ''.join(project.render(rows) for rows in batches))
        self.assertEqual(rendered.count('\n'), len(batches))
        self.assertTrue(rendered.endswith('\n'))
        self.assertIn('雪', rendered)
        self.assertEqual(batches, original)

    def test_batch_member_errors_and_no_mutation(self):
        class IntSubclass(int):
            pass

        valid = {'path': ' A/ ', 'target': ' SVC ', 'priority': 1}
        invalid_rows = [None, {}, dict(valid, extra=1)]
        for key in valid:
            missing = dict(valid)
            del missing[key]
            invalid_rows.append(missing)
        for key in ('path', 'target'):
            invalid_rows.extend(dict(valid, **{key: value}) for value in (None, 1, '', ' \t\n'))
        invalid_rows.extend(dict(valid, priority=value) for value in (True, False, IntSubclass(1), 1.0, '1', None))
        invalid_members = [(value, TypeError, 'routing: rows must be a list')
                           for value in (None, (), {}, 'rows', 1)]
        invalid_members.extend(([valid, dict(valid, path='//A/'), row], ValueError,
                                'routing: invalid row') for row in invalid_rows)
        for member, error_type, message in invalid_members:
            for position in range(3):
                batches = [[valid], [valid]]
                batches.insert(position, member)
                original = copy.deepcopy(batches)
                for call in (project.run_many, project.render_many):
                    with self.subTest(call=call.__name__, member=member, position=position):
                        with self.assertRaises(error_type) as raised:
                            call(batches)
                        self.assertEqual(str(raised.exception), message)
                        self.assertEqual(batches, original)
        # Member validation follows encounter order, even across error types.
        for call in (project.run_many, project.render_many):
            with self.assertRaisesRegex(ValueError, '^routing: invalid row$'):
                call([[{}], None])
            with self.assertRaisesRegex(TypeError, '^routing: rows must be a list$'):
                call([None, [{}]])

    def test_batch_subclasses_and_independent_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(path=' A/ ', target=' SVC ', priority=0)])
        batches = Rows([rows, rows, [], []])
        original = copy.deepcopy(batches)
        expected = [project.run(member) for member in batches]
        result = project.run_many(batches)
        self.assertEqual(result, expected)
        self.assertEqual(project.render_many(batches), ''.join(project.render(member) for member in batches))
        self.assertIsNot(result[0]['rules'][0], rows[0])
        for left in range(len(result)):
            for right in range(left + 1, len(result)):
                self.assertIsNot(result[left], result[right])
                for key in ('rules', 'targets'):
                    self.assertIsNot(result[left][key], result[right][key])
        self.assertIsNot(result[0]['rules'][0], result[1]['rules'][0])
        result[0]['rules'][0]['target'] = 'changed'
        result[0]['rules'].append({})
        result[0]['targets'].append('changed')
        result[2]['rules'].append({})
        result[2]['targets'].append('changed')
        self.assertEqual(result[1], expected[1])
        self.assertEqual(result[3], expected[3])
        result.append({})
        self.assertEqual(batches, original)
        self.assertEqual(project.run_many(batches), expected)
        self.assertEqual(project.run(rows), expected[0])
        empty = project.run_many([])
        empty.append({})
        self.assertEqual(project.run_many([]), [])

    def test_subclasses_and_fresh_results(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(priority=0, target=' SVC ', path=' A/ ')])
        original = copy.deepcopy(rows)
        expected = {'rules': [{'path': '/a', 'target': 'svc', 'priority': 0}], 'targets': ['svc']}
        result = project.run(rows)
        self.assertEqual(result, expected)
        self.assertEqual(list(result['rules'][0]), ['path', 'target', 'priority'])
        self.assertIsNot(result['rules'][0], rows[0])
        result['rules'][0]['target'] = 'changed'
        result['rules'].append({})
        result['targets'].append('changed')
        validated = validation.validate(rows)
        validated[0]['path'] = '/changed'
        self.assertEqual(rows, original)
        self.assertEqual(project.run(rows), expected)

    def test_render_and_empty(self):
        rows = [{'path': '/É/"', 'target': '雪\n"\\', 'priority': -2}]
        expected = json.dumps(project.run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), expected)
        self.assertIn('雪', project.render(rows))
        self.assertEqual(project.run([]), {'rules': [], 'targets': []})
        self.assertEqual(project.render([]), '{"rules":[],"targets":[]}\n')
        empty = project.run([])
        empty['rules'].append({})
        empty['targets'].append('svc')
        self.assertEqual(project.run([]), {'rules': [], 'targets': []})
        self.assertEqual(policy.normalize(' STRAẞE///X/ '), '/strasse/x')


if __name__ == '__main__':
    unittest.main()
