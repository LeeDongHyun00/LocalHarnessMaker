import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'old', 'value': -1},
            {'id': 'b', 'target': 'Doc', 'value': 20},
            {'id': 'a', 'target': ' DOC ', 'value': 30},
            {'id': 'A', 'target': 'doc', 'value': 5},
            {'id': 'c', 'target': 'Another', 'value': 0},
        ]
        expected = {
            'patches': {'another': ['c'], 'doc': ['b', 'a']},
            'offsets': {'another': [0], 'doc': [20, 5]},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['patches']), ['another', 'doc'])
        self.assertEqual(run_many([rows, []]), [expected, {'patches': {}, 'offsets': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_structural_validation_precedes_domain_rules(self) -> None:
        for rows in (
            [{'id': 'a', 'target': 'd', 'value': -1}],
            [{'id': 'a', 'target': 'd', 'value': 1},
             {'id': 'A', 'target': 'e', 'value': 2}],
            [{'id': 'a', 'target': 'd', 'value': 1},
             {'id': 'b', 'target': 'd', 'value': 1}],
        ):
            rows.append({'id': 'bad', 'target': 'd', 'value': True})
            for api in (run, render, engine.compute):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(ValueError, '^document-patches: invalid row$'):
                        api(rows)

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([
            Row(id=Text('  Straße / A  B '), target=Text(' Ω / 文  件 '), value=-2),
            Row(id='STRASSE / A  B', target=' elsewhere ', value=10 ** 100),
        ])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'strasse / a  b', 'target': 'ω / 文  件', 'value': -2},
            {'id': 'strasse / a  b', 'target': 'elsewhere', 'value': 10 ** 100},
        ])
        self.assertIsNot(canonical, rows)
        self.assertTrue(all(a is not b for a, b in zip(canonical, rows)))
        self.assertEqual(policy.normalize(Text('  Straße / A  B ')), 'strasse / a  b')
        expected = {'patches': {'elsewhere': ['strasse / a  b']},
                    'offsets': {'elsewhere': [10 ** 100]}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(json.loads(render(rows)), expected)

    def test_malformed_rows(self) -> None:
        class Integer(int):
            pass

        bad_rows = [None, [], {},
                    {'id': 'a', 'target': 'd', 'value': 1, 'extra': 0}]
        for field, values in (
            ('id', ['', ' \t ', 1, None]),
            ('target', ['', '\n', 1, None]),
            ('value', [True, Integer(1), 1.0, '1', None]),
        ):
            for value in values:
                row = {'id': 'a', 'target': 'd', 'value': 1}
                row[field] = value
                bad_rows.append(row)
        for row in bad_rows:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, '^document-patches: invalid row$'):
                    run([row])
        for api in (run, render, engine.compute, validation.validate):
            for rows in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^document-patches: rows must be a list$'):
                    api(rows)

    def test_negative_precedes_collision_and_obsolete_collision_is_ignored(self) -> None:
        rows = [{'id': 'a', 'target': 'd', 'value': 1},
                {'id': 'b', 'target': 'd', 'value': 1}]
        with self.assertRaisesRegex(ValueError, '^document-patches: collision$'):
            run(rows)
        with self.assertRaisesRegex(ValueError, '^document-patches: negative offset$'):
            run(rows + [{'id': 'c', 'target': 'e', 'value': -1}])
        self.assertEqual(run(rows + [{'id': 'b', 'target': 'e', 'value': 0}]),
                         {'patches': {'d': ['a'], 'e': ['b']},
                          'offsets': {'d': [1], 'e': [0]}})

    def test_first_occurrence_position_is_preserved(self) -> None:
        rows = [{'id': 'a', 'target': 'old', 'value': 9},
                {'id': 'b', 'target': 'd', 'value': 2},
                {'id': 'A', 'target': 'new', 'value': 0}]
        with patch.object(engine, 'resolve', wraps=engine.resolve) as resolve:
            run(rows)
        self.assertEqual(resolve.call_args.args[0], [
            {'id': 'a', 'target': 'new', 'value': 0},
            {'id': 'b', 'target': 'd', 'value': 2},
        ])

    def test_fresh_outputs_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' A ', 'target': ' D ', 'value': 2}]
        batches = [rows, rows]
        before = copy.deepcopy(batches)
        outputs = run_many(batches)
        outputs[0]['patches']['d'].append('changed')
        outputs[0]['offsets']['d'].clear()
        self.assertEqual(outputs[1], run(rows))
        self.assertEqual(batches, before)
        invalid_batches = [rows, rows + [{'id': 'b', 'target': 'd', 'value': -1}]]
        before = copy.deepcopy(invalid_batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^document-patches: negative offset$'):
                api(invalid_batches)
            self.assertEqual(invalid_batches, before)
        empties = run_many([[], []])
        empties[0]['patches']['new'] = []
        self.assertEqual(empties[1], {'patches': {}, 'offsets': {}})

    def test_render_format_and_empty_inputs(self) -> None:
        rows = [{'id': ' Ω ', 'target': ' 文 ', 'value': 2}]
        self.assertEqual(render(rows), '{"offsets":{"文":[2]},"patches":{"文":["ω"]}}\n')
        self.assertEqual(render(rows), json.dumps(run(rows), ensure_ascii=False,
                                               sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'patches': {}, 'offsets': {}})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for api in (run_many, render_many):
            for batches in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^document-patches: batches must be a list$'):
                    api(batches)

    def test_dynamic_compute_dispatch_and_batch_atomicity(self) -> None:
        rows = [{'id': 'a', 'target': 'd', 'value': 1}]
        for api, argument, count in (
            (run, rows, 1), (render, rows, 1),
            (run_many, [rows, []], 2), (render_many, [rows, []], 2),
        ):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
            self.assertEqual(compute.call_count, count)
        failure = [{'id': 'b', 'target': 'd', 'value': -1}]
        for api in (run_many, render_many):
            batches = [rows, failure, None]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^document-patches: negative offset$'):
                    api(batches)
            self.assertEqual(compute.call_args_list, [unittest.mock.call(rows),
                                                       unittest.mock.call(failure)])
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
