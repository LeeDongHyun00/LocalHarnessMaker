import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' B ', 'target': ' Straße / X ', 'value': -5},
            {'id': 'b', 'target': 'STRASSE / X', 'value': -5},
            {'id': ' A ', 'target': 'strasse / x', 'value': 5},
            {'id': 'c', 'target': 'Z', 'value': 100},
            {'id': 'd', 'target': 'Beta', 'value': -1},
            {'id': 'e', 'target': 'Alpha', 'value': -1},
        ]
        expected = {'facets': [
            {'name': 'strasse / x', 'count': 2, 'score': 0, 'ids': ['a', 'b']},
            {'name': 'z', 'count': 1, 'score': 100, 'ids': ['c']},
            {'name': 'alpha', 'count': 1, 'score': -1, 'ids': ['e']},
            {'name': 'beta', 'count': 1, 'score': -1, 'ids': ['d']},
        ]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'facets': []}])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, []]), encoded + '{"facets":[]}\n')
        self.assertEqual(list(run(rows)['facets'][0]), ['name', 'count', 'score', 'ids'])

    def test_validation_and_precedence(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        row = DictSubclass(id=StringSubclass(' A '), target=StringSubclass(' É / X '),
                           value=10 ** 200)
        rows = ListSubclass([row, dict(row)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'a', 'target': 'é / x', 'value': 10 ** 200},
            {'id': 'a', 'target': 'é / x', 'value': 10 ** 200},
        ])
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], row)
        self.assertEqual(policy.normalize(' Straße /  É '), 'strasse /  é')
        self.assertEqual(engine.compute(rows), run(rows))
        bad_rows = [None, [], {}, dict(row, extra=1), dict(row, id=' '),
                    dict(row, target=1), dict(row, value=True),
                    dict(row, value=IntSubclass(1)), dict(row, value=1.0)]
        conflict = dict(row, value=-1)
        for bad in bad_rows:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(bad=bad, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                        api([row, conflict, bad])
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^search-facets: duplicate id$'):
                api([row, conflict])

    def test_container_contracts_and_empty(self) -> None:
        for api in (run, render, engine.compute, validation.validate):
            for value in (None, {}, (), 'rows'):
                with self.assertRaisesRegex(TypeError, '^search-facets: rows must be a list$'):
                    api(value)
        for api in (run_many, render_many):
            for value in (None, {}, (), 'batches'):
                with self.assertRaisesRegex(TypeError, '^search-facets: batches must be a list$'):
                    api(value)
        self.assertEqual(run([]), {'facets': []})
        self.assertEqual(render([]), '{"facets":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' É ', 'value': -2}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['facets'][0]['ids'].append('changed')
        results[0]['facets'][0]['score'] = 7
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, before)
        self.assertEqual(render(rows), '{"facets":[{"count":1,"ids":["a"],"name":"é","score":-2}]}\n')
        bad = [rows[0], {'id': 'x', 'target': 'y', 'value': {'nested': []}}]
        batches = [rows, bad, rows]
        snapshot = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^search-facets: invalid row$'):
                api(batches)
            self.assertEqual(batches, snapshot)

    def test_shared_engine_and_batch_failure_order(self) -> None:
        rows = [{'id': 'x', 'target': 'y', 'value': 1}]
        for api, argument, count in (
            (run, rows, 1), (render, rows, 1),
            (run_many, [rows, rows], 2), (render_many, [rows, rows], 2),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                for call in compute.call_args_list:
                    self.assertIs(call.args[0], rows)
        duplicate = rows + [dict(rows[0], value=2)]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^search-facets: duplicate id$'):
                    api([rows, duplicate, None])
                self.assertEqual(compute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
