import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Queue/B ', 'value': -2},
            {'id': 'A', 'target': 'queue/b', 'value': -2},
            {'id': 'z', 'target': 'QUEUE/B', 'value': -2},
            {'id': ' Top ', 'target': 'queue/b', 'value': 10**100},
            {'id': ' Straße ', 'target': ' Ä / Q ', 'value': -(10**100)},
            {'id': ' Other ', 'target': ' A A ', 'value': 0},
        ]
        expected = {'queues': {
            'a a': ['other'], 'queue/b': ['top', 'z', 'a'], 'ä / q': ['strasse'],
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['queues']), list(expected['queues']))
        self.assertEqual(run_many([rows, []]), [expected, {'queues': {}}])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, []]), encoded + '{"queues":{}}\n')

    def test_validation_precedes_selection(self) -> None:
        rows = [
            {'id': 'x', 'target': 'q', 'value': 1},
            {'id': ' X ', 'target': 'q', 'value': 2},
        ]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (run, render, engine.compute):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^job-queues: duplicate id$'):
                    api(rows)
                with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                    api(rows + [{'id': 'bad', 'target': 'q', 'value': True}])

    def test_structural_contract(self) -> None:
        class IntSubclass(int):
            pass

        invalid = [None, [], {}, {'id': 'x', 'target': 'q', 'value': 1, 'extra': 0}]
        invalid += [{'id': ident, 'target': target, 'value': value} for ident, target, value in (
            (' ', 'q', 1), ('x', '\t', 1), (1, 'q', 1), ('x', None, 1),
            ('x', 'q', True), ('x', 'q', IntSubclass(1)), ('x', 'q', 1.0),
        )]
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'x'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                        api(rows)
            for row in invalid:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                        api([row])

    def test_subclasses_and_canonical_copies(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        rows = ListSubclass([DictSubclass(id=StrSubclass(' Straße '), target=StrSubclass(' Q / X '), value=0)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'strasse', 'target': 'q / x', 'value': 0}])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Ä  / STRAẞE '), 'ä  / strasse')
        self.assertEqual(run_many(ListSubclass([rows])), [{'queues': {'q / x': ['strasse']}}])

    def test_outputs_are_independent(self) -> None:
        rows = [{'id': ' X ', 'target': ' Q ', 'value': 1}]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['queues']['q'].append('changed')
        self.assertEqual(outputs[1], {'queues': {'q': ['x']}})
        self.assertEqual(run(rows), outputs[1])
        self.assertEqual(rows, before)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        empty = run_many([[], []])
        empty[0]['queues']['new'] = []
        self.assertEqual(empty[1], {'queues': {}})

    def test_batch_contract_and_failure_order(self) -> None:
        good = [{'id': 'x', 'target': 'q', 'value': 0}]
        duplicate = good + [{'id': 'x', 'target': 'q', 'value': 1}]
        malformed = [{'id': 'bad', 'target': 'q', 'value': {'nested': []}}]
        for api in (run_many, render_many):
            for outer in (None, (), {}, ''):
                with self.assertRaisesRegex(TypeError, '^job-queues: batches must be a list$'):
                    api(outer)
            for bad, message in ((duplicate, 'duplicate id'), (malformed, 'invalid row'), (None, 'rows must be a list')):
                batches = [good, bad, malformed]
                before = copy.deepcopy(batches)
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    with self.assertRaisesRegex((TypeError, ValueError), '^job-queues: ' + message + '$'):
                        api(batches)
                    self.assertEqual(compute.call_count, 2)
                    self.assertIs(compute.call_args_list[0].args[0], good)
                    self.assertIs(compute.call_args_list[1].args[0], bad)
                self.assertEqual(batches, before)

    def test_runtime_compute_lookup(self) -> None:
        rows = [{'id': 'x', 'target': 'q', 'value': 1}]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2), (render_many, [rows, rows], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', return_value={'queues': {'instrumented': []}}) as compute:
                    result = api(argument)
                    self.assertEqual(compute.call_count, count)
                    for call in compute.call_args_list:
                        self.assertIs(call.args[0], rows)
                    self.assertIn('instrumented', str(result))

    def test_empty_inputs(self) -> None:
        self.assertEqual(engine.compute([]), {'queues': {}})
        self.assertEqual(run([]), {'queues': {}})
        self.assertEqual(render([]), '{"queues":{}}\n')
        self.assertEqual(validation.validate([]), [])
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
