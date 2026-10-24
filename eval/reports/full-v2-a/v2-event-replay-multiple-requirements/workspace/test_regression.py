import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class ReplayTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'obsolete', 'value': -100},
            {'id': 'b', 'target': 'STRASSE / Ω', 'value': -2},
            {'id': 'a', 'target': ' Straße / Ω ', 'value': 3},
            {'id': 'c', 'target': 'Z', 'value': 0},
            {'id': 'A', 'target': ' Straße / Ω ', 'value': 2},
        ]
        expected = {'balances': {'strasse / ω': 0, 'z': 0}, 'history': [2, 0, 0]}
        original = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'balances': {}, 'history': []}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"balances":{},"history":[]}\n')
        self.assertEqual(rows, original)

    def test_negative_prefix_and_revision_position(self) -> None:
        cases = [
            [{'id': 'a', 'target': 'x', 'value': -1},
             {'id': 'b', 'target': 'x', 'value': 2}],
            [{'id': 'a', 'target': 'x', 'value': 5},
             {'id': 'b', 'target': 'x', 'value': -1},
             {'id': 'a', 'target': 'y', 'value': 2}],
        ]
        for rows in cases:
            for api, argument in ((run, rows), (render, rows),
                                  (run_many, [[], rows]), (render_many, [[], rows])):
                with self.subTest(api=api.__name__, rows=rows):
                    before = copy.deepcopy(argument)
                    with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                        api(argument)
                    self.assertEqual(argument, before)

    def test_structural_validation_precedes_domain(self) -> None:
        prefix = [{'id': 'a', 'target': 'x', 'value': -1},
                  {'id': 'a', 'target': 'y', 'value': -2}]
        class IntSubclass(int):
            pass
        invalid = [{}, {'id': ' ', 'target': 'x', 'value': 1},
                   {'id': 'x', 'target': '\t', 'value': 1},
                   {'id': 1, 'target': 'x', 'value': 1},
                   {'id': 'x', 'target': 'x', 'value': True},
                   {'id': 'x', 'target': 'x', 'value': IntSubclass(1)},
                   {'id': 'x', 'target': 'x', 'value': 1, 'extra': 0}]
        for row in invalid:
            rows = prefix + [row]
            for api, argument in ((run, rows), (render, rows),
                                  (run_many, [rows]), (render_many, [rows])):
                with self.subTest(api=api.__name__, row=row):
                    before = copy.deepcopy(argument)
                    with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                        api(argument)
                    self.assertEqual(argument, before)
        self.assertEqual(validation.validate(prefix), prefix)

    def test_canonical_validation_and_unbounded_values(self) -> None:
        class Text(str):
            pass
        class Row(dict):
            pass
        class Rows(list):
            pass
        rows = Rows([Row(id=Text(' STRAẞE / X '), target=Text(' Ω  Y '), value=10 ** 100),
                     Row(id='strasse / x', target='other', value=-1)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / x', 'target': 'ω  y', 'value': 10 ** 100},
            {'id': 'strasse / x', 'target': 'other', 'value': -1}])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Ω / STRAẞE ')), 'ω / strasse')
        self.assertEqual(engine.compute(rows[:1]),
                         {'balances': {'ω  y': 10 ** 100}, 'history': [10 ** 100]})

    def test_container_errors_and_empty_inputs(self) -> None:
        for value in (None, (), {}, 'rows', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                        api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^event-replay: batches must be a list$'):
                    api(value)
        self.assertEqual(run([]), {'balances': {}, 'history': []})
        self.assertEqual(render([]), '{"balances":{},"history":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_results_and_dictionary_order(self) -> None:
        rows = [{'id': 'a', 'target': 'z', 'value': 2},
                {'id': 'b', 'target': 'a', 'value': 0}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        self.assertEqual(list(results[0]), ['balances', 'history'])
        self.assertEqual(list(results[0]['balances']), ['a', 'z'])
        results[0]['balances']['z'] = 999
        results[0]['history'].append(999)
        expected = {'balances': {'a': 0, 'z': 2}, 'history': [2, 0]}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, original)

    def test_runtime_engine_lookup_and_batch_failure_order(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, count)
        bad = [{'id': 'a', 'target': 'x', 'value': -1}]
        batches = [rows, bad, [{}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                    api(batches)
                self.assertEqual(compute.call_args_list, [unittest.mock.call(rows), unittest.mock.call(bad)])
                self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
