import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(event: str, target: str, value: int) -> dict:
    return {'id': event, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' First ', 'obsolete', 10**100),
                row('next', ' FLOW/ Straße ', 1),
                row('FIRST', 'flow/ STRASSE', 0),
                row('close', 'flow/ strasse', 2)]
        expected = {'states': {'flow/ strasse': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'states': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_final_revision_can_lower_value(self) -> None:
        self.assertEqual(run([row('a', 'x', 2), row('b', 'x', 1),
                              row('a', 'x', 0)]), {'states': {'x': 1}})

    def test_transitions(self) -> None:
        self.assertEqual(run([row(str(i), 'x', value)
                              for i, value in enumerate([0, 0, 1, 1, 2, 2])]),
                         {'states': {'x': 2}})
        for values in ([1], [2], [0, 2], [0, 1, 0], [0, 1, 2, 0], [0, 1, 2, 1]):
            with self.subTest(values=values):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    run([row(str(i), 'x', value) for i, value in enumerate(values)])

    def test_state_errors_precede_transitions(self) -> None:
        for code in (-1, 3, 10**100):
            with self.subTest(code=code):
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid state$'):
                    run([row('a', 'x', 1), row('b', 'y', code)])

    def test_structural_errors_precede_domain(self) -> None:
        class IntSubclass(int):
            pass

        malformed = [{}, row('', 'x', 0), row('a', '  ', 0),
                     row('a', 'x', True), row('a', 'x', IntSubclass(0)),
                     row(1, 'x', 0), row('a', None, 0),
                     dict(row('a', 'x', 0), extra=1), ['a', 'x', 0],
                     row('a', 'x', {'nested': []})]
        for bad in malformed:
            rows = [row('a', 'x', 999), row('a', 'y', 1), bad]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(bad=bad, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^workflow-state: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_validation_preserves_all_revisions(self) -> None:
        rows = [row(' A ', ' X/Y  Z ', 10**100), row('a', 'other', -1)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('a', 'x/y  z', 10**100), row('a', 'other', -1)])
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows[0]['id'], ' A ')
        self.assertEqual(policy.normalize(' Straße/ Ω  X '), 'strasse/ ω  x')

    def test_subclasses_and_outer_types(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        rows = ListSubclass([DictSubclass(id=StrSubclass(' A '),
                                         target=StrSubclass(' X '), value=0)])
        self.assertEqual(run(rows), {'states': {'x': 0}})
        self.assertEqual(run_many(ListSubclass([rows])), [{'states': {'x': 0}}])
        for value in (None, (), {}, iter([]), 'rows'):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^workflow-state: rows must be a list$'):
                    api(value)
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^workflow-state: batches must be a list$'):
                    api(value)

    def test_serialization_and_sorted_states(self) -> None:
        rows = [row('a', 'Ω', 0), row('b', 'b', 0), row('c', 'A', 0)]
        result = run(rows)
        self.assertEqual(list(result['states']), ['a', 'b', 'ω'])
        self.assertEqual(render(rows), '{"states":{"a":0,"b":0,"ω":0}}\n')
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False,
                                                 sort_keys=True, separators=(',', ':')) + '\n')

    def test_empty_and_independent_results(self) -> None:
        self.assertEqual(run([]), {'states': {}})
        self.assertEqual(render([]), '{"states":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [row('a', 'x', 0)]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['states']['x'] = 2
        self.assertEqual(results[1], {'states': {'x': 0}})
        self.assertEqual(run(rows), {'states': {'x': 0}})
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['states']['new'] = 0
        self.assertEqual(empty[1], {'states': {}})

    def test_batch_failure_order_and_dynamic_compute(self) -> None:
        good = [row('a', 'x', 0)]
        bad = [row('b', 'y', 1)]
        later = [row('c', 'z', {'nested': []})]
        batches = [good, bad, later]
        before = copy.deepcopy(batches)
        original = engine.compute
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=original) as compute:
                with self.assertRaisesRegex(ValueError, '^workflow-state: invalid transition$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, before)
        for api, argument, count in ((run, good, 1), (render, good, 1),
                                     (run_many, [good, good], 2),
                                     (render_many, [good, good], 2)):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)


if __name__ == '__main__':
    unittest.main()
