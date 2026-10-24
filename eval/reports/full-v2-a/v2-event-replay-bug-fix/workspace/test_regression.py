import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' First ', 'target': ' Straße / A ', 'value': 5},
            {'id': 'FIRST', 'target': 'STRASSE / A', 'value': 5},
            {'id': 'second', 'target': 'strasse / a', 'value': -5},
            {'id': 'third', 'target': ' Z ', 'value': 2},
        ]
        expected = {'balances': {'strasse / a': 0, 'z': 2}, 'history': [5, 0, 2]}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['balances']), ['strasse / a', 'z'])
        self.assertEqual(run_many([rows, []]), [expected, {'balances': {}, 'history': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
            run([{'id': 'a', 'target': 'x', 'value': -1},
                 {'id': 'b', 'target': 'x', 'value': 1}])
        with self.assertRaisesRegex(ValueError, '^event-replay: duplicate id$'):
            run(rows + [{'id': 'first', 'target': 'z', 'value': 5}])

    def test_structural_validation_and_precedence(self) -> None:
        class Integer(int):
            pass

        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        valid = Row(id=Text(' A '), target=Text(' B '), value=10 ** 100)
        self.assertEqual(run(Rows([valid]))['history'], [10 ** 100])
        for invalid in [None, [], {}, {'id': '', 'target': 'x', 'value': 1},
                        {'id': 'a', 'target': '  ', 'value': 1},
                        {'id': 1, 'target': 'x', 'value': 1},
                        {'id': 'a', 'target': 'x', 'value': True},
                        {'id': 'a', 'target': 'x', 'value': Integer(1)},
                        {'id': 'a', 'target': 'x', 'value': 1, 'extra': []}]:
            for prefix in [[], [{'id': 'a', 'target': 'x', 'value': -1}],
                           [{'id': 'a', 'target': 'x', 'value': 1},
                            {'id': 'a', 'target': 'x', 'value': 2}]]:
                with self.subTest(invalid=invalid, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^event-replay: invalid row$'):
                        run(prefix + [invalid])
        for api in [run, render, engine.compute, validation.validate]:
            with self.assertRaisesRegex(TypeError, '^event-replay: rows must be a list$'):
                api(())
        rows = [{'id': ' A ', 'target': ' X ', 'value': -1},
                {'id': 'a', 'target': 'y', 'value': 2}]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'a', 'target': 'x', 'value': -1},
                                     {'id': 'a', 'target': 'y', 'value': 2}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize('  Straße / X  Y  '), 'strasse / x  y')

    def test_fresh_outputs_and_serialization(self) -> None:
        rows = [{'id': 'a', 'target': ' Ω ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['balances']['ω'] = 99
        results[0]['history'].append(99)
        expected = {'balances': {'ω': 1}, 'history': [1]}
        self.assertEqual(results[1], expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(rows, before)
        self.assertEqual(render(rows), json.dumps(expected, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')) + '\n')
        self.assertEqual(run([]), {'balances': {}, 'history': []})
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_batch_atomicity_and_dynamic_engine(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        bad = [{'id': 'b', 'target': 'x', 'value': -1}]
        batches = [rows, bad, [{'extra': {'nested': []}}]]
        before = copy.deepcopy(batches)
        for api in [run_many, render_many]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^event-replay: negative prefix$'):
                    api(batches)
                self.assertEqual(compute.call_args_list, [unittest.mock.call(rows),
                                                         unittest.mock.call(bad)])
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^event-replay: batches must be a list$'):
                api(())
        for api, argument, count in [(run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)


if __name__ == '__main__':
    unittest.main()
