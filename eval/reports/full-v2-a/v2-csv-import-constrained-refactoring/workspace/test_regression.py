import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': ' Z/É ', 'value': 0},
            {'id': 'SECOND', 'target': ' A B ', 'value': -7},
            {'id': 'first', 'target': 'z/é', 'value': 0},
            {'id': 'Third', 'target': 'Z/É', 'value': 10**100},
        ]
        expected = {
            'columns': ['a b', 'z/é'],
            'data': [[-7], [0, 10**100]],
            'ids': [['second'], ['first', 'third']],
        }
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)), ['columns', 'data', 'ids'])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(run_many([rows, [], rows]), [expected, self.empty(), expected])
        self.assertEqual(render_many([rows, [], rows]), encoded + render([]) + encoded)
        self.assertEqual(rows, before)

    @staticmethod
    def empty() -> dict:
        return {'columns': [], 'data': [], 'ids': []}

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Straße/甲 '), target=Text(' X  Y '), value=-1)])
        canonical = [{'id': 'strasse/甲', 'target': 'x  y', 'value': -1}]
        self.assertEqual(policy.normalize(Text(' Straße/甲 ')), 'strasse/甲')
        self.assertEqual(validation.validate(rows), canonical)
        self.assertEqual(engine.compute(rows), run(rows))
        repeated = rows + rows
        result = validation.validate(repeated)
        self.assertEqual(result, canonical + canonical)
        self.assertIsNot(result[0], result[1])
        result[0]['id'] = 'changed'
        self.assertEqual(rows[0]['id'], ' Straße/甲 ')

    def test_structural_errors_take_precedence(self) -> None:
        class Integer(int):
            pass

        duplicate = [{'id': 'a', 'target': 'b', 'value': 1},
                     {'id': 'A', 'target': 'b', 'value': 2}]
        invalid = [None, {}, {'id': ' ', 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': '', 'value': 1},
                   {'id': 1, 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': None, 'value': 1},
                   {'id': 'a', 'target': 'b', 'value': True},
                   {'id': 'a', 'target': 'b', 'value': Integer(1)},
                   {'id': 'a', 'target': 'b', 'value': 1, 'extra': []}]
        for row in invalid:
            rows = duplicate + [row]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^csv-import: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        self.assertEqual(validation.validate(duplicate),
                         [{'id': 'a', 'target': 'b', 'value': 1},
                          {'id': 'a', 'target': 'b', 'value': 2}])
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^csv-import: duplicate id$'):
                api(duplicate)

    def test_container_errors_and_empty_results(self) -> None:
        for invalid in (None, (), {}, 'rows', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                    api(invalid)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^csv-import: batches must be a list$'):
                    api(invalid)
        self.assertEqual(run([]), self.empty())
        self.assertEqual(render([]), '{"columns":[],"data":[],"ids":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 0}]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        outputs = run_many(batches)
        for key in ('columns', 'data', 'ids'):
            if key == 'columns':
                outputs[0][key].append('changed')
            else:
                outputs[0][key][0].append('changed')
        self.assertEqual(outputs[1], run(rows))
        self.assertEqual(batches, before)
        empty_outputs = run_many([[], []])
        empty_outputs[0]['data'].append([])
        self.assertEqual(empty_outputs[1], self.empty())

    def test_facades_resolve_compute_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        empty = []
        for api, argument, calls in ((run, rows, [rows]), (render, rows, [rows]),
                                     (run_many, [rows, empty], [rows, empty]),
                                     (render_many, [rows, empty], [rows, empty])):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, len(calls))
                    for actual, expected in zip(compute.call_args_list, calls):
                        self.assertIs(actual.args[0], expected)

    def test_batches_stop_at_first_failure(self) -> None:
        good = [{'id': 'a', 'target': 'b', 'value': 1}]
        duplicate = good + [{'id': 'a', 'target': 'c', 'value': 1}]
        batches = [good, duplicate, [{'invalid': ['nested']}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^csv-import: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[1].args[0], duplicate)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^csv-import: rows must be a list$'):
                api([good, None])


if __name__ == '__main__':
    unittest.main()
