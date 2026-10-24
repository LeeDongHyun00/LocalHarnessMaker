import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Child ', 'target': ' STRASSE ', 'value': 3},
            {'id': ' Straße ', 'target': 'straße', 'value': 1},
            {'id': 'STRASSE', 'target': ' STRASSE ', 'value': 1},
            {'id': 'Other', 'target': 'other', 'value': 3},
        ]
        expected = {'migrations': ['strasse', 'child', 'other']}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'migrations': []}])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + '{"migrations":[]}\n')

    def test_structure_and_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        valid = Rows([Row(id=Text(' A / B '), target=Text(' a / b '), value=10**100)])
        self.assertEqual(project.run(valid), {'migrations': ['a / b']})
        for value in (True, Integer(1), 1.0, '1', None, {'nested': []}):
            with self.subTest(value=value):
                self.assert_error_all([{'id': 'a', 'target': 'a', 'value': value}],
                                      ValueError, 'invalid row')
        for row in ({}, {'id': 'a', 'target': 'a', 'value': 1, 'extra': 2},
                    {'id': '', 'target': 'a', 'value': 1},
                    {'id': 'a', 'target': ' \t', 'value': 1},
                    {'id': 1, 'target': 'a', 'value': 1}, []):
            with self.subTest(row=row):
                self.assert_error_all([row], ValueError, 'invalid row')
        for rows in (None, (), {}, 'rows'):
            self.assert_error_all(rows, TypeError, 'rows must be a list')

    def assert_error_all(self, rows, exception, message) -> None:
        original = copy.deepcopy(rows)
        calls = (project.run, project.render, engine.compute, 
                 lambda data: project.run_many([data]),
                 lambda data: project.render_many([data]))
        for call in calls:
            with self.assertRaisesRegex(exception, '^schema-migration: ' + message + '$'):
                call(rows)
            self.assertEqual(rows, original)

    def test_structural_errors_precede_selection_and_domain(self) -> None:
        for first in (
            [{'id': 'a', 'target': 'a', 'value': 1},
             {'id': 'A', 'target': 'a', 'value': 2}],
            [{'id': 'a', 'target': 'missing', 'value': 0}],
        ):
            self.assert_error_all(first + [{'id': 'broken'}], ValueError, 'invalid row')

    def test_domain_error_precedence(self) -> None:
        self.assert_error_all([
            {'id': 'A', 'target': 'a', 'value': 0},
            {'id': 'a', 'target': 'a', 'value': 1},
        ], ValueError, 'duplicate id')
        self.assert_error_all([
            {'id': 'a', 'target': 'missing', 'value': 0},
        ], ValueError, 'invalid version')
        self.assert_error_all([
            {'id': 'a', 'target': 'a', 'value': 2},
            {'id': 'b', 'target': 'a', 'value': 1},
            {'id': 'c', 'target': 'missing', 'value': 1},
        ], ValueError, 'missing predecessor')
        for version in (1, 2):
            self.assert_error_all([
                {'id': 'a', 'target': 'a', 'value': 2},
                {'id': 'b', 'target': 'a', 'value': version},
            ], ValueError, 'version order')

    def test_validation_only_canonicalizes(self) -> None:
        rows = [
            {'value': -1, 'target': ' Missing / É ', 'id': ' STRASSE '},
            {'id': 'straße', 'target': 'Other', 'value': 0},
        ]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse', 'target': 'missing / é', 'value': -1},
            {'id': 'strasse', 'target': 'other', 'value': 0},
        ])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(policy.normalize('  STRAßE / É  X  '), 'strasse / é  x')

    def test_empty_and_fresh_outputs(self) -> None:
        self.assertEqual(project.run([]), {'migrations': []})
        self.assertEqual(project.render([]), '{"migrations":[]}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        rows = [{'id': 'a', 'target': 'a', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        outputs[0]['migrations'].append('changed')
        self.assertEqual(outputs[1], {'migrations': ['a']})
        self.assertEqual(project.run(rows), outputs[1])
        self.assertEqual(rows, before)
        self.assertEqual(list(outputs[1]), ['migrations'])

    def test_serialization(self) -> None:
        rows = [{'id': ' É / A  B ', 'target': 'é / a  b', 'value': 1}]
        self.assertEqual(project.render(rows), '{"migrations":["é / a  b"]}\n')
        nested = {'z': [{'z': 1, 'a': {'é': 2, 'b': 3}}], 'a': []}
        with patch.object(engine, 'compute', return_value=nested) as compute:
            self.assertEqual(project.render([]),
                             json.dumps(nested, ensure_ascii=False, sort_keys=True,
                                        separators=(',', ':')) + '\n')
            compute.assert_called_once_with([])

    def test_runtime_compute_dispatch(self) -> None:
        rows = [{'id': 'a', 'target': 'a', 'value': 1}]
        for api, argument, count in (
            (project.run, rows, 1), (project.render, rows, 1),
            (project.run_many, [rows, rows], 2),
            (project.render_many, [rows, rows], 2),
        ):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, count)
                    self.assertTrue(all(call.args[0] is rows for call in compute.call_args_list))

    def test_batch_atomicity_and_first_failure(self) -> None:
        valid = [{'id': 'a', 'target': 'a', 'value': 1}]
        invalid = [{'id': 'b', 'target': 'missing', 'value': 1}]
        batches = [valid, invalid, [{'invalid': {'nested': []}}]]
        before = copy.deepcopy(batches)
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^schema-migration: missing predecessor$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)
            for outer in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^schema-migration: batches must be a list$'):
                    api(outer)


if __name__ == '__main__':
    unittest.main()
