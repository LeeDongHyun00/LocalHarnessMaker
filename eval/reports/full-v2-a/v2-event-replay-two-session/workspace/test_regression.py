import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' CREDIT_A ', 'target': ' Straße_/X Y ', 'value': 8},
            {'id': 'credit-a', 'target': 'strasse-/x y', 'value': 8},
            {'id': 'debit', 'target': 'STRASSE_/X Y', 'value': -8},
            {'id': 'other', 'target': ' A ', 'value': 2},
        ]
        expected = {'balances': {'a': 2, 'strasse-/x y': 0}, 'history': [8, 0, 2]}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(list(project.run(rows)['balances']), ['a', 'strasse-/x y'])
        self.assertEqual(policy.normalize(' Straße_/X Y '), 'strasse-/x y')

    def test_error_ordering(self) -> None:
        negative = {'id': 'a', 'target': 'x', 'value': -1}
        duplicate = {'id': 'a', 'target': 'x', 'value': 2}
        invalid = {'id': 'later', 'target': 'x', 'value': True}
        cases = [
            ([negative, duplicate, invalid], 'invalid row'),
            ([negative, invalid], 'invalid row'),
            ([negative, duplicate], 'duplicate id'),
            ([negative, {'id': 'repair', 'target': 'x', 'value': 2}], 'negative prefix'),
        ]
        for api in (project.run, project.render, engine.compute):
            for rows, message in cases:
                with self.subTest(api=api.__name__, message=message):
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, '^event-replay: ' + message + '$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_structural_validation(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        row = DictSubclass(id=StringSubclass(' A_ '), target=StringSubclass(' X_ '), value=10**100)
        rows = ListSubclass([row, row])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'a-', 'target': 'x-', 'value': 10**100}] * 2)
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], row)
        self.assertEqual(project.run(rows)['history'], [10**100])
        for bad in (None, (), {}, 'rows'):
            for api in (project.run, project.render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                    api(bad)
        for bad in (None, [], {}, {'id': 'a', 'target': 'x', 'value': 1, 'extra': 0},
                    {'id': ' ', 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': 1, 'value': 1},
                    {'id': 'a', 'target': 'x', 'value': IntSubclass(1)},
                    {'id': 'a', 'target': 'x', 'value': 1.0}):
            with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                project.run([bad])
        # Validation performs neither duplicate selection nor domain checks.
        self.assertEqual(len(validation.validate([
            {'id': 'a', 'target': 'x', 'value': -1},
            {'id': 'a', 'target': 'y', 'value': 1},
        ])), 2)

    def test_serialization_and_shared_path(self) -> None:
        rows = [{'id': 'a', 'target': ' É ', 'value': 1}]
        expected = {'balances': {'é': 1}, 'history': [1]}
        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
            self.assertEqual(project.run(rows), expected)
            compute.assert_called_once_with(rows)
        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
            self.assertEqual(project.render(rows), '{"balances":{"é":1},"history":[1]}\n')
            compute.assert_called_once_with(rows)
        self.assertEqual(project.render(rows), json.dumps(project.run(rows), ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')

    def test_empty_and_output_independence(self) -> None:
        self.assertEqual(project.run([]), {'balances': {}, 'history': []})
        self.assertEqual(project.render([]), '{"balances":{},"history":[]}\n')
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        first, second = project.run(rows), project.run(rows)
        first['balances']['x'] = 99
        first['history'].append(99)
        self.assertEqual(second, {'balances': {'x': 1}, 'history': [1]})
        self.assertEqual(project.run(rows), second)
        self.assertEqual(rows, before)

    def test_batch_results_and_shared_path(self) -> None:
        batches = [
            [
                {'id': ' CREDIT_A ', 'target': ' Straße_/X Y ', 'value': 8},
                {'id': 'credit-a', 'target': 'strasse-/x y', 'value': 8},
                {'id': 'debit', 'target': 'STRASSE_/X Y', 'value': -8},
                {'id': 'other', 'target': ' A ', 'value': 2},
            ],
            [],
            [{'id': 'credit-a', 'target': ' É ', 'value': 3}],
        ]
        before = copy.deepcopy(batches)
        expected = [
            {'balances': {'a': 2, 'strasse-/x y': 0}, 'history': [8, 0, 2]},
            {'balances': {}, 'history': []},
            {'balances': {'é': 3}, 'history': [3]},
        ]
        rendered = ''.join(json.dumps(result, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':')) + '\n' for result in expected)
        for api, output in ((project.run_many, expected), (project.render_many, rendered)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    actual = api(batches)
                    self.assertEqual(actual, output)
                    self.assertEqual(compute.call_count, len(batches))
                    for call, member in zip(compute.call_args_list, batches):
                        self.assertIs(call.args[0], member)
                self.assertEqual(batches, before)
        self.assertEqual(list(project.run_many(batches)[0]['balances']), ['a', 'strasse-/x y'])

    def test_batch_outer_validation_and_empty(self) -> None:
        class ListSubclass(list):
            pass

        for api in (project.run_many, project.render_many):
            for bad in (None, (), {}, 'batches', iter([]), 1):
                with self.subTest(api=api.__name__, bad=type(bad).__name__):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^event-replay: batches must be a list$'):
                            api(bad)
                        compute.assert_not_called()
            for empty in ([], ListSubclass()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(api(empty), [] if api is project.run_many else '')
                    compute.assert_not_called()
            batches = ListSubclass([ListSubclass([{'id': ' A_ ', 'target': ' X_ ', 'value': 1}])])
            self.assertEqual(api(batches),
                             [{'balances': {'x-': 1}, 'history': [1]}]
                             if api is project.run_many else '{"balances":{"x-":1},"history":[1]}\n')

    def test_batch_first_failure_and_policy_ordering(self) -> None:
        negative = {'id': 'a', 'target': 'x', 'value': -1}
        duplicate = {'id': 'a', 'target': 'x', 'value': 2}
        invalid = {'id': 'later', 'target': 'x', 'value': True}
        cases = [
            (None, TypeError, 'rows must be a list'),
            ((), TypeError, 'rows must be a list'),
            ([negative, duplicate, invalid], ValueError, 'invalid row'),
            ([negative, invalid], ValueError, 'invalid row'),
            ([negative, duplicate], ValueError, 'duplicate id'),
            ([negative, {'id': 'repair', 'target': 'x', 'value': 2}], ValueError, 'negative prefix'),
        ]
        for api in (project.run_many, project.render_many):
            for member, error, message in cases:
                for failure_index in (0, 1):
                    with self.subTest(api=api.__name__, message=message, index=failure_index):
                        batches = [[]] * failure_index + [member, [invalid]]
                        before = copy.deepcopy(batches)
                        with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                            with self.assertRaisesRegex(error, '^event-replay: ' + message + '$'):
                                api(batches)
                            self.assertEqual(compute.call_count, failure_index + 1)
                            for call, rows in zip(compute.call_args_list, batches):
                                self.assertIs(call.args[0], rows)
                        self.assertEqual(batches, before)

    def test_batch_nested_result_independence(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = project.run_many(batches)
        second = project.run_many(batches)
        for index, result in enumerate(first):
            for other in first[index + 1:] + second:
                self.assertIsNot(result, other)
                self.assertIsNot(result['balances'], other['balances'])
                self.assertIsNot(result['history'], other['history'])
        first[0]['balances']['x'] = 99
        first[0]['history'].append(99)
        self.assertEqual(first[1], {'balances': {'x': 1}, 'history': [1]})
        first[2]['balances']['new'] = 1
        first[2]['history'].append(1)
        self.assertEqual(first[3], {'balances': {}, 'history': []})
        self.assertEqual(project.run_many(batches), second)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
