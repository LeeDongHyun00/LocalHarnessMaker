import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Child/ß ', 'target': ' ROOT ', 'value': 10**100},
            {'id': ' Root ', 'target': 'root', 'value': 1},
            {'id': 'child/ss', 'target': 'root', 'value': 10**100},
            {'id': ' a b ', 'target': 'root', 'value': 2},
        ]
        expected = {'migrations': ['root', 'a b', 'child/ss']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'migrations': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))
        with self.assertRaisesRegex(ValueError, '^schema-migration: duplicate id$'):
            run(rows + [{'id': 'ROOT', 'target': 'root', 'value': 2}])

    def test_structural_validation_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        invalid = [None, {}, {'id': 'x', 'target': 'x', 'value': True},
                   {'id': 'x', 'target': 'x', 'value': IntSubclass(1)},
                   {'id': ' ', 'target': 'x', 'value': 1},
                   {'id': 'x', 'target': 1, 'value': 1},
                   {'id': 'x', 'target': 'x', 'value': 1, 'extra': 0}]
        early = [{'id': 'x', 'target': 'missing', 'value': -1},
                 {'id': 'x', 'target': 'x', 'value': 2}]
        for row in invalid:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api):
                    with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                        api(early + [row])
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaisesRegex(TypeError, '^schema-migration: rows must be a list$'):
                api(())

    def test_canonical_validation_without_domain_selection(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' É/ß A '), target=Text(' ROOT '), value=-1)] * 2)
        expected = [{'id': 'é/ss a', 'target': 'root', 'value': -1}] * 2
        result = validation.validate(rows)
        self.assertEqual(result, expected)
        self.assertIsNot(result[0], result[1])
        self.assertIsNot(result[0], rows[0])
        self.assertEqual(policy.normalize(Text(' É/ß A ')), 'é/ss a')

    def test_domain_error_order(self) -> None:
        cases = [
            ([{'id': 'x', 'target': 'missing', 'value': 0}], 'invalid version'),
            ([{'id': 'x', 'target': 'x', 'value': 2},
              {'id': 'y', 'target': 'x', 'value': 1},
              {'id': 'z', 'target': 'missing', 'value': 3}], 'missing predecessor'),
            ([{'id': 'x', 'target': 'x', 'value': 2},
              {'id': 'y', 'target': 'x', 'value': 2}], 'version order'),
        ]
        for rows, message in cases:
            for api in (run, render, engine.compute):
                with self.subTest(message=message, api=api):
                    with self.assertRaisesRegex(ValueError, '^schema-migration: ' + message + '$'):
                        api(rows)

    def test_sorting_and_unicode_render(self) -> None:
        rows = [{'id': name, 'target': name, 'value': version}
                for name, version in [('Ω', 3), ('z', 1), ('a', 1)]]
        self.assertEqual(run(rows), {'migrations': ['a', 'z', 'ω']})
        self.assertEqual(render(rows), '{"migrations":["a","z","ω"]}\n')
        nested = {'z': [{'β': 1, 'a': {'z': 0, 'a': 2}}], 'a': []}
        with patch.object(engine, 'compute', return_value=nested) as compute:
            self.assertEqual(render([]), json.dumps(nested, ensure_ascii=False,
                                                   sort_keys=True, separators=(',', ':')) + '\n')
            compute.assert_called_once_with([])

    def test_fresh_results_and_unchanged_inputs(self) -> None:
        rows = [{'id': ' Root ', 'target': 'ROOT', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['migrations'].append('changed')
        self.assertEqual(results[1], {'migrations': ['root']})
        self.assertEqual(run(rows), {'migrations': ['root']})
        self.assertEqual(rows, before)
        bad = rows + [{'id': 'bad', 'target': 'bad', 'value': {'nested': []}}]
        snapshot = copy.deepcopy(bad)
        for api in (run, render, engine.compute, validation.validate):
            with self.assertRaises(ValueError):
                api(bad)
            self.assertEqual(bad, snapshot)

    def test_batches_and_compute_instrumentation(self) -> None:
        rows = [{'id': 'root', 'target': 'root', 'value': 1}]
        for api, args, count in [(run, rows, 1), (render, rows, 1),
                                 (run_many, [rows, rows], 2),
                                 (render_many, [rows, rows], 2)]:
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(args)
                self.assertEqual(compute.call_count, count)
                self.assertEqual(compute.call_args_list, [((rows,),)] * count)
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        self.assertEqual(run([]), {'migrations': []})
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^schema-migration: batches must be a list$'):
                api(())

    def test_batch_failure_is_ordered_and_atomic(self) -> None:
        good = [{'id': 'root', 'target': 'root', 'value': 1}]
        bad = [{'id': 'bad', 'target': 'missing', 'value': 1}]
        batches = [good, bad, None]
        snapshot = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^schema-migration: missing predecessor$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, snapshot)


if __name__ == '__main__':
    unittest.main()
