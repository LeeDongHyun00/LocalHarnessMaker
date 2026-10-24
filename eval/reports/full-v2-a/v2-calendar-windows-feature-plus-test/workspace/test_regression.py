import copy
import json
import unittest
from unittest.mock import patch

import project
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' A ', 'target': 'old', 'value': -100},
            {'id': 'b', 'target': ' ROOM/ß ', 'value': 22},
            {'id': 'a', 'target': 'room/SS', 'value': 23},
            {'id': 'a', 'target': 'room/ss', 'value': 23},
        ]
        expected = {'rooms': {'room/ss': [[22, 23, 'b'], [23, 24, 'a']]}}
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(project.run_many([rows, []]), [expected, {'rooms': {}}])
        self.assertEqual(project.render_many([rows, []]),
                         project.render(rows) + project.render([]))

    def test_validation_is_canonical_and_does_not_select(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        rows = Rows([Row(id=Text(' Ä / X '), target=Text(' A  B '), value=10**100),
                     Row(id=' ä / x ', target='elsewhere', value=-1)])
        before = copy.deepcopy(rows)
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [
            {'id': 'ä / x', 'target': 'a  b', 'value': 10**100},
            {'id': 'ä / x', 'target': 'elsewhere', 'value': -1},
        ])
        self.assertEqual(policy.normalize(Text(' Ä / X ')), 'ä / x')
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows, before)

    def test_structural_errors_precede_selection_and_domain(self) -> None:
        class Integer(int):
            pass

        invalid_rows = [None, [], {}, {'id': 'a', 'target': 'r', 'value': 1, 'extra': 2},
                        {'id': ' ', 'target': 'r', 'value': 1},
                        {'id': 'a', 'target': '\t', 'value': 1},
                        {'id': 1, 'target': 'r', 'value': 1},
                        {'id': 'a', 'target': 1, 'value': 1},
                        {'id': 'a', 'target': 'r', 'value': True},
                        {'id': 'a', 'target': 'r', 'value': Integer(1)}]
        prefixes = [
            [{'id': 'a', 'target': 'r', 'value': 24}],
            [{'id': 'a', 'target': 'r', 'value': 1},
             {'id': 'a', 'target': 's', 'value': 1}],
        ]
        for invalid in invalid_rows:
            for prefix in prefixes:
                rows = prefix + [invalid]
                before = copy.deepcopy(rows)
                for api in (project.run, project.render, engine.compute, validation.validate):
                    with self.subTest(api=api.__name__, invalid=invalid):
                        with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid row$'):
                            api(rows)
                        self.assertEqual(rows, before)

    def test_priority_ambiguity_and_domain_precedence(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 'r', 'value': 1},
              {'id': ' A ', 'target': 's', 'value': 1},
              {'id': 'a', 'target': 'r', 'value': 2}], 'ambiguous id'),
            ([{'id': 'a', 'target': 'r', 'value': 1},
              {'id': 'b', 'target': ' R ', 'value': 1}], 'overlap'),
            ([{'id': 'a', 'target': 'r', 'value': 1},
              {'id': 'b', 'target': 'r', 'value': 1},
              {'id': 'c', 'target': 's', 'value': 24}], 'invalid hour'),
        ]
        for hour in (-1, 24, 10**100, -(10**100)):
            cases.append(([{'id': 'a', 'target': 'r', 'value': hour}], 'invalid hour'))
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for api in (project.run, project.render, engine.compute):
                with self.subTest(api=api.__name__, message=message):
                    with self.assertRaisesRegex(ValueError, '^calendar-windows: ' + message + '$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_order_unicode_and_exact_rendering(self) -> None:
        rows = [{'id': 'Z', 'target': 'Ω', 'value': 23},
                {'id': 'B', 'target': ' A / B ', 'value': 5},
                {'id': 'A', 'target': 'a / b', 'value': 0}]
        result = project.run(rows)
        self.assertEqual(list(result), ['rooms'])
        self.assertEqual(list(result['rooms']), ['a / b', 'ω'])
        self.assertEqual(result['rooms']['a / b'], [[0, 1, 'a'], [5, 6, 'b']])
        self.assertEqual(project.render(rows),
                         '{"rooms":{"a / b":[[0,1,"a"],[5,6,"b"]],"ω":[[23,24,"z"]]}}\n')
        self.assertEqual(project.render(rows), json.dumps(
            result, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')

    def test_empty_and_outer_type_contract(self) -> None:
        self.assertEqual(project.run([]), {'rooms': {}})
        self.assertEqual(project.render([]), '{"rooms":{}}\n')
        self.assertEqual(project.run_many([]), [])
        self.assertEqual(project.render_many([]), '')
        for invalid in (None, (), {}, '', iter([])):
            for api in (project.run, project.render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: rows must be a list$'):
                    api(invalid)
            for api in (project.run_many, project.render_many):
                with self.assertRaisesRegex(TypeError, '^calendar-windows: batches must be a list$'):
                    api(invalid)

    def test_fresh_nested_results_and_input_preservation(self) -> None:
        rows = [{'id': ' A ', 'target': ' R ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = project.run_many([rows, rows])
        results[0]['rooms']['r'][0][0] = 99
        results[0]['rooms']['r'].append([2, 3, 'b'])
        expected = {'rooms': {'r': [[1, 2, 'a']]}}
        self.assertEqual(results[1], expected)
        self.assertEqual(project.run(rows), expected)
        self.assertEqual(rows, before)
        empty = project.run_many([[], []])
        empty[0]['rooms']['new'] = []
        self.assertEqual(empty[1], {'rooms': {}})

    def test_all_facades_resolve_compute_at_call_time(self) -> None:
        rows = [{'id': ' A ', 'target': ' R ', 'value': 1}]
        empty = []
        for api, argument, calls in (
            (project.run, rows, [rows]),
            (project.render, rows, [rows]),
            (project.run_many, [rows, empty], [rows, empty]),
            (project.render_many, [rows, empty], [rows, empty]),
        ):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                    api(argument)
                    self.assertEqual(compute.call_count, len(calls))
                    for actual, expected in zip(compute.call_args_list, calls):
                        self.assertIs(actual.args[0], expected)

    def test_batches_stop_on_first_failure_without_mutation(self) -> None:
        good = [{'id': 'a', 'target': 'r', 'value': 1}]
        bad = [{'id': 'b', 'target': 'r', 'value': 24}]
        later = [{'id': 'invalid'}]
        for api in (project.run_many, project.render_many):
            batches = [good, bad, later]
            before = copy.deepcopy(batches)
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^calendar-windows: invalid hour$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], good)
                self.assertIs(compute.call_args_list[1].args[0], bad)
            self.assertEqual(batches, before)
            with self.assertRaisesRegex(TypeError, '^calendar-windows: rows must be a list$'):
                api([good, None])


if __name__ == '__main__':
    unittest.main()
