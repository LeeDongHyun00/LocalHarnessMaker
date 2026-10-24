import copy
import json
import unittest
from unittest.mock import call, patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A_child ', 'target': ' Z_ROOT ', 'value': -99},
            {'id': 'z_root', 'target': 'Z_ROOT', 'value': 100},
            {'id': ' B_root ', 'target': 'b-root', 'value': 0},
            {'id': 'a-child', 'target': 'z-root', 'value': -99},
            {'id': '0_leaf', 'target': 'a-child', 'value': 1},
        ]
        self.assertEqual(run(rows), {'order': ['b-root', 'z-root', 'a-child', '0-leaf']})

    def test_normalization_and_validation(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Straße_A / B '), target=Text(' STRASSE_a / b '), value=10**200)])
        expected = [{'id': 'strasse-a / b', 'target': 'strasse-a / b', 'value': 10**200}]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Straße_A / B '), 'strasse-a / b')
        self.assertEqual(engine.compute(rows), {'order': ['strasse-a / b']})
        self.assertEqual(run(rows), {'order': ['strasse-a / b']})
        self.assertEqual(json.loads(render(rows)), {'order': ['strasse-a / b']})

    def test_structural_errors(self) -> None:
        class Integer(int):
            pass

        invalid_rows = [None, [], {}, {'id': 'x', 'target': 'x'},
                        {'id': 'x', 'target': 'x', 'value': 1, 'extra': 0}]
        for field, values in [('id', ['', '  ', 1, None]),
                              ('target', ['', '\t', False, None]),
                              ('value', [True, Integer(1), 1.0, '1', None])]:
            for value in values:
                row = {'id': 'x', 'target': 'x', 'value': 1}
                row[field] = value
                invalid_rows.append(row)
        for api in (validation.validate, engine.compute, run, render, run_many, render_many):
            for value in (None, (), {}, 'rows', 1):
                with self.subTest(api=api.__name__, value=value):
                    with self.assertRaisesRegex(TypeError, '^dependency-graph: rows must be a list$'):
                        api([value] if api in (run_many, render_many) else value)
            for row in invalid_rows:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                        api([[row]] if api in (run_many, render_many) else [row])

    def test_error_precedence_and_no_mutation(self) -> None:
        cases = [
            ([{'id': 'x', 'target': 'absent', 'value': 1},
              {'id': 'x', 'target': 'x', 'value': 2}, {}], 'invalid row'),
            ([{'id': 'x', 'target': 'absent', 'value': 1},
              {'id': 'x', 'target': 'x', 'value': 2}], 'duplicate id'),
            ([{'id': 'x', 'target': 'absent', 'value': 1}], 'missing dependency'),
            ([{'id': 'x', 'target': 'y', 'value': 1},
              {'id': 'y', 'target': 'x', 'value': 1}], 'cycle'),
            ([{'id': 'root', 'target': 'root', 'value': 1},
              {'id': 'x', 'target': 'y', 'value': 1},
              {'id': 'y', 'target': 'x', 'value': 1},
              {'id': 'z', 'target': 'absent', 'value': 1}], 'missing dependency'),
            ([{'id': 'x', 'target': 'x', 'value': {'nested': []}}], 'invalid row'),
        ]
        for api in (engine.compute, run, render, run_many, render_many):
            for rows, error in cases:
                before = copy.deepcopy(rows)
                with self.subTest(api=api.__name__, error=error):
                    with self.assertRaisesRegex(ValueError, '^dependency-graph: ' + error + '$'):
                        api([[], rows, []] if api in (run_many, render_many) else rows)
                    self.assertEqual(rows, before)

    def test_validation_does_not_select_or_check_domain(self) -> None:
        rows = [{'id': ' X ', 'target': 'absent', 'value': 1},
                {'id': 'x', 'target': 'x', 'value': 2}]
        self.assertEqual(validation.validate(rows), [
            {'id': 'x', 'target': 'absent', 'value': 1},
            {'id': 'x', 'target': 'x', 'value': 2}])

    def test_fresh_results(self) -> None:
        rows = [{'id': ' X ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        first['order'].append('changed')
        self.assertEqual(second, {'order': ['x']})
        self.assertEqual(run(rows), second)
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        self.assertEqual(list(second), ['order'])

    def test_empty(self) -> None:
        self.assertEqual(run([]), {'order': []})
        self.assertEqual(render([]), '{"order":[]}\n')
        self.assertIsNot(run([])['order'], run([])['order'])

    def test_render_exact_unicode(self) -> None:
        rows = [{'id': ' 雪 ', 'target': '雪', 'value': 0}]
        self.assertEqual(render(rows), '{"order":["雪"]}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                                sort_keys=True, separators=(',', ':')) + '\n')

    def test_shared_compute_path(self) -> None:
        rows = []
        with patch.object(engine, 'compute', return_value={'z': [{'b': 1, 'a': '雪'}], 'a': []}) as compute:
            self.assertEqual(run(rows), {'z': [{'b': 1, 'a': '雪'}], 'a': []})
            compute.assert_called_once_with(rows)
            compute.reset_mock()
            self.assertEqual(render(rows), '{"a":[],"z":[{"a":"雪","b":1}]}\n')
            compute.assert_called_once_with(rows)
        for api in (run, render):
            with patch.object(engine, 'compute', side_effect=ValueError('dependency-graph: cycle')) as compute:
                with self.assertRaisesRegex(ValueError, '^dependency-graph: cycle$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_outer_inputs(self) -> None:
        for api in (run_many, render_many):
            for value in (None, (), {}, 'batches', 1, iter([[]])):
                with self.subTest(api=api.__name__, value=value):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^dependency-graph: batches must be a list$'):
                            api(value)
                        compute.assert_not_called()

    def test_batch_empty(self) -> None:
        for api, expected in ((run_many, []), (render_many, '')):
            with patch.object(engine, 'compute') as compute:
                self.assertEqual(api([]), expected)
                compute.assert_not_called()
        self.assertEqual(run_many([[], []]), [{'order': []}, {'order': []}])
        self.assertEqual(render_many([[], []]), '{"order":[]}\n{"order":[]}\n')

    def test_batch_results_and_rendering(self) -> None:
        class Batches(list):
            pass

        batches = Batches([
            [{'id': ' A_child ', 'target': ' Z_ROOT ', 'value': -99},
             {'id': 'z_root', 'target': 'Z_ROOT', 'value': 100},
             {'id': ' B_root ', 'target': 'b-root', 'value': 0},
             {'id': 'a-child', 'target': 'z-root', 'value': -99},
             {'id': '0_leaf', 'target': 'a-child', 'value': 1}],
            [{'id': ' Straße_A / 雪 ', 'target': ' STRASSE_a / 雪 ', 'value': 10**200}],
            [],
        ])
        before = copy.deepcopy(batches)
        expected = [{'order': ['b-root', 'z-root', 'a-child', '0-leaf']},
                    {'order': ['strasse-a / 雪']}, {'order': []}]
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(run_many(batches), [run(rows) for rows in batches])
        self.assertEqual(render_many(batches),
                         '{"order":["b-root","z-root","a-child","0-leaf"]}\n'
                         '{"order":["strasse-a / 雪"]}\n{"order":[]}\n')
        self.assertEqual(render_many(batches), ''.join(render(rows) for rows in batches))
        self.assertEqual(batches, before)

    def test_batch_fresh_results(self) -> None:
        rows = [{'id': ' X ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        for index, result in enumerate(first):
            for other in first[index + 1:] + second:
                self.assertIsNot(result, other)
                self.assertIsNot(result['order'], other['order'])
        first[0]['order'].append('changed')
        first[2]['order'].append('changed')
        self.assertEqual(first[1], {'order': ['x']})
        self.assertEqual(first[3], {'order': []})
        self.assertEqual(second, [{'order': ['x']}, {'order': ['x']},
                                  {'order': []}, {'order': []}])
        self.assertEqual(run_many(batches), second)
        self.assertEqual(batches, before)
        self.assertIs(batches[0], rows)
        self.assertIs(batches[1], rows)

    def test_batch_shared_compute_path(self) -> None:
        batches = [[], [{'id': 'x', 'target': 'x', 'value': 1}], []]
        outputs = [{'z': [{'b': 1, 'a': '雪'}], 'a': []}, {'order': ['x']}, {'order': []}]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', side_effect=copy.deepcopy(outputs)) as compute:
                expected = outputs if api is run_many else (
                    '{"a":[],"z":[{"a":"雪","b":1}]}\n'
                    '{"order":["x"]}\n{"order":[]}\n')
                self.assertEqual(api(batches), expected)
                self.assertEqual(compute.call_args_list, [call(rows) for rows in batches])
                for actual, original in zip(compute.call_args_list, batches):
                    self.assertIs(actual.args[0], original)

    def test_batch_first_failure(self) -> None:
        good = [{'id': ' Root ', 'target': 'ROOT', 'value': 0}]
        bad = [{'id': 'x', 'target': 'missing', 'value': 1}]
        later = [{}]
        for api in (run_many, render_many):
            for batches in ([bad, later], [good, bad, later], [good, good, bad]):
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex(ValueError, '^dependency-graph: missing dependency$'):
                        api(batches)
                    self.assertEqual(compute.call_args_list,
                                     [call(rows) for rows in batches[:batches.index(bad) + 1]])
                self.assertEqual(batches, before)
            error = ValueError('dependency-graph: cycle')
            with patch.object(engine, 'compute', side_effect=[{'order': []}, error]) as compute:
                with self.assertRaises(ValueError) as caught:
                    api([good, bad, later])
                self.assertIs(caught.exception, error)
                self.assertEqual(compute.call_args_list, [call(good), call(bad)])


if __name__ == '__main__':
    unittest.main()
