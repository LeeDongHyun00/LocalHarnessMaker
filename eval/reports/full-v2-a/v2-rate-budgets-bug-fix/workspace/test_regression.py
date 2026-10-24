import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Straße/Team X ', 'value': 60},
            {'id': 'a', 'target': 'STRASSE/TEAM X', 'value': 60},
            {'id': 'B', 'target': 'strasse/team x', 'value': 40},
        ]
        expected = {'remaining': {'strasse/team x': 0}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'remaining': {}}])
        self.assertEqual(project.render_many([rows, []]),
                         '{"remaining":{"strasse/team x":0}}\n{"remaining":{}}\n')

    def test_validation_preserves_order_and_duplicates(self) -> None:
        rows = [
            {'value': 10**200, 'target': ' Z / É ', 'id': ' B '},
            {'id': 'B', 'target': 'z / é', 'value': 10**200},
            {'id': 'a', 'target': 'a', 'value': -1},
        ]
        before = copy.deepcopy(rows)
        result = validation.validate(rows)
        self.assertEqual(result, [
            {'id': 'b', 'target': 'z / é', 'value': 10**200},
            {'id': 'b', 'target': 'z / é', 'value': 10**200},
            {'id': 'a', 'target': 'a', 'value': -1},
        ])
        self.assertEqual(list(result[0]), ['id', 'target', 'value'])
        result[0]['target'] = 'changed'
        self.assertEqual(result[1]['target'], 'z / é')
        self.assertEqual(rows, before)
        self.assertEqual(policy.normalize(' Straße / É  X '), 'strasse / é  x')

    def test_structural_errors_take_precedence(self) -> None:
        for earlier in (
            [{'id': 'a', 'target': 'x', 'value': 101}],
            [{'id': 'a', 'target': 'x', 'value': 1},
             {'id': 'A', 'target': 'y', 'value': 2}],
        ):
            rows = earlier + [{'id': 'bad', 'target': 'x', 'value': True}]
            for api in (project.run, project.render, engine.compute,
                        validation.validate):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                        api(rows)

    def test_structure_and_subclasses(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        self.assertEqual(project.run(ListSubclass([
            DictSubclass(id=StringSubclass(' A '), target=StringSubclass(' X '), value=0)
        ])), {'remaining': {'x': 100}})
        for rows in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^rate-budgets: rows must be a list$'):
                project.run(rows)
        for row in (None, [], {}, {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0},
                    {'id': ' ', 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': '\t', 'value': 1},
                    {'id': 1, 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': None, 'value': 1},
                    {'id': 'a', 'target': 'x', 'value': IntSubclass(1)},
                    {'id': 'a', 'target': 'x', 'value': 1.0}):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                    project.run([row])

    def test_domain_errors_and_cost_precedence(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 'x', 'value': n}], 'invalid cost')
            for n in (-10**200, 101, 10**200)
        ]
        cases += [
            ([{'id': 'a', 'target': 'x', 'value': 60},
              {'id': 'b', 'target': 'X', 'value': 41}], 'exhausted'),
            ([{'id': 'a', 'target': 'x', 'value': 60},
              {'id': 'b', 'target': 'x', 'value': 60},
              {'id': 'c', 'target': 'y', 'value': -1}], 'invalid cost'),
            ([{'id': 'a', 'target': 'x', 'value': 1},
              {'id': ' A ', 'target': 'x', 'value': 2}], 'duplicate id'),
        ]
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for api in (project.run, project.render, engine.compute):
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^rate-budgets: ' + message + '$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_serialization_order_and_independence(self) -> None:
        rows = [{'id': 'z', 'target': 'É', 'value': 1},
                {'id': 'a', 'target': 'A', 'value': 2}]
        before = copy.deepcopy(rows)
        result = project.run(rows)
        self.assertEqual(list(result['remaining']), ['a', 'é'])
        self.assertEqual(project.render(rows),
                         json.dumps(result, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')) + '\n')
        batch = project.run_many([rows, rows])
        batch[0]['remaining']['a'] = -10
        result['remaining'].clear()
        self.assertEqual(batch[1], {'remaining': {'a': 98, 'é': 99}})
        self.assertEqual(project.run(rows), batch[1])
        self.assertEqual(rows, before)
        empty = project.run_many([[], []])
        empty[0]['remaining']['new'] = 1
        self.assertEqual(empty[1], {'remaining': {}})
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')

    def test_batch_failures_are_ordered_and_atomic(self) -> None:
        batches = [[{'id': 'a', 'target': 'x', 'value': 101}], [None]]
        before = copy.deepcopy(batches)
        for api in (project.run_many, project.render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid cost$'):
                    api(batches)
                self.assertEqual(compute.call_count, 1)
            self.assertEqual(batches, before)
            for invalid in (None, (), {}, ''):
                with self.assertRaisesRegex(TypeError, '^rate-budgets: batches must be a list$'):
                    api(invalid)
            good_then_bad = [[], [{'id': 'bad', 'target': 'x', 'value': True}]]
            snapshot = copy.deepcopy(good_then_bad)
            with self.assertRaisesRegex(ValueError, '^rate-budgets: invalid row$'):
                api(good_then_bad)
            self.assertEqual(good_then_bad, snapshot)

    def test_facades_resolve_compute_at_call_time(self) -> None:
        for api, argument, calls in (
            (project.run, [], 1), (project.render, [], 1),
            (project.run_many, [[], []], 2),
            (project.render_many, [[], []], 2),
        ):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', return_value={'remaining': {'é': 7}}) as compute:
                    result = api(argument)
                    self.assertEqual(compute.call_count, calls)
                    if api is project.run:
                        self.assertEqual(result, {'remaining': {'é': 7}})
                    elif api is project.render:
                        self.assertEqual(result, '{"remaining":{"é":7}}\n')
                    elif api is project.run_many:
                        self.assertEqual(result, [{'remaining': {'é': 7}}] * 2)
                    else:
                        self.assertEqual(result, '{"remaining":{"é":7}}\n' * 2)


if __name__ == '__main__':
    unittest.main()
