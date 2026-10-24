import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Low ', 'target': ' Straße/A B ', 'value': 2},
            {'id': 'HIGH', 'target': 'STRASSE/A B', 'value': 10**100},
            {'id': 'low', 'target': 'strasse/a b', 'value': 2},
            {'id': 'Other', 'target': ' Alpha ', 'value': 0},
        ]
        expected = {
            'patches': {'alpha': ['other'], 'strasse/a b': ['high', 'low']},
            'offsets': {'alpha': [0], 'strasse/a b': [10**100, 2]},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['patches']), ['alpha', 'strasse/a b'])
        self.assertEqual(run_many([rows, []]), [expected, {'patches': {}, 'offsets': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_validation_is_canonical_without_domain_checks(self) -> None:
        rows = [
            {'id': ' X ', 'target': ' DOC ', 'value': -1},
            {'id': 'x', 'target': 'doc', 'value': 2},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'x', 'target': 'doc', 'value': -1},
            {'id': 'x', 'target': 'doc', 'value': 2},
        ])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize('  Straße / A  B  '), 'strasse / a  b')

    def test_structural_errors_and_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        self.assertEqual(run(Rows([Row(id=Text(' X '), target=Text(' D '), value=0)])),
                         {'patches': {'d': ['x']}, 'offsets': {'d': [0]}})
        for value in (True, Integer(1), 1.0, '1', None):
            with self.subTest(value=value):
                self.assert_error([{'id': 'x', 'target': 'd', 'value': value}],
                                  ValueError, 'invalid row')
        for row in (None, [], {}, {'id': 'x', 'target': 'd', 'value': 1, 'extra': 2},
                    {'id': ' ', 'target': 'd', 'value': 1},
                    {'id': 'x', 'target': 3, 'value': 1}):
            self.assert_error([row], ValueError, 'invalid row')
        for rows in (None, (), {}, 'rows'):
            self.assert_error(rows, TypeError, 'rows must be a list')

    def assert_error(self, rows, kind, message) -> None:
        before = copy.deepcopy(rows)
        for api in (validation.validate, engine.compute, run, render):
            with self.subTest(api=api.__name__):
                with self.assertRaises(kind) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'document-patches: ' + message)
                self.assertEqual(rows, before)

    def test_error_precedence(self) -> None:
        first = {'id': 'x', 'target': 'doc', 'value': 0}
        duplicate = {'id': ' X ', 'target': 'doc', 'value': 1}
        collision = {'id': 'y', 'target': 'DOC', 'value': 0}
        negative = {'id': 'z', 'target': 'doc', 'value': -1}
        for prefix in ([first, duplicate], [negative], [first, collision]):
            self.assert_error(prefix + [{}], ValueError, 'invalid row')
        for rows, message in (([first, duplicate], 'duplicate id'),
                              ([first, collision, negative], 'negative offset'),
                              ([first, collision], 'collision')):
            for api in (engine.compute, run, render):
                with self.assertRaises(ValueError) as caught:
                    api(rows)
                self.assertEqual(str(caught.exception), 'document-patches: ' + message)

    def test_render_and_empty(self) -> None:
        rows = [{'id': 'É', 'target': '文', 'value': 0}]
        self.assertEqual(render(rows), '{"offsets":{"文":[0]},"patches":{"文":["é"]}}\n')
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(run([]), {'patches': {}, 'offsets': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' X ', 'target': ' D ', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['patches']['d'].append('changed')
        outputs[0]['offsets']['d'].append(99)
        self.assertEqual(outputs[1], run(rows))
        outputs[0]['patches']['new'] = []
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)

    def test_batch_errors_are_atomic_and_ordered(self) -> None:
        batches = [[{'id': 'x', 'target': 'd', 'value': -1}], [{}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception), 'document-patches: negative offset')
                self.assertEqual(compute.call_count, 1)
            with self.assertRaises(TypeError) as caught:
                api(())
            self.assertEqual(str(caught.exception), 'document-patches: batches must be a list')
        self.assertEqual(batches, before)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaises(ValueError):
                    api([[], [{}]])
                self.assertEqual(compute.call_count, 2)

    def test_engine_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'x', 'target': 'd', 'value': 0}]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)


if __name__ == '__main__':
    unittest.main()
