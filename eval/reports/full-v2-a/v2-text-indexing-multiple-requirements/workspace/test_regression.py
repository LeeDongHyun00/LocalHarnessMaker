import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'obsolete', 'value': -9},
            {'id': 'B', 'target': ' STRASSE / 水 ', 'value': 4},
            {'id': 'a', 'target': 'Straße / 水', 'value': 0},
            {'id': 'C', 'target': 'z', 'value': 20},
            {'id': 'c', 'target': 'Straße / 水', 'value': 2},
        ]
        expected = {'index': {'strasse / 水': {
            'count': 6, 'documents': ['a', 'b', 'c']}}}
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'index': {}}])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, []]), encoded + '{"index":{}}\n')
        self.assertEqual(rows, before)

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([
            Row(id=Text(' A '), target=Text(' Straße / 水  X '), value=-1),
            Row(id='a', target='other', value=10 ** 100),
        ])
        expected = [
            {'id': 'a', 'target': 'strasse / 水  x', 'value': -1},
            {'id': 'a', 'target': 'other', 'value': 10 ** 100},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / 水  X ')),
                         'strasse / 水  x')
        self.assertEqual(engine.compute(rows), {
            'index': {'other': {'count': 10 ** 100, 'documents': ['a']}}})

    def test_structural_errors_precede_domain_errors(self) -> None:
        class Count(int):
            pass

        invalid_rows = [
            None, [], {}, {'id': 'a', 'target': 'b'},
            {'id': 'a', 'target': 'b', 'value': 1, 'extra': 2},
            {'id': ' ', 'target': 'b', 'value': 1},
            {'id': 'a', 'target': '\t', 'value': 1},
            {'id': 1, 'target': 'b', 'value': 1},
            {'id': 'a', 'target': None, 'value': 1},
            {'id': 'a', 'target': 'b', 'value': True},
            {'id': 'a', 'target': 'b', 'value': Count(1)},
            {'id': 'a', 'target': 'b', 'value': 1.0},
        ]
        for bad in invalid_rows:
            rows = [{'id': 'a', 'target': 'b', 'value': -1},
                    {'id': 'a', 'target': 'c', 'value': -2}, bad]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(api=api.__name__, bad=bad):
                    with self.assertRaisesRegex(
                            ValueError, '^text-indexing: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_errors_empty_inputs_and_batch_order(self) -> None:
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(
                        TypeError, '^text-indexing: rows must be a list$'):
                    api(rows)
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(
                        TypeError, '^text-indexing: batches must be a list$'):
                    api(batches)
            batches = [[{'id': 'a', 'target': 'b', 'value': -1}], [None]]
            before = copy.deepcopy(batches)
            with self.assertRaisesRegex(
                    ValueError, '^text-indexing: negative count$'):
                api(batches)
            self.assertEqual(batches, before)
        self.assertEqual(run([]), {'index': {}})
        self.assertEqual(render([]), '{"index":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_output_order_and_independence(self) -> None:
        rows = [{'id': 'z', 'target': 'z', 'value': 1},
                {'id': 'b', 'target': 'a', 'value': 0},
                {'id': 'a', 'target': 'a', 'value': 2}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        pristine = copy.deepcopy(results[1])
        self.assertEqual(list(results[0]), ['index'])
        self.assertEqual(list(results[0]['index']), ['a', 'z'])
        self.assertEqual(list(results[0]['index']['a']), ['count', 'documents'])
        self.assertEqual(results[0]['index']['a']['documents'], ['b', 'a'])
        results[0]['index']['a']['documents'].append('changed')
        results[0]['index']['z']['count'] = 999
        results[0]['index']['new'] = {}
        self.assertEqual(results[1], pristine)
        self.assertEqual(run(rows), pristine)
        self.assertEqual(rows, before)

    def test_facades_resolve_compute_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, expected_calls in (
                (run, rows, [rows]), (render, rows, [rows]),
                (run_many, [rows, []], [rows, []]),
                (render_many, [rows, []], [rows, []])):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as spy:
                    api(argument)
                    self.assertEqual(spy.call_count, len(expected_calls))
                    self.assertEqual([call.args[0] for call in spy.call_args_list],
                                     expected_calls)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as spy:
                with self.assertRaisesRegex(ValueError, 'negative count'):
                    api([rows, [{'id': 'b', 'target': 'c', 'value': -1}], []])
                self.assertEqual(spy.call_count, 2)


if __name__ == '__main__':
    unittest.main()
