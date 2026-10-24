import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


def row(name='file', digest='SHA', size=1):
    return {'id': name, 'target': digest, 'value': size}


class RegressionTests(unittest.TestCase):
    def assert_error(self, api, argument, kind, message):
        with self.assertRaises(kind) as caught:
            api(argument)
        self.assertEqual(str(caught.exception), 'filesystem-manifests: ' + message)

    def test_domain_edge(self):
        rows = [row(' Dir/FILE ', ' SHA ', 7), row('dir/file', 'sha', 7),
                row('A', 'Other', 0)]
        expected = {'files': {'a': {'digest': 'other', 'size': 0},
                              'dir/file': {'digest': 'sha', 'size': 7}}, 'bytes': 7}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'files': {}, 'bytes': 0}])
        self.assertEqual(project.render_many([rows, []]), project.render(rows) + project.render([]))
        self.assert_error(project.run, [row('X'), row('x', size=2)], ValueError, 'duplicate id')

    def test_structural_validation_and_precedence(self):
        malformed = [None, {}, row(size=True), row(size=1.0), row(name='  '),
                     row(digest='\t'), row(name=3), dict(row(), extra=1)]
        for bad in malformed:
            for api in (project.run, project.render, engine.compute, validation.validate):
                with self.subTest(bad=bad, api=api.__name__):
                    self.assert_error(api, [row('../bad', size=-1), row('X'),
                                            row('x', size=2), bad], ValueError, 'invalid row')
        for api in (project.run, project.render, engine.compute, validation.validate):
            for bad in (None, (), {}, 'rows'):
                self.assert_error(api, bad, TypeError, 'rows must be a list')

    def test_subclasses_and_unbounded_integers(self):
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(id=Text(' FILE '), target=Text(' HASH '), value=10 ** 100)])
        self.assertEqual(project.run(rows)['bytes'], 10 ** 100)
        self.assert_error(project.run, [row(size=Integer(1))], ValueError, 'invalid row')

    def test_validation_retains_all_rows_and_order(self):
        rows = [row(' Z ', ' SS ', -2), row('z', 'ss', -2), row('../A')]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('z', 'ss', -2), row('z', 'ss', -2), row('../a', 'sha')])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical, rows)
        for new, old in zip(canonical, rows):
            self.assertIsNot(new, old)
        self.assertIsNot(canonical[0], canonical[1])

    def test_text_and_dictionary_order(self):
        rows = [row(' Z/É ß\\X ', ' DIGEST/ß  É '), row('A')]
        result = project.run(rows)
        self.assertEqual(policy.normalize(' É ß/\\  X '), 'é ss/\\  x')
        self.assertEqual(list(result), ['files', 'bytes'])
        self.assertEqual(list(result['files']), ['a', 'z/é ss\\x'])
        self.assertEqual(list(result['files']['a']), ['digest', 'size'])
        self.assertEqual(result['files']['z/é ss\\x']['digest'], 'digest/ss  é')
        self.assertEqual(project.render(rows), json.dumps(result, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')

    def test_domain_errors_and_precedence(self):
        for name in ('/a', 'a/', 'a//b', '.', '..', 'a/./b', 'a/../b'):
            for api in (project.run, project.render, engine.compute):
                self.assert_error(api, [row(size=-1), row(name)], ValueError, 'invalid path')
        self.assert_error(project.run, [row(size=-1)], ValueError, 'negative size')
        self.assert_error(project.run, [row('../a'), row('X'), row('x', size=2)],
                          ValueError, 'duplicate id')
        self.assertEqual(project.run([row('a\\..\\b')])['bytes'], 1)

    def test_empty_and_independent_outputs(self):
        self.assertEqual(project.run([]), {'files': {}, 'bytes': 0})
        self.assertEqual(project.render([]), '{"bytes":0,"files":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        rows = [row()]
        before = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        outputs[0]['files']['file']['digest'] = 'changed'
        outputs[0]['files']['extra'] = {}
        self.assertEqual(outputs[1], project.run(rows))
        self.assertEqual(rows, before)
        empties = project.run_many([[], []])
        empties[0]['files']['x'] = {}
        self.assertEqual(empties[1], {'files': {}, 'bytes': 0})

    def test_batch_order_atomicity_and_errors(self):
        for api in (project.run_many, project.render_many):
            for bad in (None, (), {}, 'batches'):
                self.assert_error(api, bad, TypeError, 'batches must be a list')
            batches = [[row('Z')], [row(size=-1)], [None]]
            before = copy.deepcopy(batches)
            self.assert_error(api, batches, ValueError, 'negative size')
            self.assertEqual(batches, before)
            self.assert_error(api, [[row()], ()], TypeError, 'rows must be a list')
        batches = [[row('Z', size=3)], [row('A', size=2)]]
        self.assertEqual([r['bytes'] for r in project.run_many(batches)], [3, 2])
        self.assertEqual(project.render_many(batches), ''.join(project.render(r) for r in batches))

    def test_failure_does_not_mutate_inputs(self):
        for rows in ([row(' X '), row('x', size=2)], [row('../X')],
                     [row(size=-1)], [row(), {'nested': {'keep': []}}]):
            for api in (project.run, project.render, engine.compute, validation.validate):
                before = copy.deepcopy(rows)
                try:
                    api(rows)
                except ValueError:
                    pass
                self.assertEqual(rows, before)

    def test_all_facades_resolve_compute_at_call_time(self):
        original = engine.compute
        rows = [row()]
        for api, argument, count in ((project.run, rows, 1), (project.render, rows, 1),
                                     (project.run_many, [rows, rows], 2),
                                     (project.render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                self.assertTrue(all(call.args[0] is rows for call in compute.call_args_list))
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=original) as compute:
                self.assert_error(api, [[row(size=-1)], [None]], ValueError, 'negative size')
                self.assertEqual(compute.call_count, 1)


if __name__ == '__main__':
    unittest.main()
