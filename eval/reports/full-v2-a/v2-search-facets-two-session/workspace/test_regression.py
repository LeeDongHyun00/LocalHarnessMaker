import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B_2 ', 'target': ' TOP_TAG ', 'value': -4},
            {'id': 'b-2', 'target': 'top-tag', 'value': -4},
            {'id': 'A', 'target': 'top-tag', 'value': 4},
            {'id': 'c', 'target': 'z', 'value': 9},
            {'id': 'd', 'target': 'a', 'value': 9},
            {'id': 'e', 'target': 'negative', 'value': -8},
        ]
        expected = {'facets': [
            {'name': 'top-tag', 'count': 2, 'score': 0, 'ids': ['a', 'b-2']},
            {'name': 'a', 'count': 1, 'score': 9, 'ids': ['d']},
            {'name': 'z', 'count': 1, 'score': 9, 'ids': ['c']},
            {'name': 'negative', 'count': 1, 'score': -8, 'ids': ['e']},
        ]}
        self.assertEqual(run(rows), expected)
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

        rows = Rows([Row(id=Text(' Straße_文 / X '), target=Text(' A_B / 文  C '), value=7)])
        expected = {'facets': [
            {'name': 'a-b / 文  c', 'count': 1, 'score': 7, 'ids': ['strasse-文 / x']}
        ]}
        self.assertEqual(policy.normalize(Text(' Straße_文 / X ')), 'strasse-文 / x')
        self.assertEqual(validation.validate(rows), [
            {'id': 'strasse-文 / x', 'target': 'a-b / 文  c', 'value': 7}
        ])
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(json.loads(render(rows)), expected)

    def test_validation_precedes_selection(self) -> None:
        rows = [
            {'id': ' X ', 'target': 'a', 'value': 1},
            {'id': 'x', 'target': 'b', 'value': 2},
        ]
        canonical = validation.validate(rows)
        self.assertEqual([r['target'] for r in canonical], ['a', 'b'])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        for api in (run, render, engine.compute):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^search-facets: duplicate id$'):
                    api(rows)
                with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                    api(rows + [{'id': 'later', 'target': 'a', 'value': True}])

    def test_structural_errors(self) -> None:
        class Integer(int):
            pass

        invalid_rows = [None, [], {},
                        {'id': 'x', 'target': 'a', 'value': 1, 'extra': 0},
                        {'id': 'x', 'target': 'a'},
                        {'id': ' ', 'target': 'a', 'value': 1},
                        {'id': 'x', 'target': '\t', 'value': 1},
                        {'id': 1, 'target': 'a', 'value': 1},
                        {'id': 'x', 'target': None, 'value': 1}]
        invalid_rows += [{'id': 'x', 'target': 'a', 'value': v}
                         for v in (True, False, Integer(1), 1.0, '1', None)]
        for api in (validation.validate, engine.compute, run, render):
            for value in (None, {}, (), 'rows', 1):
                with self.subTest(api=api.__name__, outer=value):
                    with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                        api(value)
            for row in invalid_rows:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                        api([row])

    def test_large_scores_and_empty(self) -> None:
        for api in (run, engine.compute):
            self.assertEqual(api([]), {'facets': []})
            self.assertEqual(api([
                {'id': 'a', 'target': 'n', 'value': 10 ** 100},
                {'id': 'b', 'target': 'n', 'value': -(10 ** 100) - 1},
            ]), {'facets': [{'name': 'n', 'count': 2, 'score': -1, 'ids': ['a', 'b']}]})
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(render([]), '{"facets":[]}\n')

    def test_input_and_output_independence(self) -> None:
        rows = [{'id': ' B ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        first['facets'][0]['ids'].append('changed')
        first['facets'][0]['score'] = 99
        first['facets'].append({})
        self.assertEqual(second, run(rows))
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        render(rows)
        self.assertEqual(rows, before)
        invalid = rows + [{'id': 'bad', 'target': 'x', 'value': {'nested': []}}]
        snapshot = copy.deepcopy(invalid)
        for api in (validation.validate, engine.compute, run, render):
            with self.assertRaises(ValueError):
                api(invalid)
            self.assertEqual(invalid, snapshot)
        conflict = rows + [{'id': 'b', 'target': 'other', 'value': 2}]
        snapshot = copy.deepcopy(conflict)
        with self.assertRaises(ValueError):
            run(conflict)
        self.assertEqual(conflict, snapshot)

    def test_render_exact_serialization(self) -> None:
        rows = [{'id': '文', 'target': 'É_文', 'value': 0}]
        self.assertEqual(render(rows),
                         '{"facets":[{"count":1,"ids":["文"],"name":"é-文","score":0}]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                               sort_keys=True, separators=(',', ':')) + '\n')

    def test_compute_resolved_at_call_time_once(self) -> None:
        rows = [{'id': 'a', 'target': 'a', 'value': 1}]
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('search-facets: invalid row')) as compute:
                with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_domain_and_serialization(self) -> None:
        rows = [
            {'id': ' B_2 ', 'target': ' TOP_TAG ', 'value': -4},
            {'id': 'b-2', 'target': 'top-tag', 'value': -4},
            {'id': 'A', 'target': 'top-tag', 'value': 4},
            {'id': 'c', 'target': 'z', 'value': 9},
            {'id': 'd', 'target': 'a', 'value': 9},
            {'id': 'e', 'target': 'negative', 'value': -8},
        ]
        batches = [rows, [], [
            {'id': ' Straße_文 / X ', 'target': ' A_B / 文  C ', 'value': 10 ** 100},
        ], rows]
        before = copy.deepcopy(batches)
        expected = [
            {'facets': [
                {'name': 'top-tag', 'count': 2, 'score': 0, 'ids': ['a', 'b-2']},
                {'name': 'a', 'count': 1, 'score': 9, 'ids': ['d']},
                {'name': 'z', 'count': 1, 'score': 9, 'ids': ['c']},
                {'name': 'negative', 'count': 1, 'score': -8, 'ids': ['e']},
            ]},
            {'facets': []},
            {'facets': [{'name': 'a-b / 文  c', 'count': 1,
                         'score': 10 ** 100, 'ids': ['strasse-文 / x']}]},
        ]
        expected.append(copy.deepcopy(expected[0]))
        results = run_many(batches)
        self.assertEqual(results, expected)
        for result in results:
            self.assertEqual(list(result), ['facets'])
            for facet in result['facets']:
                self.assertEqual(list(facet), ['name', 'count', 'score', 'ids'])
        rendered = render_many(batches)
        self.assertEqual(rendered, ''.join(render(rows) for rows in batches))
        self.assertEqual(rendered, ''.join(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for result in expected))
        self.assertEqual(batches, before)

    def test_batch_outer_empty_and_subclasses(self) -> None:
        class Batches(list):
            pass

        for api in (run_many, render_many):
            for value in (None, {}, (), 'batches', 1, iter([])):
                with self.subTest(api=api.__name__, outer=value):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^search-facets: batches must be a list$'):
                            api(value)
                        compute.assert_not_called()
            with patch.object(engine, 'compute') as compute:
                self.assertEqual(api([]), [] if api is run_many else '')
                self.assertEqual(api(Batches()), [] if api is run_many else '')
                compute.assert_not_called()
        self.assertEqual(run_many(Batches([Batches()])), [{'facets': []}])
        self.assertEqual(render_many(Batches([Batches()])), '{"facets":[]}\n')

    def test_batch_compute_once_in_encounter_order(self) -> None:
        batches = [[], [{'id': 'a', 'target': 'a', 'value': 1}], []]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, rows in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], rows)

    def test_batch_errors_stop_at_first_member(self) -> None:
        conflict = [
            {'id': ' X ', 'target': 'a', 'value': 1},
            {'id': 'x', 'target': 'b', 'value': 2},
        ]
        failures = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([{}], ValueError, 'invalid row'),
            ([{'id': 'x', 'target': 'a', 'value': True}], ValueError, 'invalid row'),
            (conflict, ValueError, 'duplicate id'),
            (conflict + [{}], ValueError, 'invalid row'),
        ]
        for api in (run_many, render_many):
            for bad, error, message in failures:
                batches = [[{'id': 'ok', 'target': 'a', 'value': 1}], bad, [{}]]
                before = copy.deepcopy(batches)
                with self.subTest(api=api.__name__, message=message, bad=bad):
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaisesRegex(error, '^search-facets: ' + message + '$'):
                            api(batches)
                        self.assertEqual(compute.call_count, 2)
                        self.assertIs(compute.call_args_list[0].args[0], batches[0])
                        self.assertIs(compute.call_args_list[1].args[0], bad)
                    self.assertEqual(batches, before)

    def test_batch_nested_result_independence(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        self.assertIsNot(first[0], first[1])
        self.assertIsNot(first[0]['facets'], first[1]['facets'])
        self.assertIsNot(first[0]['facets'][0], first[1]['facets'][0])
        self.assertIsNot(first[0]['facets'][0]['ids'], first[1]['facets'][0]['ids'])
        self.assertIsNot(first[2]['facets'], first[3]['facets'])
        first[0]['facets'][0]['ids'].append('changed')
        first[0]['facets'][0]['score'] = 99
        first[0]['facets'].append({})
        first[2]['facets'].append({})
        self.assertEqual(first[1], second[1])
        self.assertEqual(first[3], {'facets': []})
        self.assertEqual(second, run_many(batches))
        render_many(batches)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
