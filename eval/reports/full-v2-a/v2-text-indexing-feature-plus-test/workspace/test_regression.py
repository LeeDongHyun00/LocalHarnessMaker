import copy
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': 'old', 'value': 1},
            {'id': 'second', 'target': ' TOKEN ', 'value': 0},
            {'id': 'FIRST', 'target': 'token', 'value': 4},
            {'id': 'first', 'target': 'ignored', 'value': 2},
            {'id': 'first', 'target': 'TOKEN', 'value': 4},
            {'id': 'third', 'target': 'alpha', 'value': 0},
        ]
        expected = {'index': {
            'alpha': {'count': 0, 'documents': ['third']},
            'token': {'count': 4, 'documents': ['first', 'second']},
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['index']), ['alpha', 'token'])
        self.assertEqual(list(run(rows)['index']['token']), ['count', 'documents'])
        self.assertEqual(run_many([rows, []]), [expected, {'index': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_serialization(self) -> None:
        rows = [{'id': ' Straße / A  B ', 'target': ' É / SS ', 'value': 10 ** 100}]
        canonical = [{'id': 'strasse / a  b', 'target': 'é / ss', 'value': 10 ** 100}]
        expected = {'index': {'é / ss': {
            'count': 10 ** 100, 'documents': ['strasse / a  b']}}}
        self.assertEqual(policy.normalize(' Straße / A  B '), 'strasse / a  b')
        self.assertEqual(validation.validate(rows), canonical)
        for result in (engine.compute(rows), run(rows), run_many([rows])[0]):
            self.assertEqual(result, expected)
        serialized = ('{"index":{"é / ss":{"count":' + str(10 ** 100)
                      + ',"documents":["strasse / a  b"]}}}\n')
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows]), serialized)

    def test_structural_validation_precedes_policy(self) -> None:
        invalid = {'id': 'bad', 'target': 'token', 'value': True}
        prefixes = [
            [{'id': 'a', 'target': 'token', 'value': -1}],
            [{'id': 'a', 'target': 'one', 'value': 1},
             {'id': 'A', 'target': 'two', 'value': 1}],
        ]
        for prefix in prefixes:
            rows = prefix + [invalid]
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(api=api.__name__, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                        api(rows)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                    api([rows])

    def test_validation_does_not_select_or_check_domain(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'ONE', 'value': -1},
            {'id': 'a', 'target': 'two', 'value': -1},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a', 'target': 'one', 'value': -1},
            {'id': 'a', 'target': 'two', 'value': -1},
        ])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])

    def test_ambiguity_is_not_erased_by_later_winner(self) -> None:
        rows = [
            {'id': 'a', 'target': 'one', 'value': 2},
            {'id': 'A', 'target': 'two', 'value': 2},
            {'id': 'a', 'target': 'three', 'value': 3},
        ]
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^text-indexing: ambiguous id$'):
                api(rows)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^text-indexing: ambiguous id$'):
                api([rows])

    def test_structural_types_and_exact_errors(self) -> None:
        class IntSubclass(int):
            pass

        invalid_rows = [None, [], {},
                        {'id': 'a', 'target': 'x', 'value': 1, 'extra': 1}]
        for field, values in (
            ('id', ['', ' \t', 1, None]),
            ('target', ['', '\n', False, None]),
            ('value', [True, IntSubclass(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'id': 'a', 'target': 'x', 'value': 1}
                row[field] = value
                invalid_rows.append(row)
        for row in invalid_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^text-indexing: invalid row$'):
                    run([row])
        for api in (validation.validate, engine.compute, run, render):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                    api(rows)

    def test_allowed_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' X '), value=0)])
        expected = {'index': {'x': {'count': 0, 'documents': ['a']}}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render_many(Rows([rows])), render(rows))

    def test_empty_and_outer_validation(self) -> None:
        self.assertEqual(run([]), {'index': {}})
        self.assertEqual(render([]), '{"index":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^text-indexing: batches must be a list$'):
                    api(batches)
            with self.assertRaisesRegex(TypeError, '^text-indexing: rows must be a list$'):
                api([()])

    def test_batch_failure_order_and_compute_delegation(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        negative = [{'id': 'b', 'target': 'x', 'value': -1}]
        malformed = [{'nested': {'values': [1, 2]}}]
        for api in (run_many, render_many):
            batches = [good, negative, malformed]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^text-indexing: negative count$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], negative)
            self.assertEqual(batches, before)

        for api, argument, count in (
            (run, good, 1), (render, good, 1),
            (run_many, [good, good, []], 3),
            (render_many, [good, good, []], 3),
        ):
            with patch.object(engine, 'compute', return_value={'observed': []}) as compute:
                result = api(argument)
                self.assertEqual(compute.call_count, count)
                if api is run:
                    self.assertEqual(result, {'observed': []})
                elif api is render:
                    self.assertEqual(result, '{"observed":[]}\n')
                elif api is run_many:
                    self.assertEqual(result, [{'observed': []}] * 3)
                else:
                    self.assertEqual(result, '{"observed":[]}\n' * 3)

    def test_outputs_and_inputs_are_independent(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        single = run(rows)
        canonical = validation.validate(rows)
        render_many([rows, rows])
        canonical[0]['id'] = 'changed'
        results[0]['index']['x']['documents'].append('changed')
        results[0]['index']['x']['count'] = 999
        results[0]['index']['new'] = {}
        self.assertEqual(rows, before)
        self.assertEqual(results[1], single)
        self.assertEqual(run(rows), single)
        empty = run_many([[], []])
        empty[0]['index']['changed'] = {}
        self.assertEqual(empty[1], {'index': {}})
        self.assertEqual(run([]), {'index': {}})


if __name__ == '__main__':
    unittest.main()
