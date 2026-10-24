import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'Old', 'value': -10},
            {'id': 'b', 'target': ' Launch ', 'value': -2},
            {'id': 'a', 'target': 'LAUNCH', 'value': -2},
            {'id': 'a', 'target': 'ignored', 'value': -3},
            {'id': 'a', 'target': 'launch', 'value': -2},
            {'id': 'z', 'target': 'Other', 'value': 10**100},
            {'id': 'c', 'target': 'launch', 'value': -4},
        ]
        expected = {'dispatch': {'launch': 'b', 'other': 'z'},
                    'shadowed': ['a', 'c']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['dispatch']), ['launch', 'other'])
        self.assertEqual(run_many([rows, []]),
                         [expected, {'dispatch': {}, 'shadowed': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' Straße / A '), target=Text(' Ä / X Y '), value=1),
                     Row(id='strasse / a', target='Next', value=2)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a', 'target': 'ä / x y', 'value': 1},
            {'id': 'strasse / a', 'target': 'next', 'value': 2}])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / A ')), 'strasse / a')
        expected = {'dispatch': {'next': 'strasse / a'}, 'shadowed': []}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        single = [rows[0]]
        self.assertEqual(render(single),
                         '{"dispatch":{"ä / x y":"strasse / a"},"shadowed":[]}\n')
        self.assertEqual(render_many([single]), render(single))

    def test_invalid_rows_and_precedence(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'b'},
                   {'id': 'a', 'target': 'b', 'value': 1, 'extra': {}},
                   {'id': ' ', 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': '\t', 'value': 1},
                   {'id': 1, 'target': 'b', 'value': 1},
                   {'id': 'a', 'target': None, 'value': 1},
                   {'id': 'a', 'target': 'b', 'value': True},
                   {'id': 'a', 'target': 'b', 'value': Integer(1)},
                   {'id': 'a', 'target': 'b', 'value': 1.0}]
        conflict = [{'id': 'a', 'target': 'one', 'value': 1},
                    {'id': 'A', 'target': 'two', 'value': 1}]
        for row in invalid:
            rows = conflict + [row]
            before = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                    api([rows])
                self.assertEqual(rows, before)

    def test_ambiguity_is_immediate_after_validation(self) -> None:
        rows = [{'id': ' A ', 'target': 'one', 'value': 1},
                {'id': 'a', 'target': 'two', 'value': 1},
                {'id': 'a', 'target': 'three', 'value': 2}]
        self.assertEqual(len(validation.validate(rows)), 3)
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^command-dispatch: ambiguous id$'):
                api(rows)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^command-dispatch: ambiguous id$'):
                api([rows, [None]])

    def test_container_types_and_empty_results(self) -> None:
        for bad in (None, (), {}, 'rows', iter([])):
            for api in (validation.validate, engine.compute, run, render):
                with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                    api(bad)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^command-dispatch: batches must be a list$'):
                    api(bad)
                with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                    api([bad])
        self.assertEqual(run([]), {'dispatch': {}, 'shadowed': []})
        self.assertEqual(render([]), '{"dispatch":{},"shadowed":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_output_isolation(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 0},
                {'id': 'b', 'target': 'x', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        expected = copy.deepcopy(results[1])
        results[0]['dispatch']['x'] = 'changed'
        results[0]['shadowed'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)

    def test_shared_compute_path(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        other = [{'id': 'b', 'target': 'y', 'value': 2}]
        for api, argument, members in ((run, rows, [rows]),
                                       (render, rows, [rows]),
                                       (run_many, [rows, other], [rows, other]),
                                       (render_many, [rows, other], [rows, other])):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, len(members))
                    for call, member in zip(compute.call_args_list, members):
                        self.assertIs(call.args[0], member)
        sentinel = {'z': {'β': 1, 'a': 2}, 'a': ['é']}
        with patch.object(engine, 'compute', return_value=sentinel):
            self.assertEqual(run(rows), sentinel)
            self.assertEqual(render(rows), json.dumps(sentinel, ensure_ascii=False,
                                                     sort_keys=True, separators=(',', ':')) + '\n')

    def test_batch_failure_stops_in_encounter_order(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 1}]
        bad = [{'id': 'a', 'target': 'x', 'value': 1},
               {'id': 'a', 'target': 'y', 'value': 1}]
        batches = [good, bad, [None]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^command-dispatch: ambiguous id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
