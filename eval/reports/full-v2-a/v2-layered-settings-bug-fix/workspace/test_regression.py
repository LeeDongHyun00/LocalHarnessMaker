import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Straße/A B ', 'value': -8},
            {'id': 'z', 'target': 'STRASSE/A B', 'value': -8},
            {'id': ' B ', 'target': 'STRASSE/A B', 'value': -2},
            {'id': ' A ', 'target': 'straße/a b', 'value': -2},
            {'id': 'other', 'target': ' Alpha ', 'value': -(10 ** 100)},
        ]
        expected = {'settings': {'alpha': 'other', 'strasse/a b': 'a'}}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['settings']), ['alpha', 'strasse/a b'])
        self.assertEqual(run_many([rows, []]), [expected, {'settings': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Ä / X '), target=Text(' Straße '), value=10 ** 100)])
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'ä / x', 'target': 'strasse', 'value': 10 ** 100}])
        self.assertEqual(policy.normalize(' Ä / X '), 'ä / x')
        self.assertEqual(engine.compute(rows), {'settings': {'strasse': 'ä / x'}})
        self.assertEqual(rows, before)
        self.assertIsNot(canonical[0], rows[0])
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        duplicates = [{'id': ' A ', 'target': 'X', 'value': 1},
                      {'id': 'a', 'target': 'Y', 'value': 2}]
        self.assertEqual([row['target'] for row in validation.validate(duplicates)], ['x', 'y'])

    def test_invalid_rows_and_error_precedence(self) -> None:
        class Integer(int):
            pass

        invalid_rows = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 0}]
        for key, bad_values in [('id', ['', '  ', 1, None]),
                                ('target', ['', '\t', 1, None]),
                                ('value', [True, Integer(1), 1.0, '1', None, {'nested': []}])]:
            for value in bad_values:
                row = {'id': 'a', 'target': 'b', 'value': 1}
                row[key] = value
                invalid_rows.append(row)
        conflict = [{'id': 'a', 'target': 'x', 'value': 1},
                    {'id': ' A ', 'target': 'y', 'value': 1}]
        apis = [run, render, engine.compute, validation.validate,
                lambda rows: run_many([rows]), lambda rows: render_many([rows])]
        for bad in invalid_rows:
            rows = conflict + [bad]
            before = copy.deepcopy(rows)
            for api in apis:
                with self.subTest(api=api, bad=bad):
                    with self.assertRaisesRegex(ValueError, '^layered-settings: invalid row$'):
                        api(rows)
                    self.assertEqual(rows, before)
        for api in apis:
            with self.assertRaisesRegex(TypeError, '^layered-settings: rows must be a list$'):
                api(())
        for api in apis[:-3] + apis[-2:]:
            with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                api(conflict)

    def test_fresh_results_and_empty_inputs(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['settings']['x'] = 'changed'
        self.assertEqual(results[1], {'settings': {'x': 'a'}})
        self.assertEqual(run(rows), results[1])
        self.assertEqual(rows, before)
        self.assertEqual(run([]), {'settings': {}})
        self.assertEqual(render([]), '{"settings":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        empty = run_many([[], []])
        empty[0]['settings']['changed'] = 'a'
        self.assertEqual(empty[1], {'settings': {}})

    def test_render_and_compute_dispatch(self) -> None:
        rows = [{'id': ' Ä ', 'target': 'Z', 'value': 4}]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True,
                              separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        for api, argument, count in [(run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, []], 2),
                                     (render_many, [rows, []], 2)]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
        # Serialization also honors recursively sorted keys in instrumented results.
        with patch.object(engine, 'compute', return_value={'z': {'é': 1, 'a': 2}, 'a': []}):
            self.assertEqual(render(rows), '{"a":[],"z":{"a":2,"é":1}}\n')

    def test_batch_failure_order_and_atomicity(self) -> None:
        conflict = [{'id': 'a', 'target': 'x', 'value': 1},
                    {'id': 'a', 'target': 'y', 'value': 1}]
        good = [{'id': 'b', 'target': 'z', 'value': 2}]
        for api in [run_many, render_many]:
            for outer in [None, (), {}, 'rows']:
                with self.assertRaisesRegex(TypeError, '^layered-settings: batches must be a list$'):
                    api(outer)
            batches = [good, conflict, [None]]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^layered-settings: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], conflict)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
