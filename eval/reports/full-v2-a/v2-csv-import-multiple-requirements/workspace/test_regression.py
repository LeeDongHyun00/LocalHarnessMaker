import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'obsolete', 'value': 99},
            {'id': 'B', 'target': 'Z', 'value': 0},
            {'id': 'C', 'target': 'a', 'value': -3},
            {'id': 'a', 'target': 'z', 'value': -9},
        ]
        expected = {'columns': ['a', 'z'], 'data': [[-3], [-9, 0]],
                    'ids': [['c'], ['a', 'b']]}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]),
                         [expected, {'columns': [], 'data': [], 'ids': []}])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + project.render([]))

    def test_canonical_validation_and_large_integers(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Straße / X '), target=Text(' É / A  B '),
                         value=10 ** 100),
                     Row(id='STRASSE / X', target='final', value=-10 ** 100)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / x', 'target': 'é / a  b', 'value': 10 ** 100},
            {'id': 'strasse / x', 'target': 'final', 'value': -10 ** 100}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' É / A  B ')), 'é / a  b')
        expected = {'columns': ['final'], 'data': [[-10 ** 100]],
                    'ids': [['strasse / x']]}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(project.run(rows), expected)

    def test_structural_errors_and_precedence(self) -> None:
        class Integer(int):
            pass

        malformed = [None, [], {}, {'id': 'x', 'target': 'a', 'value': 1, 'extra': 2},
                     {'id': '', 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': ' \t', 'value': 1},
                     {'id': 1, 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': None, 'value': 1},
                     {'id': 'x', 'target': 'a', 'value': True},
                     {'id': 'x', 'target': 'a', 'value': Integer(1)},
                     {'id': 'x', 'target': 'a', 'value': 1.0}]
        for bad in malformed:
            rows = [{'id': 'x', 'target': 'a', 'value': 1},
                    {'id': 'x', 'target': 'b', 'value': 2}, bad]
            before = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, project.run, project.render):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in (validation.validate, engine.compute, project.run, project.render):
            for bad in (None, (), {}, iter([])):
                with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                    api(bad)

    def test_render_and_order(self) -> None:
        rows = [{'id': 'É / A', 'target': 'Ω', 'value': 0},
                {'id': 'b', 'target': 'a', 'value': -2}]
        result = project.run(rows)
        self.assertEqual(list(result), ['columns', 'data', 'ids'])
        rendered = project.render(rows)
        self.assertEqual(rendered, json.dumps(result, ensure_ascii=False,
                                             sort_keys=True, separators=(',', ':')) + '\n')
        self.assertIn('é / a', rendered)
        self.assertEqual(rendered.count('\n'), 1)

    def test_fresh_results_and_no_mutation(self) -> None:
        rows = [{'id': ' A ', 'target': ' Z ', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        expected = copy.deepcopy(outputs[1])
        outputs[0]['columns'].append('changed')
        outputs[0]['data'][0].append(2)
        outputs[0]['ids'][0].append('changed')
        self.assertEqual(outputs[1], expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(rows, before)
        empty = project.run_many([[], []])
        empty[0]['data'].append([1])
        self.assertEqual(empty[1], {'columns': [], 'data': [], 'ids': []})

    def test_batch_errors_and_call_time_dispatch(self) -> None:
        good = [{'id': 'x', 'target': 'a', 'value': 1}]
        bad = [{'id': 'x', 'target': 'a', 'value': False}]
        batches = [good, bad, good]
        before = copy.deepcopy(batches)
        original = engine.compute
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=original) as compute:
                with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, before)
            for invalid in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^csv-import: batches must be a list$'):
                    api(invalid)
            with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                api([None, bad])
        for api, arg, count in ((project.run, good, 1), (project.render, good, 1),
                                (project.run_many, [good, good], 2),
                                (project.render_many, [good, good], 2)):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(arg)
                self.assertEqual(compute.call_count, count)

    def test_empty_batches(self) -> None:
        self.assertEqual(project.run([]), {'columns': [], 'data': [], 'ids': []})
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')


if __name__ == '__main__':
    unittest.main()
