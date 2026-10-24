import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key, target, value=1):
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row('a', 'missing', -1), row('z', 'z'), row('a', 'z', 10),
                row('b', 'b', 100), row('c', 'a'), row('a', 'missing', 0),
                row('a', 'z', 10)]
        expected = {'order': ['b', 'z', 'a', 'c']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'order': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_fresh_validation(self) -> None:
        rows = [row(' Straße / X ', ' STRASSE / X ', 10**300),
                row('Straße / X', 'other', -10**300)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [row('strasse / x', 'strasse / x', 10**300),
                                     row('strasse / x', 'other', -10**300)])
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(' Straße / X '), 'strasse / x')
        for api in (run, engine.compute):
            self.assertEqual(api(rows), {'order': ['strasse / x']})
        self.assertEqual(render(rows), '{"order":["strasse / x"]}\n')
        self.assertEqual(run_many([rows]), [{'order': ['strasse / x']}])
        self.assertEqual(render_many([rows]), render(rows))

    def test_subclasses_and_exact_integer_type(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Integer(int):
            pass

        self.assertEqual(run(Rows([Row(id=Text(' A '), target=Text('A'), value=1)])),
                         {'order': ['a']})
        for value in (True, Integer(1), 1.0, '1', None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                    run([row('a', 'a', value)])

    def test_structural_errors_precede_domain_errors(self) -> None:
        invalid = [None, {}, row('', 'a'), row('a', ' '), row(1, 'a'),
                   row('a', None), dict(row('a', 'a'), extra=1)]
        prefixes = [[row('a', 'missing')], [row('a', 'b'), row('a', 'c')],
                    [row('a', 'b'), row('b', 'a')]]
        for prefix in prefixes:
            for bad in invalid:
                rows = prefix + [bad]
                for api in (run, render, engine.compute, validation.validate):
                    with self.subTest(api=api.__name__, rows=rows):
                        with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                            api(rows)

    def test_ambiguity_is_immediate_after_validation(self) -> None:
        rows = [row(' A ', 'a'), row('a', 'b'), row('a', 'a', 2)]
        self.assertEqual(len(validation.validate(rows)), 3)
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^dependency-graph: ambiguous id$'):
                api(rows)
        self.assertEqual(run([row('a', 'a', 5), row('a', 'missing', 1)]),
                         {'order': ['a']})

    def test_missing_dependencies_and_cycles(self) -> None:
        cases = [([row('a', 'b')], 'missing dependency'),
                 ([row('a', 'b'), row('b', 'a')], 'cycle'),
                 ([row('r', 'r'), row('a', 'b'), row('b', 'a')], 'cycle')]
        for rows, error in cases:
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^dependency-graph: ' + error + '$'):
                    api(rows)

    def test_empty_and_outer_types(self) -> None:
        self.assertEqual(run([]), {'order': []})
        self.assertEqual(render([]), '{"order":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        for bad in (None, (), {}, '', iter([])):
            for api in (run_many, render_many):
                with self.assertRaisesRegex(TypeError, '^dependency-graph: batches must be a list$'):
                    api(bad)
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^dependency-graph: rows must be a list$'):
                    api(bad)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(TypeError, '^dependency-graph: rows must be a list$'):
                api([()])

    def test_outputs_and_inputs_are_independent(self) -> None:
        rows = [row('z', 'z'), row('a', 'z')]
        before = copy.deepcopy(rows)
        result = run_many([rows, rows])
        self.assertIsNot(result[0], result[1])
        result[0]['order'].append('changed')
        self.assertEqual(result[1], {'order': ['z', 'a']})
        self.assertEqual(run(rows), result[1])
        self.assertEqual(rows, before)
        self.assertEqual(list(result[1]), ['order'])
        invalid = [row('a', 'missing'), {'id': {'nested': []}, 'target': 'a', 'value': 1}]
        batches = [rows, invalid, rows]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with self.assertRaisesRegex(ValueError, '^dependency-graph: invalid row$'):
                api(batches)
            self.assertEqual(batches, before)

    def test_runtime_engine_dispatch_and_json(self) -> None:
        rows = [row('a', 'a')]
        payload = {'z': [{'β': 1, 'a': 2}], 'a': {'z': 0, 'b': []}}
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':')) + '\n'
        for api, argument, expected, count in (
            (run, rows, payload, 1), (render, rows, serialized, 1),
            (run_many, [rows, rows], [payload, payload], 2),
            (render_many, [rows, rows], serialized * 2, 2),
        ):
            with patch.object(engine, 'compute', return_value=payload) as compute:
                self.assertEqual(api(argument), expected)
                self.assertEqual(compute.call_count, count)
                for call in compute.call_args_list:
                    self.assertIs(call.args[0], rows)

    def test_batches_stop_at_first_failure(self) -> None:
        first = [row('a', 'missing')]
        later = [None]
        original = engine.compute
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=original) as compute:
                with self.assertRaisesRegex(ValueError, '^dependency-graph: missing dependency$'):
                    api([first, later])
                self.assertEqual(compute.call_count, 1)
            good = [row('a', 'a')]
            with patch.object(engine, 'compute', wraps=original) as compute:
                with self.assertRaisesRegex(ValueError, '^dependency-graph: missing dependency$'):
                    api([good, first, later])
                self.assertEqual(compute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
