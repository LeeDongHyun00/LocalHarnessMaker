import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B ', 'target': ' Alpha ', 'value': -3},
            {'id': 'b', 'target': 'alpha', 'value': -3},
            {'id': 'A', 'target': 'ALPHA', 'value': 3},
            {'id': 'c', 'target': 'beta', 'value': 100},
            {'id': 'd', 'target': 'gamma', 'value': -8},
            {'id': 'e', 'target': 'delta', 'value': -8},
        ]
        expected = {'facets': [
            {'name': 'alpha', 'count': 2, 'score': 0, 'ids': ['a', 'b']},
            {'name': 'beta', 'count': 1, 'score': 100, 'ids': ['c']},
            {'name': 'delta', 'count': 1, 'score': -8, 'ids': ['e']},
            {'name': 'gamma', 'count': 1, 'score': -8, 'ids': ['d']},
        ]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'facets': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        self.assertEqual(list(run(rows)), ['facets'])
        for facet in run(rows)['facets']:
            self.assertEqual(list(facet), ['name', 'count', 'score', 'ids'])

    def test_normalization_and_subclasses(self) -> None:
        class Text(str):
            pass

        class Row(dict):
            pass

        class Rows(list):
            pass

        rows = Rows([Row(id=Text(' Straße / X  Y '),
                         target=Text(' CAFÉ / A  B '), value=10 ** 100)])
        expected = {'facets': [{'name': 'café / a  b', 'count': 1,
                               'score': 10 ** 100, 'ids': ['strasse / x  y']}]}
        self.assertEqual(policy.normalize(Text(' Straße / X  Y ')), 'strasse / x  y')
        for api in (run, engine.compute):
            self.assertEqual(api(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows]), encoded)

    def test_validation_keeps_all_rows_and_is_fresh(self) -> None:
        rows = [{'value': 1, 'target': ' X ', 'id': ' A '},
                {'id': 'a', 'target': 'x', 'value': 1},
                {'id': 'a', 'target': 'y', 'value': 2}]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'a', 'target': 'x', 'value': 1},
            {'id': 'a', 'target': 'y', 'value': 2}])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        canonical[0]['target'] = 'changed'
        self.assertEqual(canonical[1]['target'], 'x')
        self.assertEqual(rows, before)

    def test_invalid_rows(self) -> None:
        class Score(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'x'},
                   {'id': 'a', 'target': 'x', 'value': 1, 'extra': []},
                   {'id': ' ', 'target': 'x', 'value': 1},
                   {'id': 'a', 'target': '\t', 'value': 1},
                   {'id': 1, 'target': 'x', 'value': 1},
                   {'id': 'a', 'target': [], 'value': 1}]
        invalid.extend({'id': 'a', 'target': 'x', 'value': value}
                       for value in (True, Score(1), 1.0, '1', None, {}))
        for row in invalid:
            for api in (run, render, engine.compute, validation.validate,
                        lambda rows: run_many([rows]),
                        lambda rows: render_many([rows])):
                with self.subTest(row=row, api=api):
                    rows = [row]
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_structural_errors_precede_duplicates(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1},
                {'id': ' A ', 'target': 'y', 'value': 1}, {}]
        for api in (run, render, engine.compute,
                    lambda rows: run_many([rows]),
                    lambda rows: render_many([rows])):
            with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                api(rows)
            with self.assertRaisesRegex(ValueError, '^search-facets: duplicate id$'):
                api(rows[:-1])

    def test_outer_types_and_empty_inputs(self) -> None:
        for invalid in (None, (), {}, '', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                    api(invalid)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^search-facets: batches must be a list$'):
                    api(invalid)
        self.assertEqual(run([]), {'facets': []})
        self.assertEqual(render([]), '{"facets":[]}\n')
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': -1}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        other = run(rows)
        expected = copy.deepcopy(other)
        outputs[0]['facets'][0]['ids'].append('extra')
        outputs[0]['facets'][0]['name'] = 'changed'
        outputs[0]['facets'].append({})
        self.assertEqual(outputs[1], expected)
        self.assertEqual(other, expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        self.assertIsNot(run([])['facets'], run([])['facets'])

    def test_runtime_compute_lookup(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 1}]
        second = [{'id': 'b', 'target': 'y', 'value': -2}]
        for api, argument, members in (
                (run, first, [first]), (render, first, [first]),
                (run_many, [first, second], [first, second]),
                (render_many, [first, second], [first, second])):
            with patch.object(engine, 'compute', return_value={'facets': []}) as compute:
                result = api(argument)
                self.assertEqual(compute.call_count, len(members))
                for call, member in zip(compute.call_args_list, members):
                    self.assertIs(call.args[0], member)
                if api is run:
                    self.assertEqual(result, {'facets': []})
                elif api is render:
                    self.assertEqual(result, '{"facets":[]}\n')

    def test_batches_stop_at_first_failure(self) -> None:
        valid = [{'id': 'a', 'target': 'x', 'value': 1}]
        duplicate = valid + [{'id': 'a', 'target': 'y', 'value': 1}]
        batches = [valid, duplicate, [{}]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^search-facets: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], valid)
                self.assertIs(compute.call_args_list[1].args[0], duplicate)
            self.assertEqual(batches, before)
        error = RuntimeError('sentinel')
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', side_effect=error) as compute:
                with self.assertRaises(RuntimeError) as raised:
                    api(batches)
                self.assertIs(raised.exception, error)
                self.assertEqual(compute.call_count, 1)


if __name__ == '__main__':
    unittest.main()
