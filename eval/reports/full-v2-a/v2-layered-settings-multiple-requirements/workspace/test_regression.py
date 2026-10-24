import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': 'Old', 'value': 100},
            {'id': 'b', 'target': 'NEW', 'value': -4},
            {'id': 'A', 'target': 'new', 'value': -4},
            {'id': 'z', 'target': ' New ', 'value': -9},
        ]
        expected = {'settings': {'new': 'a'}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'settings': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_highest_priority_and_unbounded_integers(self) -> None:
        self.assertEqual(run([
            {'id': 'low', 'target': 'x', 'value': -100},
            {'id': 'high', 'target': 'x', 'value': -2},
            {'id': 'huge', 'target': 'y', 'value': 10 ** 500},
        ]), {'settings': {'x': 'high', 'y': 'huge'}})

    def test_validation_preserves_all_revisions(self) -> None:
        rows = [
            {'id': ' B ', 'target': ' Z ', 'value': 4},
            {'id': 'A', 'target': 'Y', 'value': 2},
            {'id': 'b', 'target': 'X', 'value': 1},
        ]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'b', 'target': 'z', 'value': 4},
            {'id': 'a', 'target': 'y', 'value': 2},
            {'id': 'b', 'target': 'x', 'value': 1},
        ])
        self.assertTrue(all(a is not b for a, b in zip(rows, canonical)))
        with patch.object(engine, 'resolve', return_value={}) as resolve:
            engine.compute(rows)
        self.assertEqual(resolve.call_args.args[0], [canonical[2], canonical[1]])

    def test_normalization_and_recursive_order(self) -> None:
        rows = [
            {'id': ' STRAẞE / A ', 'target': ' É / Two  Words ', 'value': 1},
            {'id': 'Z', 'target': ' A ', 'value': 1},
        ]
        expected = {'settings': {'a': 'z', 'é / two  words': 'strasse / a'}}
        self.assertEqual(policy.normalize(' É / Two  Words '), 'é / two  words')
        self.assertEqual(validation.validate(rows)[0]['id'], 'strasse / a')
        for api in (run, engine.compute):
            result = api(rows)
            self.assertEqual(result, expected)
            self.assertEqual(list(result['settings']), ['a', 'é / two  words'])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(run_many([rows]), [expected])
        self.assertEqual(render_many([rows]), serialized)

    def test_structure_and_error_precedence(self) -> None:
        class Integer(int):
            pass

        invalid = [None, {}, {'id': 'x', 'target': 'y', 'value': 1, 'extra': 2},
                   {'id': ' ', 'target': 'y', 'value': 1},
                   {'id': 'x', 'target': '\t', 'value': 1},
                   {'id': 1, 'target': 'y', 'value': 1},
                   {'id': 'x', 'target': 'y', 'value': True},
                   {'id': 'x', 'target': 'y', 'value': Integer(1)}]
        for row in invalid:
            rows = [{'id': 'x', 'target': 'a', 'value': 1},
                    {'id': 'x', 'target': 'b', 'value': 2}, row]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                api(())

    def test_container_and_string_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' B '), value=1)])
        self.assertEqual(run(rows), {'settings': {'b': 'a'}})
        self.assertEqual(run_many(Rows([rows])), [{'settings': {'b': 'a'}}])

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' B ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['settings']['b'] = 'changed'
        self.assertEqual(results[1], {'settings': {'b': 'a'}})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)

    def test_empty_and_outer_type(self) -> None:
        self.assertEqual(run([]), {'settings': {}})
        self.assertEqual(render([]), '{"settings":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^layered-settings: batches must be a list$'):
                api(())

    def test_batch_atomicity_and_first_failure(self) -> None:
        batches = [[{'id': 'A', 'target': 'B', 'value': 1}], None, [{}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIsNone(compute.call_args_list[1].args[0])
            self.assertEqual(batches, before)

    def test_shared_engine_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, calls in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, calls)
            error = ValueError('instrumented failure')
            with patch.object(engine, 'compute', side_effect=error):
                with self.assertRaises(ValueError) as caught:
                    api(argument)
                self.assertIs(caught.exception, error)


if __name__ == '__main__':
    unittest.main()
