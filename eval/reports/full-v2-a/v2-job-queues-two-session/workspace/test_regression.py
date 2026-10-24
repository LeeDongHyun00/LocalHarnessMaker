import copy
import json
import unittest
from unittest.mock import patch

from project import run, render, run_many, render_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z_ID ', 'target': ' B_Q ', 'value': 3},
            {'id': 'a', 'target': 'b-q', 'value': 3},
            {'id': 'z-id', 'target': 'b_q', 'value': 3},
            {'id': 'low', 'target': 'b-q', 'value': -5},
            {'id': 'high', 'target': 'b-q', 'value': 10**100},
            {'id': 'other', 'target': 'A', 'value': 0},
        ]
        result = run(rows)
        self.assertEqual(result, {'queues': {'a': ['other'], 'b-q': ['high', 'z-id', 'a', 'low']}})
        self.assertEqual(list(result['queues']), ['a', 'b-q'])

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Straße_/ A '), target=Text(' Q_/ X '), value=-(10**100))])
        canonical = validation.validate(rows)
        expected = {'id': 'strasse-/ a', 'target': 'q-/ x', 'value': -(10**100)}
        self.assertEqual(canonical, [expected])
        self.assertIsNot(canonical, rows)
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Straße_/ A '), 'strasse-/ a')
        for entry in (run, engine.compute):
            self.assertEqual(entry(rows), {'queues': {'q-/ x': ['strasse-/ a']}})
        self.assertEqual(json.loads(render(rows)), run(rows))
        duplicates = [{'id': ' X ', 'target': ' Q ', 'value': 1}, {'id': 'x', 'target': 'q', 'value': 2}]
        self.assertEqual(len(validation.validate(duplicates)), 2)

    def test_errors_and_validation_precedence(self) -> None:
        class Number(int):
            pass

        good = {'id': 'x', 'target': 'q', 'value': 1}
        bad_rows = [None, [], {}, dict(good, extra=0), dict(good, id=' '),
                    dict(good, target=0), dict(good, id=None), dict(good, target='\t'),
                    dict(good, value=True), dict(good, value=Number(1)),
                    dict(good, value=1.0)]
        for entry in (validation.validate, engine.compute, run, render):
            for rows in (None, (), {}, 'rows', iter([])):
                with self.subTest(entry=entry.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^job-queues: rows must be a list$'):
                        entry(rows)
            for row in bad_rows:
                with self.subTest(entry=entry.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                        entry([good, dict(good, value=2), row])
        for entry in (engine.compute, run, render):
            for conflicting in (dict(good, value=2), dict(good, target='other')):
                with self.assertRaisesRegex(ValueError, '^job-queues: duplicate id$'):
                    entry([good, conflicting])

    def test_no_mutation_and_independent_outputs(self) -> None:
        rows = [{'id': ' X ', 'target': ' Q ', 'value': 1}]
        before = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        first['queues']['q'].append('changed')
        self.assertEqual(second, {'queues': {'q': ['x']}})
        self.assertEqual(run(rows), second)
        self.assertEqual(rows, before)
        invalid = rows + [{'id': 'bad', 'target': 'q', 'value': {'nested': []}}]
        invalid_before = copy.deepcopy(invalid)
        for entry in (run, render):
            with self.assertRaises(ValueError):
                entry(invalid)
            self.assertEqual(invalid, invalid_before)
        conflicting = rows + [{'id': 'x', 'target': 'q', 'value': 2}]
        conflicting_before = copy.deepcopy(conflicting)
        with self.assertRaises(ValueError):
            run(conflicting)
        self.assertEqual(conflicting, conflicting_before)

    def test_empty_and_render(self) -> None:
        first = run([])
        second = run([])
        self.assertEqual(first, {'queues': {}})
        self.assertIsNot(first, second)
        self.assertIsNot(first['queues'], second['queues'])
        rows = [{'id': 'É_/ Z', 'target': '中文_/ Q', 'value': 0}]
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(render([]), '{"queues":{}}\n')

    def test_compute_resolved_at_call_time_once(self) -> None:
        rows = [{'id': 'x', 'target': 'q', 'value': 1}]
        for entry in (run, render):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                entry(rows)
                compute.assert_called_once_with(rows)
            with patch.object(engine, 'compute', side_effect=ValueError('job-queues: invalid row')) as compute:
                with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                    entry(rows)
                compute.assert_called_once_with(rows)

    def test_batch_outer_inputs_and_empty(self) -> None:
        class Batches(list):
            pass

        for entry in (run_many, render_many):
            for batches in (None, (), {}, 'batches', iter([]), 0):
                with self.subTest(entry=entry.__name__, batches=batches):
                    with patch.object(engine, 'compute') as compute:
                        with self.assertRaisesRegex(TypeError, '^job-queues: batches must be a list$'):
                            entry(batches)
                        compute.assert_not_called()
            for batches in ([], Batches()):
                with patch.object(engine, 'compute') as compute:
                    self.assertEqual(entry(batches), [] if entry is run_many else '')
                    compute.assert_not_called()
        rows = [{'id': ' X ', 'target': ' Q ', 'value': 1}]
        self.assertEqual(run_many(Batches([rows])), [run(rows)])
        self.assertEqual(render_many(Batches([rows])), render(rows))

    def test_batch_policies_and_render(self) -> None:
        batches = [
            [
                {'id': ' Z_ID ', 'target': ' B_Q ', 'value': 3},
                {'id': 'a', 'target': 'b-q', 'value': 3},
                {'id': 'z-id', 'target': 'b_q', 'value': 3},
                {'id': 'low', 'target': 'b-q', 'value': -(10**100)},
                {'id': 'high', 'target': 'b-q', 'value': 10**100},
                {'id': ' Straße_/ A ', 'target': ' 中文_/ Q ', 'value': 0},
                {'id': 'other', 'target': 'A', 'value': 0},
            ],
            [],
            [{'id': 'z-id', 'target': 'other', 'value': 99}],
        ]
        before = copy.deepcopy(batches)
        expected = [
            {'queues': {'a': ['other'], 'b-q': ['high', 'z-id', 'a', 'low'],
                        '中文-/ q': ['strasse-/ a']}},
            {'queues': {}},
            {'queues': {'other': ['z-id']}},
        ]
        results = run_many(batches)
        self.assertEqual(results, expected)
        self.assertEqual(list(results[0]['queues']), ['a', 'b-q', '中文-/ q'])
        rendered = render_many(batches)
        self.assertEqual(rendered, ''.join(render(rows) for rows in batches))
        self.assertEqual(rendered, ''.join(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for result in expected))
        self.assertEqual(batches, before)

    def test_batch_nested_results_are_independent(self) -> None:
        rows = [{'id': ' X ', 'target': ' Q ', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        self.assertIsNot(first[0], first[1])
        self.assertIsNot(first[0]['queues'], first[1]['queues'])
        self.assertIsNot(first[0]['queues']['q'], first[1]['queues']['q'])
        self.assertIsNot(first[2]['queues'], first[3]['queues'])
        first[0]['queues']['q'].append('changed')
        first[2]['queues']['new'] = []
        self.assertEqual(first[1], {'queues': {'q': ['x']}})
        self.assertEqual(first[3], {'queues': {}})
        self.assertEqual(second, run_many(batches))
        self.assertEqual(batches, before)

    def test_batch_errors_stop_at_first_member_without_mutation(self) -> None:
        good = {'id': ' X ', 'target': ' Q ', 'value': 1}
        duplicate = [good, dict(good, value=2)]
        invalid = duplicate + [dict(good, value={'nested': []})]
        cases = [(None, TypeError, 'rows must be a list'),
                 ((), TypeError, 'rows must be a list'),
                 (duplicate, ValueError, 'duplicate id'),
                 (invalid, ValueError, 'invalid row'),
                 ([dict(good, value=True)], ValueError, 'invalid row')]
        for entry in (run_many, render_many):
            for failing, error, message in cases:
                with self.subTest(entry=entry.__name__, message=message, failing=failing):
                    batches = [[good], failing, [None]]
                    before = copy.deepcopy(batches)
                    with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                        with self.assertRaisesRegex(error, '^job-queues: ' + message + '$'):
                            entry(batches)
                        self.assertEqual(compute.call_count, 2)
                        self.assertIs(compute.call_args_list[0].args[0], batches[0])
                        self.assertIs(compute.call_args_list[1].args[0], batches[1])
                    self.assertEqual(batches, before)

    def test_batch_compute_resolved_at_call_time_once_per_member(self) -> None:
        batches = [[], [{'id': 'x', 'target': 'q', 'value': 1}], []]
        for entry in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                entry(batches)
                self.assertEqual(compute.call_count, len(batches))
                for call, rows in zip(compute.call_args_list, batches):
                    self.assertIs(call.args[0], rows)
            with patch.object(engine, 'compute', side_effect=ValueError('job-queues: invalid row')) as compute:
                with self.assertRaisesRegex(ValueError, '^job-queues: invalid row$'):
                    entry(batches)
                compute.assert_called_once_with(batches[0])


if __name__ == '__main__':
    unittest.main()
