import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def event(identifier: str, target: str, value: int) -> dict:
    return {'id': identifier, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [event(' START_ID ', ' Straße_A / B ', 0),
                event('start-id', 'strasse-a / b', 0),
                event('again', 'STRASSE_A / B', 0),
                event('next', 'strasse-a / b', 1),
                event('end', 'strasse-a / b', 2),
                event('end-again', 'strasse-a / b', 2)]
        self.assertEqual(run(rows), {'states': {'strasse-a / b': 2}})
        self.assertEqual(engine.compute(rows), run(rows))

    def test_transition_and_state_errors(self) -> None:
        cases = [([1], 'invalid transition'), ([2], 'invalid transition'),
                 ([0, 2], 'invalid transition'),
                 ([0, 1, 0], 'invalid transition'),
                 ([0, 1, 2, 1], 'invalid transition'),
                 ([0, 1, 2, 0], 'invalid transition'),
                 ([0, 2, 10 ** 100], 'invalid state'),
                 ([-10 ** 100], 'invalid state')]
        for codes, error in cases:
            rows = [event(str(i), 'a', code) for i, code in enumerate(codes)]
            for api in (run, render, engine.compute):
                with self.subTest(codes=codes, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^workflow-state: ' + error + '$'):
                        api(rows)

    def test_validation_and_error_precedence(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [None, [], {}, event('', 'a', 0), event('a', '  ', 0),
                     event(1, 'a', 0), event('a', None, 0),
                     event('a', 'a', True), event('a', 'a', IntSubclass(0)),
                     event('a', 'a', 0.0), dict(event('a', 'a', 0), extra=1)]
        for row in malformed:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                        api([event('dup', 'a', 2), event('dup', 'b', 9), row])
        for rows in (None, (), {}, 'rows'):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^workflow-state: rows must be a list$'):
                    api(rows)
        with self.assertRaisesRegex(ValueError, '^workflow-state: duplicate id$'):
            run([event(' X_Y ', 'a', 99), event('x-y', 'b', 0)])

    def test_canonical_validation_without_domain_selection(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        rows = ListSubclass([DictSubclass(event(StrSubclass(' X_Y '), ' Ä / B_C ', 10 ** 100)),
                             event('x-y', 'other', -1)])
        expected = [event('x-y', 'ä / b-c', 10 ** 100), event('x-y', 'other', -1)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertEqual(policy.normalize(' Straße_A / B '), 'strasse-a / b')

    def test_order_and_render(self) -> None:
        rows = [event('1', 'Z', 0), event('2', 'é', 0), event('3', 'A', 0),
                event('4', 'z', 1), event('5', 'a', 1)]
        result = run(rows)
        self.assertEqual(list(result['states']), ['a', 'z', 'é'])
        self.assertEqual(render(rows), '{"states":{"a":1,"z":1,"é":0}}\n')
        self.assertEqual(json.loads(render(rows)), result)
        self.assertEqual(run([]), {'states': {}})
        self.assertEqual(render([]), '{"states":{}}\n')

    def test_fresh_outputs_and_no_mutation(self) -> None:
        rows = [event(' X ', ' A ', 0)]
        before = copy.deepcopy(rows)
        first, second = run(rows), run(rows)
        first['states']['a'] = 2
        self.assertEqual(second, {'states': {'a': 0}})
        self.assertEqual(run(rows), second)
        canonical = validation.validate(rows)
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, before)
        failures = [[event('x', 'a', 0), event('x', 'b', 0)],
                    [event('x', 'a', 2)],
                    [event('x', 'a', 5)],
                    [event('x', 'a', 0), {'nested': {'keep': []}}]]
        for invalid in failures:
            snapshot = copy.deepcopy(invalid)
            with self.assertRaises(ValueError):
                run(invalid)
            self.assertEqual(invalid, snapshot)

    def test_compute_resolved_at_call_time_once(self) -> None:
        rows = [event('x', 'a', 0)]
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('workflow-state: invalid state')) as compute:
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid state$'):
                    api(rows)
                compute.assert_called_once_with(rows)

    def test_batch_results_and_render_order(self) -> None:
        batches = [[event(' START_ID ', ' Straße_A / B ', 0),
                    event('start-id', 'strasse-a / b', 0),
                    event('next', 'STRASSE_A / B', 1),
                    event('end', 'strasse-a / b', 2)],
                   [],
                   [event('1', 'Z', 0), event('2', 'é', 0),
                    event('3', 'A', 0), event('4', 'z', 1)],
                   [event(' START_ID ', ' Straße_A / B ', 0)]]
        expected = [{'states': {'strasse-a / b': 2}}, {'states': {}},
                    {'states': {'a': 0, 'z': 1, 'é': 0}},
                    {'states': {'strasse-a / b': 0}}]
        results = run_many(batches)
        self.assertEqual(results, expected)
        self.assertEqual(list(results[2]['states']), ['a', 'z', 'é'])
        self.assertEqual(render_many(batches),
                         '{"states":{"strasse-a / b":2}}\n'
                         '{"states":{}}\n'
                         '{"states":{"a":0,"z":1,"é":0}}\n'
                         '{"states":{"strasse-a / b":0}}\n')
        self.assertEqual(render_many(batches), ''.join(map(render, batches)))

    def test_batch_outer_validation_and_empty(self) -> None:
        class ListSubclass(list):
            pass

        for api in (run_many, render_many):
            for invalid in (None, (), {}, 'batches', iter([]), 0):
                with self.subTest(api=api.__name__, invalid=invalid):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^workflow-state: batches must be a list$'):
                            api(invalid)
                        compute.assert_not_called()
            with patch.object(engine, 'compute') as compute:
                self.assertEqual(api([]), [] if api is run_many else '')
                self.assertEqual(api(ListSubclass()), [] if api is run_many else '')
                compute.assert_not_called()
        batches = ListSubclass([ListSubclass([event('x', 'a', 0)])])
        self.assertEqual(run_many(batches), [{'states': {'a': 0}}])
        self.assertEqual(render_many(batches), '{"states":{"a":0}}\n')

    def test_batch_day_one_errors_and_precedence(self) -> None:
        cases = [((), TypeError, 'rows must be a list'),
                 ([event('x', 'a', 2), event('x', 'b', 9), {}],
                  ValueError, 'invalid row'),
                 ([event(' X_Y ', 'a', 99), event('x-y', 'b', 0)],
                  ValueError, 'duplicate id'),
                 ([event('x', 'a', 2), event('y', 'a', 99)],
                  ValueError, 'invalid state'),
                 ([event('x', 'a', 0), event('y', 'a', 2)],
                  ValueError, 'invalid transition'),
                 ([event('x', 'a', 0), event('y', 'a', 1),
                   event('z', 'a', 2), event('w', 'a', 0)],
                  ValueError, 'invalid transition'),
                 ([event('x', 'a', True)], ValueError, 'invalid row')]
        for api in (run_many, render_many):
            for rows, error_type, message in cases:
                batches = [[event('ok', 'b', 0)], rows, None]
                before = copy.deepcopy(batches)
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(error_type, '^workflow-state: ' + message + '$'):
                        api(batches)
                    self.assertEqual(batches, before)

    def test_batch_compute_once_in_encounter_order(self) -> None:
        rows = [event('x', 'a', 0)]
        batches = [rows, [], rows]
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, member in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], member)

    def test_batch_failure_is_atomic_and_stops_processing(self) -> None:
        batches = [[event('first', 'a', 0)], [event('bad', 'a', 2)],
                   [event('last', 'a', 0)]]
        for api in (run_many, render_many):
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, before)

    def test_batch_fresh_results_and_no_mutation(self) -> None:
        rows = [event(' X ', ' A ', 0)]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first, second = run_many(batches), run_many(batches)
        for index, result in enumerate(first):
            self.assertIsNot(result, second[index])
            self.assertIsNot(result['states'], second[index]['states'])
            for other in first[index + 1:]:
                self.assertIsNot(result, other)
                self.assertIsNot(result['states'], other['states'])
        first[0]['states']['a'] = 2
        first[2]['states']['added'] = 0
        self.assertEqual(first[1], {'states': {'a': 0}})
        self.assertEqual(first[3], {'states': {}})
        self.assertEqual(second, run_many(batches))
        render_many(batches)
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
