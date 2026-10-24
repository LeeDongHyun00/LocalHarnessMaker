import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'obsolete', 'value': 100},
            {'id': 'b', 'target': ' Beta ', 'value': 2},
            {'id': 'a', 'target': 'BETA', 'value': -5},
            {'id': 'c', 'target': 'zero', 'value': 0},
            {'id': 'd', 'target': 'alpha', 'value': 0},
            {'id': 'e', 'target': 'negative', 'value': -8},
            {'id': 'f', 'target': 'positive', 'value': 9},
        ]
        expected = {'facets': [
            {'name': 'beta', 'count': 2, 'score': -3, 'ids': ['a', 'b']},
            {'name': 'positive', 'count': 1, 'score': 9, 'ids': ['f']},
            {'name': 'alpha', 'count': 1, 'score': 0, 'ids': ['d']},
            {'name': 'zero', 'count': 1, 'score': 0, 'ids': ['c']},
            {'name': 'negative', 'count': 1, 'score': -8, 'ids': ['e']},
        ]}
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(run(rows), expected)
        self.assertEqual(render(rows), encoded)
        self.assertEqual(run_many([rows, []]), [expected, {'facets': []}])
        self.assertEqual(render_many([rows, []]), encoded + '{"facets":[]}\n')

    def test_validation_preserves_all_revisions(self) -> None:
        rows = [
            {'id': ' Straße / A ', 'target': ' É / X  Y ', 'value': 10**100},
            {'id': 'STRASSE / A', 'target': 'elsewhere', 'value': -10**101},
        ]
        original = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a', 'target': 'é / x  y', 'value': 10**100},
            {'id': 'strasse / a', 'target': 'elsewhere', 'value': -10**101},
        ])
        self.assertEqual(policy.normalize(' É / X  Y '), 'é / x  y')
        self.assertEqual(run(rows)['facets'], [
            {'name': 'elsewhere', 'count': 1, 'score': -10**101,
             'ids': ['strasse / a']},
        ])
        self.assertEqual(rows, original)
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, original)

    def test_selection_retains_first_position(self) -> None:
        rows = [
            {'id': 'a', 'target': 'old', 'value': 8},
            {'id': 'b', 'target': 'b', 'value': 2},
            {'id': ' A ', 'target': 'new', 'value': -1},
        ]
        with patch.object(engine, 'resolve', wraps=engine.resolve) as resolve:
            run(rows)
        self.assertEqual(resolve.call_args.args[0], [
            {'id': 'a', 'target': 'new', 'value': -1},
            {'id': 'b', 'target': 'b', 'value': 2},
        ])

    def test_structural_errors(self) -> None:
        class Integer(int):
            pass

        valid = {'id': 'a', 'target': 'x', 'value': 1}
        invalid_rows = [None, [], {}, {**valid, 'extra': 1},
                        {**valid, 'id': '  '}, {**valid, 'id': 1},
                        {**valid, 'target': '\t'}, {**valid, 'target': None},
                        {**valid, 'value': True}, {**valid, 'value': Integer(1)},
                        {**valid, 'value': 1.0}]
        for bad in invalid_rows:
            rows = [valid, {**valid, 'value': -3}, bad]
            original = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render,
                        lambda r: run_many([r]), lambda r: render_many([r])):
                with self.subTest(bad=bad, api=api):
                    with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, original)
        for bad in (None, (), {}, 'rows'):
            for api in (validation.validate, engine.compute, run, render):
                with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                    api(bad)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^search-facets: batches must be a list$'):
                    api(bad)

    def test_allowed_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' A '), target=Text(' É '), value=0)])
        expected = {'facets': [{'name': 'é', 'count': 1, 'score': 0, 'ids': ['a']}]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        self.assertEqual(render(rows), '{"facets":[{"count":1,"ids":["a"],"name":"é","score":0}]}\n')

    def test_batch_atomicity_and_runtime_dispatch(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 1}]
        bad = [{'id': 'a', 'target': 'x', 'value': False}]
        later = [{'id': 'later', 'target': 'x', 'value': 1}]
        for api in (run_many, render_many):
            batches = [first, bad, later]
            original = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], first)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, original)
        for api, argument, expected_calls in (
            (run, first, 1), (render, first, 1),
            (run_many, [first, later], 2), (render_many, [first, later], 2),
        ):
            with patch.object(engine, 'compute', return_value={'facets': []}) as compute:
                api(argument)
                self.assertEqual(compute.call_count, expected_calls)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                api([()])

    def test_fresh_outputs_and_insertion_order(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        original = copy.deepcopy(rows)
        results = run_many([rows, rows])
        subsequent = run(rows)
        self.assertEqual(list(subsequent), ['facets'])
        self.assertEqual(list(subsequent['facets'][0]), ['name', 'count', 'score', 'ids'])
        results[0]['facets'][0]['ids'].append('changed')
        results[0]['facets'][0]['name'] = 'changed'
        results[0]['facets'].append({})
        self.assertEqual(results[1], subsequent)
        self.assertEqual(run(rows), subsequent)
        results[1]['facets'].clear()
        self.assertEqual(run(rows), subsequent)
        self.assertEqual(rows, original)

    def test_empty_inputs(self) -> None:
        self.assertEqual(run([]), {'facets': []})
        self.assertEqual(render([]), '{"facets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        results = run_many([[], []])
        results[0]['facets'].append({})
        self.assertEqual(results[1], {'facets': []})


if __name__ == '__main__':
    unittest.main()
