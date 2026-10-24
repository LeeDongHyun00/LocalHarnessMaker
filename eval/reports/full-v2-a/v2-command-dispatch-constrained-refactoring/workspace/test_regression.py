import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': ' Build/ Straße ', 'value': -4},
            {'id': 'a', 'target': 'build/ strasse', 'value': -4},
            {'id': 'z', 'target': 'BUILD/ STRASSE', 'value': -4},
            {'id': 'higher', 'target': 'other', 'value': 10 ** 100},
            {'id': 'lower', 'target': 'other', 'value': -10 ** 100},
        ]
        expected = {
            'dispatch': {'build/ strasse': 'z', 'other': 'higher'},
            'shadowed': ['a', 'lower'],
        }
        before = copy.deepcopy(rows)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dispatch': {}, 'shadowed': []}])
        serialized = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), serialized)
        self.assertEqual(render_many([rows, []]), serialized + '{"dispatch":{},"shadowed":[]}\n')
        self.assertEqual(rows, before)
        self.assertEqual(list(run(rows)), ['dispatch', 'shadowed'])
        self.assertEqual(list(run(rows)['dispatch']), ['build/ strasse', 'other'])

    def test_validation_and_normalization(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' B '), target=Text(' X / Straße '), value=-1),
                     Row(id='b', target='different', value=2)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'b', 'target': 'x / strasse', 'value': -1},
                                     {'id': 'b', 'target': 'different', 'value': 2}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' X / Straße ')), 'x / strasse')
        with self.assertRaisesRegex(ValueError, '^command-dispatch: duplicate id$'):
            run(rows)

    def test_invalid_rows_and_precedence(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 2}]
        invalid += [{'id': i, 'target': t, 'value': v} for i, t, v in
                    [(' ', 'b', 1), ('a', '', 1), (1, 'b', 1), ('a', None, 1),
                     ('a', 'b', True), ('a', 'b', Integer(1)), ('a', 'b', 1.0)]]
        duplicate = [{'id': 'a', 'target': 'b', 'value': 1},
                     {'id': 'a', 'target': 'c', 'value': 1}]
        for bad in invalid:
            rows = duplicate + [bad]
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(bad=bad, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^command-dispatch: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^command-dispatch: rows must be a list$'):
                api(())

    def test_dynamic_compute_once_per_member(self) -> None:
        rows = [{'id': 'a', 'target': 'b', 'value': 1}]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, []], 2),
                                     (render_many, [rows, []], 2)):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_args_list, [unittest.mock.call(rows)] +
                                     ([unittest.mock.call([])] if count == 2 else []))

    def test_batch_atomic_failure_order(self) -> None:
        good = [{'id': 'ok', 'target': 'x', 'value': 0}]
        duplicate = [{'id': 'a', 'target': 'b', 'value': 1},
                     {'id': 'a', 'target': 'c', 'value': 1}]
        batches = [good, duplicate, [None]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^command-dispatch: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^command-dispatch: batches must be a list$'):
                api(())

    def test_fresh_results_and_empty_batches(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1},
                {'id': 'b', 'target': 'x', 'value': 0}]
        expected = {'dispatch': {'x': 'a'}, 'shadowed': ['b']}
        results = run_many([rows, rows])
        results[0]['dispatch']['x'] = 'changed'
        results[0]['shadowed'].append('changed')
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows[0], {'id': 'a', 'target': 'x', 'value': 1})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        empty = run_many([[], []])
        empty[0]['dispatch']['changed'] = 'changed'
        empty[0]['shadowed'].append('changed')
        self.assertEqual(empty[1], {'dispatch': {}, 'shadowed': []})


if __name__ == '__main__':
    unittest.main()
