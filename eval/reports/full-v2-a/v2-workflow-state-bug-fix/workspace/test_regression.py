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
        rows = [event(' A ', ' Straße / X ', 0),
                event('a', 'STRASSE / X', 0),
                event('b', 'strasse / x', 0),
                event('c', 'strasse / x', 1),
                event('d', 'strasse / x', 2),
                event('e', 'strasse / x', 2)]
        expected = {'states': {'strasse / x': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'states': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        with self.assertRaisesRegex(ValueError, '^workflow-state: duplicate id$'):
            run(rows + [event('A', 'another', 0)])

    def test_validation_is_structural_only(self) -> None:
        rows = [event(' A ', ' X /  Y ', 10 ** 100), event('a', 'z', -1)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [event('a', 'x /  y', 10 ** 100),
                                     event('a', 'z', -1)])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize('  Straße /  É  '), 'strasse /  é')

    def test_structure_precedes_selection_and_domain(self) -> None:
        for prefix in ([event('a', 'x', 0), event('a', 'y', 0)],
                       [event('a', 'x', 7)], [event('a', 'x', 1)]):
            for api in (run, render, engine.compute):
                with self.subTest(api=api, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                        api(prefix + [event('bad', ' ', 0)])

    def test_row_types(self) -> None:
        class IntSubclass(int):
            pass

        class StringSubclass(str):
            pass

        class DictSubclass(dict):
            pass

        class ListSubclass(list):
            pass

        self.assertEqual(run(ListSubclass([DictSubclass(event(
            StringSubclass(' A '), StringSubclass(' X '), 0))])),
            {'states': {'x': 0}})
        for rows in (None, (), {}, 'rows'):
            with self.assertRaisesRegex(TypeError, '^workflow-state: rows must be a list$'):
                run(rows)
        for row in (None, [], {}, event('', 'x', 0), event('a', 1, 0),
                    event('a', 'x', True), event('a', 'x', IntSubclass(0)),
                    dict(event('a', 'x', 0), extra=1)):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                    run([row])

    def test_state_and_transition_errors(self) -> None:
        for codes in ([1], [2], [0, 2], [0, 1, 0], [0, 1, 2, 1]):
            with self.subTest(codes=codes):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    run([event(str(i), 'x', code) for i, code in enumerate(codes)])
        for value in (-1, 3, 10 ** 100):
            with self.assertRaisesRegex(ValueError, '^workflow-state: invalid state$'):
                run([event('a', 'x', 1), event('b', 'x', value)])

    def test_order_and_json(self) -> None:
        rows = [event('a', ' Z ', 0), event('b', ' É ', 0), event('c', 'A', 0)]
        result = run(rows)
        self.assertEqual(list(result['states']), ['a', 'z', 'é'])
        self.assertEqual(render(rows), '{"states":{"a":0,"z":0,"é":0}}\n')
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'states': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_freshness_and_input_preservation(self) -> None:
        rows = [event(' A ', ' X ', 0)]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['states']['x'] = 2
        self.assertEqual(results[1], {'states': {'x': 0}})
        self.assertEqual(run(rows), {'states': {'x': 0}})
        self.assertEqual(rows, before)
        bad = rows + [event('b', 'x', 2)]
        nested = bad + [{'id': 'c', 'target': 'x', 'value': {'nested': []}}]
        for member in (bad, nested):
            batches = [rows, member, rows]
            snapshot = copy.deepcopy(batches)
            for api in (run_many, render_many):
                with self.assertRaises(ValueError):
                    api(batches)
                self.assertEqual(batches, snapshot)

    def test_shared_compute_and_batch_failure_order(self) -> None:
        rows = [event('a', 'x', 0)]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
        for api in (run_many, render_many):
            for outer in (None, (), {}):
                with self.assertRaisesRegex(TypeError, '^workflow-state: batches must be a list$'):
                    api(outer)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    api([rows, [event('b', 'x', 1)], None])
                self.assertEqual(compute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
