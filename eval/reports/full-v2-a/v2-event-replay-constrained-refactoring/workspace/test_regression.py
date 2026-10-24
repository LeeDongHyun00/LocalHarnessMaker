import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Straße / X ', 'value': 5},
            {'id': 'a', 'target': 'STRASSE / X', 'value': 5},
            {'id': 'B', 'target': 'strasse / x', 'value': -5},
            {'id': 'C', 'target': ' Alpha ', 'value': 2},
        ]
        expected = {'balances': {'alpha': 2, 'strasse / x': 0},
                    'history': [5, 0, 2]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['alpha', 'strasse / x'])
        self.assertEqual(run_many([rows, []]), [expected, {'balances': {}, 'history': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_structural_errors_take_precedence(self) -> None:
        invalid = {'id': 'later', 'target': 'x', 'value': True}
        for earlier in (
            [{'id': 'a', 'target': 'x', 'value': -1}],
            [{'id': 'a', 'target': 'x', 'value': 1},
             {'id': 'A', 'target': 'x', 'value': 2}],
        ):
            rows = earlier + [invalid]
            before = copy.deepcopy(rows)
            for call in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                    call(rows)
            self.assertEqual(rows, before)

    def test_duplicate_and_prefix_errors(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 'x', 'value': 1},
              {'id': ' A ', 'target': 'y', 'value': 1}], 'duplicate id'),
            ([{'id': 'a', 'target': 'x', 'value': -1},
              {'id': 'b', 'target': 'x', 'value': 2}], 'negative prefix'),
        ]
        for rows, message in cases:
            for call in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^event-replay: ' + message + '$'):
                    call(rows)

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(id=Text(' A / B '), target=Text(' É  X '), value=10 ** 100)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'a / b', 'target': 'é  x', 'value': 10 ** 100}])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / É  X ')), 'strasse / é  x')
        self.assertEqual(run(rows)['history'], [10 ** 100])
        for bad in (None, (), {}, 'rows'):
            for call in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                    call(bad)
        malformed = [None, [], {}, {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0}]
        for field, values in (('id', ['', '  ', 1]), ('target', ['', '\t', None]),
                              ('value', [True, Integer(1), 1.0, '1'])):
            for value in values:
                row = {'id': 'a', 'target': 'x', 'value': 1}
                row[field] = value
                malformed.append(row)
        for row in malformed:
            with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                validation.validate([row])
        # Validation canonicalizes all rows without selection or replay.
        raw = [{'id': 'A', 'target': 'X', 'value': -1},
               {'id': 'a', 'target': 'x', 'value': 2}]
        self.assertEqual(len(validation.validate(raw)), 2)

    def test_serialization_and_empty_results(self) -> None:
        rows = [{'id': 'é', 'target': ' É / X ', 'value': 1}]
        self.assertEqual(render(rows), '{"balances":{"é / x":1},"history":[1]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                                sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'balances': {}, 'history': []})
        self.assertEqual(render([]), '{"balances":{},"history":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_results_and_inputs_are_independent(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['balances']['x'] = 99
        results[0]['history'].append(99)
        self.assertEqual(results[1], {'balances': {'x': 1}, 'history': [1]})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        nested = [{'id': 'bad', 'target': 'x', 'value': {'nested': [1]}}]
        batches = [rows, nested]
        before = copy.deepcopy(batches)
        for call in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                call(batches)
            self.assertEqual(batches, before)

    def test_compute_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        for call, argument, count in ((run, rows, 1), (render, rows, 1),
                                      (run_many, [rows, []], 2),
                                      (render_many, [rows, []], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as observed:
                call(argument)
                self.assertEqual(observed.call_count, count)
                self.assertIs(observed.call_args_list[0].args[0], rows)

    def test_batches_stop_at_first_failure(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        negative = [{'id': 'b', 'target': 'x', 'value': -1}]
        for call in (run_many, render_many):
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^event-replay: batches must be a list$'):
                    call(bad)
            with patch.object(engine, 'compute', wraps=engine.compute) as observed:
                with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                    call([good, negative, None])
                self.assertEqual(observed.call_count, 2)


if __name__ == '__main__':
    unittest.main()
