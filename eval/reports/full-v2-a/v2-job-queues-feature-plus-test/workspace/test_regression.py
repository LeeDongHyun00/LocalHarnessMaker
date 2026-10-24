import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': 'old', 'value': -10},
            {'id': 'a', 'target': ' Q ', 'value': 5},
            {'id': 'z', 'target': 'q', 'value': 5},
            {'id': 'z', 'target': 'ignored', 'value': 4},
            {'id': 'a', 'target': 'q', 'value': 5},
            {'id': 'last', 'target': 'q', 'value': -2},
            {'id': 'other', 'target': ' B ', 'value': 10**100},
        ]
        expected = {'queues': {'b': ['other'], 'q': ['z', 'a', 'last']}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['queues']), ['b', 'q'])
        self.assertEqual(run_many([rows, []]), [expected, {'queues': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_serialization(self) -> None:
        rows = [{'id': ' Straße / A  B ', 'target': ' Ω / Q ', 'value': -10**100}]
        expected = {'queues': {'ω / q': ['strasse / a  b']}}
        self.assertEqual(policy.normalize(' Straße / A  B '), 'strasse / a  b')
        self.assertEqual(validation.validate(rows), [
            {'id': 'strasse / a  b', 'target': 'ω / q', 'value': -10**100}])
        self.assertEqual(engine.compute(rows), expected)
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows, rows]), encoded * 2)

    def test_validation_precedes_ambiguity(self) -> None:
        rows = [{'id': 'x', 'target': 'a', 'value': 1},
                {'id': ' X ', 'target': 'b', 'value': 1}]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (run, render, engine.compute):
            with self.subTest(api=api.__name__):
                with self.assertRaisesRegex(ValueError, '^job-queues: ambiguous id$'):
                    api(rows + [{'id': 'x', 'target': 'b', 'value': 2}])
                with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                    api(rows + [{'id': 'bad', 'target': 'a', 'value': True}])

    def test_invalid_inputs_and_exact_value_type(self) -> None:
        class Integer(int):
            pass

        malformed = [None, [], {},
                     {'id': 'x', 'target': 'q', 'value': 1, 'extra': 0},
                     {'id': ' ', 'target': 'q', 'value': 1},
                     {'id': 'x', 'target': '\t', 'value': 1},
                     {'id': 1, 'target': 'q', 'value': 1},
                     {'id': 'x', 'target': 1, 'value': 1}]
        malformed += [{'id': 'x', 'target': 'q', 'value': value}
                      for value in (True, Integer(2), 1.0, '1', None)]
        for api in (validation.validate, engine.compute, run, render):
            for outer in (None, (), {}, 'rows'):
                with self.subTest(api=api.__name__, outer=outer):
                    with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                        api(outer)
            for row in malformed:
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                        api([row])

    def test_container_and_string_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' X '), target=Text(' Q '), value=0)])
        self.assertEqual(run_many(Rows([rows])), [{'queues': {'q': ['x']}}])
        self.assertEqual(render_many(Rows([rows])), '{"queues":{"q":["x"]}}\n')

    def test_empty_and_outer_validation(self) -> None:
        self.assertEqual(run([]), {'queues': {}})
        self.assertEqual(render([]), '{"queues":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for outer in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^job-queues: batches must be a list$'):
                    api(outer)

    def test_independent_outputs_and_input_preservation(self) -> None:
        rows = [{'id': ' X ', 'target': ' Q ', 'value': 2}]
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        outputs = run_many([rows, rows])
        outputs[0]['queues']['q'].append('changed')
        outputs[0]['queues']['extra'] = []
        self.assertEqual(outputs[1], {'queues': {'q': ['x']}})
        self.assertEqual(run(rows), outputs[1])
        self.assertEqual(rows, before)
        bad = rows + [{'id': 'x', 'target': 'q', 'value': {'nested': []}}]
        batches = [rows, bad, rows]
        snapshot = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                api(batches)
            self.assertEqual(batches, snapshot)

    def test_dynamic_engine_delegation(self) -> None:
        rows = [{'id': 'x', 'target': 'q', 'value': 1}]
        compute = engine.compute
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=compute) as observed:
                    api(argument)
                    self.assertEqual(observed.call_count, count)
                    for call in observed.call_args_list:
                        self.assertIs(call.args[0], rows)

    def test_batch_failure_order_and_exact_exception(self) -> None:
        good = [{'id': 'x', 'target': 'q', 'value': 1}]
        ambiguous = good + [{'id': 'x', 'target': 'other', 'value': 1}]
        compute = engine.compute
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=compute) as observed:
                with self.assertRaisesRegex(ValueError, '^job-queues: ambiguous id$'):
                    api([good, ambiguous, None])
                self.assertEqual(observed.call_count, 2)
            error = RuntimeError('instrumented failure')
            with patch.object(engine, 'compute', side_effect=error) as observed:
                with self.assertRaises(RuntimeError) as raised:
                    api([good, None])
                self.assertIs(raised.exception, error)
                self.assertEqual(observed.call_count, 1)


if __name__ == '__main__':
    unittest.main()
