import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B ', 'target': 'Old', 'value': -4},
            {'id': 'A', 'target': 'Group', 'value': 0},
            {'id': 'b', 'target': 'GROUP', 'value': -1},
            {'id': 'b', 'target': 'Ignored', 'value': -2},
            {'id': 'a', 'target': 'group', 'value': 0},
            {'id': 'c', 'target': 'Alpha', 'value': 8},
            {'id': 'd', 'target': 'Beta', 'value': 8},
            {'id': 'e', 'target': 'Zero', 'value': 0},
        ]
        expected = {'facets': [
            {'name': 'group', 'count': 2, 'score': -1, 'ids': ['a', 'b']},
            {'name': 'alpha', 'count': 1, 'score': 8, 'ids': ['c']},
            {'name': 'beta', 'count': 1, 'score': 8, 'ids': ['d']},
            {'name': 'zero', 'count': 1, 'score': 0, 'ids': ['e']},
        ]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'facets': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation_order(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([
            Row(id=Text(' Straße / A  B '), target=Text(' É / X  Y '), value=-9),
            Row(id='Other', target='É / X  Y', value=0),
        ])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a  b', 'target': 'é / x  y', 'value': -9},
            {'id': 'other', 'target': 'é / x  y', 'value': 0},
        ])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' Straße / A  B ')), 'strasse / a  b')
        expected = {'facets': [
            {'name': 'é / x  y', 'count': 2, 'score': -9,
             'ids': ['other', 'strasse / a  b']},
        ]}
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        encoded = '{"facets":[{"count":2,"ids":["other","strasse / a  b"],"name":"é / x  y","score":-9}]}\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many(Rows([rows])), encoded)
        facet = run(rows)['facets'][0]
        self.assertEqual(list(facet), ['name', 'count', 'score', 'ids'])

    def test_structural_errors_precede_selection(self) -> None:
        class Integer(int):
            pass

        ambiguous = [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'A', 'target': 'y', 'value': 1},
        ]
        malformed = [None, [], {},
                     {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0},
                     {'id': ' ', 'target': 'x', 'value': 1},
                     {'id': 'a', 'target': '\t', 'value': 1},
                     {'id': 1, 'target': 'x', 'value': 1},
                     {'id': 'a', 'target': None, 'value': 1},
                     {'id': 'a', 'target': 'x', 'value': True},
                     {'id': 'a', 'target': 'x', 'value': Integer(1)},
                     {'id': 'a', 'target': 'x', 'value': 1.0}]
        for bad in malformed:
            rows = ambiguous + [bad]
            before = copy.deepcopy(rows)
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(bad=bad, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in (validation.validate, engine.compute, run, render):
            for bad in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                    api(bad)
        self.assertEqual(len(validation.validate(ambiguous)), 2)
        for api in (engine.compute, run, render):
            with self.assertRaisesRegex(ValueError, '^search-facets: ambiguous id$'):
                api(ambiguous + [{'id': 'a', 'target': 'z', 'value': 9}])

    def test_batch_atomicity_and_engine_dispatch(self) -> None:
        good = [{'id': 'a', 'target': 'x', 'value': 2}]
        ambiguous = good + [{'id': 'a', 'target': 'y', 'value': 2}]
        invalid = [{'id': 'bad'}]
        for api in (run_many, render_many):
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^search-facets: batches must be a list$'):
                    api(bad)
            for member, error, message in (
                (ambiguous, ValueError, 'ambiguous id'),
                (invalid, ValueError, 'invalid row'),
                (None, TypeError, 'rows must be a list'),
            ):
                batches = [good, member, invalid]
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(error, '^search-facets: ' + message + '$'):
                        api(batches)
                    self.assertEqual(compute.call_count, 2)
                    self.assertIs(compute.call_args_list[0].args[0], good)
                    self.assertIs(compute.call_args_list[1].args[0], member)
                self.assertEqual(batches, before)
        for api in (run, render):
            with patch.object(engine, 'compute', return_value={'facets': []}) as compute:
                api(good)
                compute.assert_called_once_with(good)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', return_value={'facets': []}) as compute:
                api([good, invalid])
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[1].args[0], invalid)

    def test_fresh_outputs_and_empty_batches(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 10 ** 100}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        expected = run(rows)
        outputs[0]['facets'][0]['ids'].append('changed')
        outputs[0]['facets'][0]['score'] = 0
        outputs[0]['facets'].append({})
        self.assertEqual(outputs[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(run([]), {'facets': []})
        self.assertEqual(render([]), '{"facets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(render_many([rows, rows]), render(rows) * 2)
        self.assertEqual(json.loads(render(rows)), expected)


if __name__ == '__main__':
    unittest.main()
