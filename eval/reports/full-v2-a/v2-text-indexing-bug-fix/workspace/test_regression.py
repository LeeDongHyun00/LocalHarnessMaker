import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B ', 'target': ' STRASSE/猫 ', 'value': 0},
            {'id': 'b', 'target': 'straße/猫', 'value': 0},
            {'id': ' A ', 'target': 'Straße/猫', 'value': 7},
            {'id': 'C', 'target': ' A  B ', 'value': 2},
        ]
        expected = {'index': {
            'a  b': {'count': 2, 'documents': ['c']},
            'strasse/猫': {'count': 7, 'documents': ['b', 'a']},
        }}
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['index']), ['a  b', 'strasse/猫'])
        self.assertEqual(list(run(rows)['index']['a  b']), ['count', 'documents'])
        self.assertEqual(rows, before)
        self.assertEqual(policy.normalize(' STRAẞE / 猫 '), 'strasse / 猫')

    def test_batch_and_render(self) -> None:
        rows = [{'id': ' É ', 'target': ' 猫 ', 'value': 0}]
        expected = {'index': {'猫': {'count': 0, 'documents': ['é']}}}
        serialized = '{"index":{"猫":{"count":0,"documents":["é"]}}}\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(run_many([rows, [], rows]), [expected, {'index': {}}, expected])
        self.assertEqual(render_many([rows, [], rows]), serialized + '{"index":{}}\n' + serialized)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_validation_without_selection_or_domain(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' T ', 'value': -1},
            {'id': 'a', 'target': 'Other', 'value': 2},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a', 'target': 't', 'value': -1},
            {'id': 'a', 'target': 'other', 'value': 2},
        ])
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows[0]['target'], ' T ')

    def test_structural_errors_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, [], {}, {'id': 'a', 'target': 't', 'value': 1, 'extra': {}},
                     {'id': ' ', 'target': 't', 'value': 1},
                     {'id': 'a', 'target': '\t', 'value': 1},
                     {'id': 1, 'target': 't', 'value': 1},
                     {'id': 'a', 'target': None, 'value': 1},
                     {'id': 'a', 'target': 't', 'value': True},
                     {'id': 'a', 'target': 't', 'value': IntSubclass(1)}]
        prefixes = [[], [{'id': 'a', 'target': 't', 'value': -1}],
                    [{'id': 'a', 'target': 't', 'value': 1},
                     {'id': 'A', 'target': 'u', 'value': 1}]]
        for bad in malformed:
            for prefix in prefixes:
                rows = prefix + [bad]
                before = copy.deepcopy(rows)
                for api in (run, render, engine.compute, validation.validate):
                    with self.subTest(bad=bad, api=api.__name__):
                        with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                            api(rows)
                        self.assertEqual(rows, before)

    def test_duplicate_and_negative_errors(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 't', 'value': -1}], 'negative count'),
            ([{'id': 'a', 'target': 't', 'value': 1},
              {'id': ' A ', 'target': 't', 'value': 2}], 'duplicate id'),
        ]
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^text-indexing: ' + message + '$'):
                    api(rows)
                self.assertEqual(rows, before)

    def test_container_types_and_large_counts(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' T '), value=10 ** 100)])
        self.assertEqual(run(rows), {'index': {'t': {'count': 10 ** 100, 'documents': ['a']}}})
        for bad in (None, (), {}, 'rows', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                    api(bad)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^text-indexing: batches must be a list$'):
                    api(bad)

    def test_output_independence(self) -> None:
        rows = [{'id': 'a', 'target': 't', 'value': 0}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['index']['t']['documents'].append('changed')
        results[0]['index']['t']['count'] = 99
        expected = {'index': {'t': {'count': 0, 'documents': ['a']}}}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['index']['changed'] = {}
        self.assertEqual(empty[1], {'index': {}})

    def test_shared_compute_path(self) -> None:
        rows = [{'id': 'a', 'target': 't', 'value': 1}]
        for api, argument, calls in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, calls)
                for call in compute.call_args_list:
                    self.assertIs(call.args[0], rows)

    def test_batch_failure_order_and_atomicity(self) -> None:
        good = [{'id': 'a', 'target': 't', 'value': 1}]
        negative = [{'id': 'b', 'target': 't', 'value': -1}]
        invalid = [{'id': 'c', 'target': 't', 'value': 1, 'nested': {'items': []}}]
        batches = [good, negative, invalid]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^text-indexing: negative count$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], negative)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
