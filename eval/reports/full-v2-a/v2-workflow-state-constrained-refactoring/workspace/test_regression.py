import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def event(event_id: str, target: str, value: int) -> dict:
    return {'id': event_id, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def assert_public_error(self, rows, error_type, message) -> None:
        before = copy.deepcopy(rows)
        for api, argument in ((run, rows), (render, rows),
                              (engine.compute, rows),
                              (run_many, [rows]), (render_many, [rows])):
            with self.subTest(api=api.__name__):
                with self.assertRaises(error_type) as caught:
                    api(argument)
                self.assertEqual(str(caught.exception), 'workflow-state: ' + message)
                self.assertEqual(rows, before)

    def test_domain_edge(self) -> None:
        rows = [event(' First ', ' Straße / A B ', 0),
                event('FIRST', 'STRASSE / A B', 0),
                event('second', 'strasse / a b', 1),
                event('third', 'strasse / a b', 1),
                event('fourth', 'strasse / a b', 2)]
        before = copy.deepcopy(rows)
        expected = {'states': {'strasse / a b': 2}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'states': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        self.assertEqual(rows, before)
        self.assert_public_error(rows + [event('FIRST', 'other', 0)],
                                 ValueError, 'duplicate id')
        self.assert_public_error(rows + [event('fifth', 'strasse / a b', 0)],
                                 ValueError, 'invalid transition')

    def test_validation_precedence_and_canonical_rows(self) -> None:
        rows = [event(' A ', ' X ', 8), event('a', 'y', 0)]
        self.assertEqual(validation.validate(rows),
                         [event('a', 'x', 8), event('a', 'y', 0)])
        self.assert_public_error(rows, ValueError, 'duplicate id')
        self.assert_public_error(rows + [{'id': 'bad'}], ValueError, 'invalid row')
        self.assert_public_error([event('a', 'x', 1), event('b', 'x', 9)],
                                 ValueError, 'invalid state')
        self.assert_public_error([event('a', 'x', 9), {'value': 0}],
                                 ValueError, 'invalid row')
        canonical = validation.validate(rows)
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows[0]['target'], ' X ')

    def test_structural_types(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        rows = ListSubclass([DictSubclass(event(StringSubclass(' A '),
                                               StringSubclass(' X '), 0))])
        self.assertEqual(run(rows), {'states': {'x': 0}})
        for bad in (None, (), {}, 'rows'):
            self.assert_public_error(bad, TypeError, 'rows must be a list')
        for bad in (None, [], {}, event('', 'x', 0), event('a', '  ', 0),
                    event(3, 'x', 0), event('a', None, 0),
                    event('a', 'x', True), event('a', 'x', IntSubclass(0)),
                    event('a', 'x', 0.0), dict(event('a', 'x', 0), extra=1)):
            self.assert_public_error([bad], ValueError, 'invalid row')
        huge = 10 ** 100
        self.assertEqual(validation.validate([event('a', 'x', huge)])[0]['value'], huge)
        self.assert_public_error([event('a', 'x', huge)], ValueError, 'invalid state')

    def test_transitions(self) -> None:
        for codes in ([1], [2], [0, 2], [0, 1, 0], [0, 1, 2, 1]):
            self.assert_public_error([event(str(i), 'x', v) for i, v in enumerate(codes)],
                                     ValueError, 'invalid transition')
        for codes in ([0], [0, 0], [0, 1, 1], [0, 1, 2, 2]):
            self.assertEqual(run([event(str(i), 'x', v) for i, v in enumerate(codes)]),
                             {'states': {'x': codes[-1]}})

    def test_serialization_order_and_empty(self) -> None:
        rows = [event('a', ' Z / X Y ', 0), event('b', ' É ', 0)]
        result = run(rows)
        self.assertEqual(list(result), ['states'])
        self.assertEqual(list(result['states']), ['z / x y', 'é'])
        self.assertEqual(policy.normalize(' Straße / A B '), 'strasse / a b')
        self.assertEqual(render(rows), '{"states":{"z / x y":0,"é":0}}\n')
        self.assertEqual(render(rows), json.dumps(result, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'states': {}})
        self.assertEqual(render([]), '{"states":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_output_independence(self) -> None:
        rows = [event('a', 'x', 0)]
        before = copy.deepcopy(rows)
        batch = run_many([rows, rows])
        single = run(rows)
        batch[0]['states']['x'] = 99
        self.assertEqual(batch[1], {'states': {'x': 0}})
        self.assertEqual(single, {'states': {'x': 0}})
        self.assertEqual(run(rows), single)
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['states']['new'] = 1
        self.assertEqual(empty[1], {'states': {}})

    def test_batch_errors_are_sequential_and_atomic(self) -> None:
        for api in (run_many, render_many):
            for bad in (None, (), {}, 'batches'):
                with self.assertRaises(TypeError) as caught:
                    api(bad)
                self.assertEqual(str(caught.exception),
                                 'workflow-state: batches must be a list')
            batches = [[event('a', 'x', 0)], [event('b', 'y', 1)], None]
            before = copy.deepcopy(batches)
            original = engine.compute
            with patch.object(engine, 'compute', wraps=original) as compute:
                with self.assertRaises(ValueError) as caught:
                    api(batches)
                self.assertEqual(str(caught.exception), 'workflow-state: invalid transition')
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, before)

    def test_runtime_compute_lookup(self) -> None:
        rows = [event('a', 'x', 0)]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', return_value={'states': {'probe': 2}}) as compute:
                    result = api(argument)
                    self.assertEqual(compute.call_count, count)
                    if api is run:
                        self.assertEqual(result, {'states': {'probe': 2}})
                    elif api is render:
                        self.assertEqual(result, '{"states":{"probe":2}}\n')
                    elif api is run_many:
                        self.assertEqual(result, [{'states': {'probe': 2}}] * 2)
                    else:
                        self.assertEqual(result, '{"states":{"probe":2}}\n' * 2)


if __name__ == '__main__':
    unittest.main()
