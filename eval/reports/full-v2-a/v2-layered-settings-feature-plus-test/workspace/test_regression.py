import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': 'old', 'value': -9},
            {'id': 'b', 'target': ' Theme ', 'value': -3},
            {'id': 'z', 'target': 'THEME', 'value': -2},
            {'id': 'A', 'target': 'theme', 'value': -2},
            {'id': 'z', 'target': 'ignored', 'value': -4},
            {'id': 'a', 'target': 'theme', 'value': -2},
            {'id': 'x', 'target': 'Alpha', 'value': -(10 ** 100)},
        ]
        expected = {'settings': {'alpha': 'x', 'theme': 'a'}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['settings']), ['alpha', 'theme'])
        self.assertEqual(run_many([rows, []]), [expected, {'settings': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_canonical_validation_preserves_encounter_order(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([
            Row(id=Text(' Straße / A  B '), target=Text(' É / C  D '), value=1),
            Row(id='STRASSE / A  B', target='elsewhere', value=2),
        ])
        expected = [
            {'id': 'strasse / a  b', 'target': 'é / c  d', 'value': 1},
            {'id': 'strasse / a  b', 'target': 'elsewhere', 'value': 2},
        ]
        self.assertEqual(validation.validate(rows), expected)
        self.assertEqual(policy.normalize(rows[0]['id']), expected[0]['id'])
        for api in (run, engine.compute):
            self.assertEqual(api(rows), {'settings': {'elsewhere': 'strasse / a  b'}})
        self.assertEqual(run_many([rows]), [run(rows)])
        self.assertEqual(render_many([rows]), render(rows))
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(validation.validate(rows), expected)

    def test_invalid_rows(self) -> None:
        class Integer(int):
            pass

        invalid = [
            None, [], {}, {'id': 'a', 'target': 'b'},
            {'id': 'a', 'target': 'b', 'value': 1, 'extra': {}},
            {'id': ' ', 'target': 'b', 'value': 1},
            {'id': 'a', 'target': '\t', 'value': 1},
            {'id': 1, 'target': 'b', 'value': 1},
            {'id': 'a', 'target': None, 'value': 1},
        ]
        invalid.extend({'id': 'a', 'target': 'b', 'value': value}
                       for value in (True, Integer(1), 1.0, '1', {}))
        for row in invalid:
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                        api([row])

    def test_container_types_and_empty_results(self) -> None:
        for value in (None, (), {}, 'rows', iter([])):
            for api in (validation.validate, engine.compute, run, render):
                with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^layered-settings: batches must be a list$'):
                    api(value)
        self.assertEqual(run([]), {'settings': {}})
        self.assertEqual(render([]), '{"settings":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_structural_errors_precede_ambiguity(self) -> None:
        rows = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': ' A ', 'target': 'y', 'value': 1},
            {'id': 'a', 'target': 'z', 'value': 2},
        ]
        self.assertEqual(len(validation.validate(rows)), 3)
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^layered-settings: ambiguous id$'):
                api(rows)
            with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                api(rows + [{'unexpected': {'nested': []}}])

    def test_duplicate_position_and_priority(self) -> None:
        rows = [
            {'id': 'z', 'target': 'old', 'value': 1},
            {'id': 'a', 'target': 'x', 'value': 3},
            {'id': 'z', 'target': 'x', 'value': 3},
            {'id': 'a', 'target': 'ignored', 'value': 2},
        ]
        from project import domain
        with patch.object(engine, 'resolve', wraps=domain.resolve) as resolve:
            self.assertEqual(run(rows), {'settings': {'x': 'a'}})
        self.assertEqual([row['id'] for row in resolve.call_args.args[0]], ['z', 'a'])
        rows.append({'id': 'huge', 'target': 'x', 'value': 10 ** 100})
        self.assertEqual(run(rows), {'settings': {'x': 'huge'}})

    def test_unicode_rendering(self) -> None:
        rows = [
            {'id': ' Straße ', 'target': ' É / A  B ', 'value': 1},
            {'id': '雪', 'target': 'alpha', 'value': 2},
        ]
        expected = '{"settings":{"alpha":"雪","é / a  b":"strasse"}}\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(json.loads(render(rows)), run(rows))
        self.assertEqual(render_many([rows, rows]), expected * 2)

    def test_fresh_results_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows]
        original = copy.deepcopy(batches)
        results = run_many(batches)
        results[0]['settings']['x'] = 'changed'
        self.assertEqual(results[1], {'settings': {'x': 'a'}})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(batches, original)
        empty = run_many([[], []])
        empty[0]['settings']['new'] = 'value'
        self.assertEqual(empty[1], {'settings': {}})
        bad = rows + [{'nested': {'items': []}}]
        batches = [rows, bad, rows]
        original = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                api(batches)
            self.assertEqual(batches, original)

    def test_compute_is_resolved_at_call_time(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 1}]
        second = [{'id': 'b', 'target': 'y', 'value': 2}]
        for api, argument, expected in (
            (run, first, [first]), (render, first, [first]),
            (run_many, [first, second], [first, second]),
            (render_many, [first, second], [first, second]),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
            self.assertEqual(compute.call_count, len(expected))
            for call, rows in zip(compute.call_args_list, expected):
                self.assertIs(call.args[0], rows)

    def test_batch_stops_at_first_failure(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        ambiguous = good + [{'id': 'a', 'target': 'y', 'value': 1}]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^layered-settings: ambiguous id$'):
                    api([good, ambiguous, None])
            self.assertEqual(compute.call_count, 2)
            self.assertIs(compute.call_args_list[-1].args[0], ambiguous)
            error = RuntimeError('instrumented failure')
            with patch.object(engine, 'compute', side_effect=error) as compute:
                with self.assertRaises(RuntimeError) as caught:
                    api([good, None])
            self.assertIs(caught.exception, error)
            self.assertEqual(compute.call_count, 1)


if __name__ == '__main__':
    unittest.main()
