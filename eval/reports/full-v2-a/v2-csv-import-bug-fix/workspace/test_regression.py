import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Straße ', 'target': ' Z/ONE ', 'value': 0},
            {'id': 'STRASSE', 'target': 'z/one', 'value': 0},
            {'id': ' Second ', 'target': ' A  B ', 'value': -7},
            {'id': 'Third', 'target': 'Z/ONE', 'value': 10**100},
        ]
        expected = {'columns': ['a  b', 'z/one'],
                    'data': [[-7], [0, 10**100]],
                    'ids': [['second'], ['strasse', 'third']]}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]),
                         [expected, {'columns': [], 'data': [], 'ids': []}])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(project.render(rows), encoded)
        self.assertEqual(project.render_many([rows, []]),
                         encoded + '{"columns":[],"data":[],"ids":[]}\n')
        self.assertEqual(list(project.run(rows)), ['columns', 'data', 'ids'])

    def test_validation_is_canonical_without_selection(self) -> None:
        rows = [{'id': ' Ä ', 'target': ' X/Y ', 'value': 1},
                {'id': 'ä', 'target': 'x/y', 'value': 2}]
        result = validation.validate(rows)
        self.assertEqual(result, [{'id': 'ä', 'target': 'x/y', 'value': 1},
                                  {'id': 'ä', 'target': 'x/y', 'value': 2}])
        self.assertIsNot(result[0], rows[0])
        self.assertEqual(policy.normalize('  Straße / A  B  '), 'strasse / a  b')
        with self.assertRaisesRegex(ValueError, '^csv-import: duplicate id$'):
            project.run(rows)

    def test_structural_errors_and_precedence(self) -> None:
        class Integer(int):
            pass

        valid = {'id': 'a', 'target': 'b', 'value': 1}
        invalid = [None, [], {}, dict(valid, extra=1), dict(valid, id=' '),
                   dict(valid, target=3), dict(valid, value=True),
                   dict(valid, value=Integer(1)), dict(valid, value=1.0)]
        for api in (project.run, project.render, engine.compute, validation.validate):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                    api(())
                for row in invalid:
                    rows = [valid, dict(valid, value=2), row]
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        self.assertEqual(project.run(Rows([Row(id=Text(' A '),
                                               target=Text(' B '), value=-1)])),
                         {'columns': ['b'], 'data': [[-1]], 'ids': [['a']]})

    def test_empty_and_unicode_rendering(self) -> None:
        self.assertEqual(project.run([]), {'columns': [], 'data': [], 'ids': []})
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        rows = [{'id': 'É', 'target': 'Ω', 'value': 0}]
        self.assertEqual(project.render(rows),
                         '{"columns":["ω"],"data":[[0]],"ids":[["é"]]}\n')

    def test_output_independence_and_input_preservation(self) -> None:
        rows = [{'id': ' A ', 'target': ' B ', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = project.run_many([rows, rows])
        expected = copy.deepcopy(outputs[1])
        outputs[0]['columns'].append('changed')
        outputs[0]['data'][0].append(2)
        outputs[0]['ids'][0].append('changed')
        self.assertEqual(outputs[1], expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(rows, before)

    def test_runtime_compute_delegation(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, count in (
            (project.run, rows, 1), (project.render, rows, 1),
            (project.run_many, [rows, rows], 2),
            (project.render_many, [rows, rows], 2),
        ):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, count)
                    for call in compute.call_args_list:
                        self.assertIs(call.args[0], rows)

    def test_batch_errors_are_atomic_and_ordered(self) -> None:
        valid = [{'id': 'a', 'target': 'b', 'value': 1}]
        duplicate = valid + [dict(valid[0], value=2)]
        for api in (project.run_many, project.render_many):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(TypeError, '^csv-import: batches must be a list$'):
                    api(())
                batches = [valid, duplicate, [None]]
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^csv-import: duplicate id$'):
                        api(batches)
                    self.assertEqual(compute.call_count, 2)
                self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
