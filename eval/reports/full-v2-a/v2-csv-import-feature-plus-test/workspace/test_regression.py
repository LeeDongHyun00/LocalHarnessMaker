import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': ' Z ', 'value': -4},
            {'id': 'second', 'target': ' B ', 'value': 0},
            {'id': 'third', 'target': 'a', 'value': -2},
            {'id': 'FIRST', 'target': 'b', 'value': 5},
            {'id': 'first', 'target': 'ignored', 'value': 1},
            {'id': 'first', 'target': 'B', 'value': 5},
        ]
        expected = {'columns': ['a', 'b'], 'data': [[-2], [5, 0]],
                    'ids': [['third'], ['first', 'second']]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)), ['columns', 'data', 'ids'])
        self.assertEqual(run_many([rows, []]), [expected, self.empty()])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    @staticmethod
    def empty() -> dict:
        return {'columns': [], 'data': [], 'ids': []}

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' Straße / X '), target=Text(' Ω / A  B '), value=10**200),
                     {'id': 'STRASSE / X', 'target': 'z', 'value': -1}])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / x', 'target': 'ω / a  b', 'value': 10**200},
            {'id': 'strasse / x', 'target': 'z', 'value': -1}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / X ')), 'strasse / x')
        expected = {'columns': ['ω / a  b'], 'data': [[10**200]], 'ids': [['strasse / x']]}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(render_many([rows]), render(rows))

    def test_invalid_rows_and_containers(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'x', 'target': 'a'},
                   {'id': 'x', 'target': 'a', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', ' \t', 1]), ('target', ['', '\n', None]),
                              ('value', [True, Integer(1), 1.0, '1'])]:
            for value in values:
                row = {'id': 'x', 'target': 'a', 'value': 1}
                row[field] = value
                invalid.append(row)
        for api in (validation.validate, engine.compute, run, render):
            for rows in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                        api(rows)
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                        api([row])
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^csv-import: batches must be a list$'):
                    api(batches)
            with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                api([None])

    def test_structural_errors_precede_ambiguity(self) -> None:
        ambiguous = [{'id': 'x', 'target': 'a', 'value': 1},
                     {'id': ' X ', 'target': 'b', 'value': 1}]
        self.assertEqual(len(validation.validate(ambiguous)), 2)
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                api(ambiguous + [{'id': 'bad'}])
            with self.assertRaisesRegex(ValueError, '^csv-import: ambiguous id$'):
                api(ambiguous + [{'id': 'x', 'target': 'c', 'value': 2}])

    def test_empty_and_json(self) -> None:
        self.assertEqual(run([]), self.empty())
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(render([]), '{"columns":[],"data":[],"ids":[]}\n')
        rows = [{'id': 'É / X', 'target': 'Ω', 'value': -1}]
        self.assertEqual(render(rows), '{"columns":["ω"],"data":[[-1]],"ids":[["é / x"]]}\n')

    def test_outputs_are_independent_and_inputs_unchanged(self) -> None:
        rows = [{'id': ' X ', 'target': ' A ', 'value': 0}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        for key in ('columns', 'data', 'ids'):
            self.assertIsNot(outputs[0][key], outputs[1][key])
        outputs[0]['columns'].append('new')
        outputs[0]['data'][0].append(9)
        outputs[0]['ids'][0].append('other')
        self.assertEqual(outputs[1], run(rows))
        self.assertEqual(rows, before)
        for api in (run_many, render_many):
            batches = [rows, [{'id': 'bad', 'nested': {'items': [1]}}]]
            original = copy.deepcopy(batches)
            with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                api(batches)
            self.assertEqual(batches, original)

    def test_compute_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'x', 'target': 'a', 'value': 1}]
        for api, argument, count in [(run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, []], 2),
                                     (render_many, [rows, []], 2)]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                self.assertIs(compute.call_args_list[0].args[0], rows)

    def test_batches_stop_at_first_failure(self) -> None:
        ambiguous = [{'id': 'x', 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': 'b', 'value': 1}]
        for api in (run_many, render_many):
            batches = [[], ambiguous, [{'invalid': True}]]
            original = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^csv-import: ambiguous id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[1].args[0], ambiguous)
            self.assertEqual(batches, original)


if __name__ == '__main__':
    unittest.main()
