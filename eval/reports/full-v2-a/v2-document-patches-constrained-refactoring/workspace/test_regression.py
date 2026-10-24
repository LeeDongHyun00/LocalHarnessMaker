import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Late ', 'target': ' Straße/文 件 ', 'value': 10**100},
            {'id': 'early', 'target': 'STRASSE/文 件', 'value': 0},
            {'id': 'LATE', 'target': 'strasse/文 件', 'value': 10**100},
            {'id': 'other', 'target': ' A ', 'value': 2},
        ]
        expected = {
            'patches': {'a': ['other'], 'strasse/文 件': ['late', 'early']},
            'offsets': {'a': [2], 'strasse/文 件': [10**100, 0]},
        }
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'patches': {}, 'offsets': {}}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"offsets":{},"patches":{}}\n')
        self.assertEqual(list(run(rows)), ['patches', 'offsets'])
        self.assertEqual(list(run(rows)['patches']), ['a', 'strasse/文 件'])

    def test_validation_and_normalization(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        rows = Rows([Row(id=Text(' STRAẞE '), target=Text(' A / 文  件 '), value=-1)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'strasse', 'target': 'a / 文  件', 'value': -1}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' A / 文  件 ')), 'a / 文  件')
        malformed = [None, [], {}, {'id': 'x', 'target': 'a', 'value': 1, 'extra': {}},
                     {'id': ' ', 'target': 'a', 'value': 1},
                     {'id': 1, 'target': 'a', 'value': 1},
                     {'id': 'x', 'target': '\t', 'value': 1},
                     {'id': 'x', 'target': None, 'value': 1}]
        malformed.extend({'id': 'x', 'target': 'a', 'value': value}
                         for value in (True, Integer(1), 1.0, '1', None))
        for row in malformed:
            with self.subTest(row=row):
                before = copy.deepcopy(row)
                with self.assertRaisesRegex(ValueError, '^document-patches: invalid row$'):
                    validation.validate([row])
                self.assertEqual(row, before)
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^document-patches: rows must be a list$'):
                api(())

    def test_error_precedence_and_immutability(self) -> None:
        base = {'id': 'x', 'target': 'a', 'value': 1}
        duplicate = {'id': 'X', 'target': 'b', 'value': 1}
        negative = {'id': 'negative', 'target': 'a', 'value': -1}
        collision = {'id': 'other', 'target': 'A', 'value': 1}
        invalid = {'id': 'bad', 'target': 'a', 'value': {'nested': []}}
        cases = [([base, duplicate, invalid], 'invalid row'),
                 ([negative, invalid], 'invalid row'),
                 ([base, collision, invalid], 'invalid row'),
                 ([base, duplicate], 'duplicate id'),
                 ([base, collision, negative], 'negative offset'),
                 ([base, collision], 'collision')]
        for rows, message in cases:
            for api in (run, render, engine.compute,
                        lambda value: run_many([value]),
                        lambda value: render_many([value])):
                with self.subTest(rows=rows, api=api):
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, '^document-patches: ' + message + '$'):
                        api(rows)
                    self.assertEqual(rows, before)
        self.assertEqual(validation.validate([base, duplicate]), [base, {'id': 'x', 'target': 'b', 'value': 1}])

    def test_fresh_outputs(self) -> None:
        rows = [{'id': ' X ', 'target': ' A ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['patches']['a'].append('changed')
        results[0]['offsets']['a'].clear()
        results[0]['patches']['new'] = []
        self.assertEqual(results[1], run(rows))
        self.assertEqual(rows, before)
        canonical = validation.validate(rows + rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(canonical[1]['id'], 'x')
        empty = run_many([[], []])
        empty[0]['patches']['changed'] = []
        self.assertEqual(empty[1], {'patches': {}, 'offsets': {}})
        self.assertEqual(run([]), {'patches': {}, 'offsets': {}})

    def test_compute_is_resolved_at_call_time(self) -> None:
        rows = [{'id': 'x', 'target': 'a', 'value': 1}]
        original = engine.compute
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, [], rows], 3),
                                     (render_many, [rows, [], rows], 3)):
            with self.subTest(api=api), patch.object(engine, 'compute', wraps=original) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                self.assertEqual([call.args[0] for call in compute.call_args_list],
                                 [rows] if count == 1 else [rows, [], rows])

    def test_batch_atomicity_and_order(self) -> None:
        good = [{'id': 'x', 'target': 'a', 'value': 1}]
        bad = [{'id': 'x', 'target': 'a', 'value': -1}]
        later = [{'id': 'invalid'}]
        for api in (run_many, render_many):
            batches = [good, bad, later]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^document-patches: negative offset$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^document-patches: batches must be a list$'):
                api(())
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')


if __name__ == '__main__':
    unittest.main()
