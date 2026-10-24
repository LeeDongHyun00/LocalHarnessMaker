import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': ' Straße/A B ', 'value': 0},
            {'id': 'FIRST', 'target': 'STRASSE/A B', 'value': 0},
            {'id': 'Second', 'target': 'strasse/a b', 'value': 10**100},
            {'id': 'Third', 'target': ' Alpha ', 'value': 2},
        ]
        expected = {'index': {
            'alpha': {'count': 2, 'documents': ['third']},
            'strasse/a b': {'count': 10**100, 'documents': ['first', 'second']},
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['index']), ['alpha', 'strasse/a b'])
        self.assertEqual(list(run(rows)['index']['alpha']), ['count', 'documents'])
        self.assertEqual(run_many([rows, []]), [expected, {'index': {}}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"index":{}}\n')

    def test_validation_only_canonicalizes(self) -> None:
        rows = [{'id': ' X ', 'target': ' É/ A ', 'value': -1},
                {'id': 'x', 'target': 'other', 'value': 2}]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'x', 'target': 'é/ a', 'value': -1},
            {'id': 'x', 'target': 'other', 'value': 2},
        ])
        self.assertEqual(policy.normalize(' É/ A '), 'é/ a')
        canonical[0]['value'] = 99
        self.assertEqual(rows, before)

    def test_structural_types(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        valid = ListSubclass([DictSubclass(id=StringSubclass(' A '),
                                         target=StringSubclass(' B '), value=1)])
        self.assertEqual(run(valid), {'index': {'b': {'count': 1, 'documents': ['a']}}})
        malformed = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, IntSubclass(1), 1.0, '1'])]:
            for value in values:
                row = {'id': 'a', 'target': 'b', 'value': 1}
                row[field] = value
                malformed.append(row)
        for row in malformed:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                        api([row])
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                    api(rows)

    def test_error_precedence_and_no_mutation(self) -> None:
        a = {'id': ' A ', 'target': ' B ', 'value': -1}
        conflict = {'id': 'a', 'target': 'c', 'value': 2}
        invalid = {'id': 'x', 'target': 'y', 'value': {'nested': []}}
        cases = [([a, conflict, invalid], 'invalid row'),
                 ([a, invalid], 'invalid row'),
                 ([a, conflict], 'duplicate id'),
                 ([a, dict(a)], 'negative count')]
        for rows, error in cases:
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^text-indexing: ' + error + '$'):
                    api(rows)
                self.assertEqual(rows, before)

    def test_unicode_render(self) -> None:
        rows = [{'id': ' 문서 ', 'target': ' 토큰/é A ', 'value': 0}]
        self.assertEqual(render(rows),
                         '{"index":{"토큰/é a":{"count":0,"documents":["문서"]}}}\n')

    def test_empty_and_batch_types(self) -> None:
        self.assertEqual(run([]), {'index': {}})
        self.assertEqual(render([]), '{"index":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^text-indexing: batches must be a list$'):
                    api(batches)

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': ' A ', 'target': ' B ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        later = run(rows)
        results[0]['index']['b']['documents'].append('changed')
        results[0]['index']['b']['count'] = 9
        self.assertEqual(results[1], later)
        results[1]['index'].clear()
        self.assertEqual(run(rows), later)
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['index']['new'] = {}
        self.assertEqual(empty[1], {'index': {}})

    def test_runtime_compute_lookup(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, expected_calls in ((run, rows, [rows]),
                                               (render, rows, [rows]),
                                               (run_many, [rows, []], [rows, []]),
                                               (render_many, [rows, []], [rows, []])):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', return_value={'sentinel': 'é'}) as compute:
                    result = api(argument)
                    self.assertEqual(compute.call_args_list,
                                     [unittest.mock.call(member) for member in expected_calls])
                    if api is run:
                        self.assertEqual(result, {'sentinel': 'é'})
                    elif api is render:
                        self.assertEqual(result, '{"sentinel":"é"}\n')
                    elif api is run_many:
                        self.assertEqual(result, [{'sentinel': 'é'}, {'sentinel': 'é'}])
                    else:
                        self.assertEqual(result, '{"sentinel":"é"}\n' * 2)

    def test_batch_first_failure_is_atomic(self) -> None:
        valid = [{'id': 'a', 'target': 'b', 'value': 1}]
        negative = [{'id': 'x', 'target': 'y', 'value': -1}]
        invalid = [{'nested': {'items': []}}]
        for api in (run_many, render_many):
            for batches, message, count in (([valid, negative, invalid], 'negative count', 2),
                                             ([negative, invalid], 'negative count', 1)):
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^text-indexing: ' + message + '$'):
                        api(batches)
                    self.assertEqual(compute.call_count, count)
                self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                api([valid, None])


if __name__ == '__main__':
    unittest.main()
