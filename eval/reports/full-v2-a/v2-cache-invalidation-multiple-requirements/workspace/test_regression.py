import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


def row(key: str, target: str, value: int) -> dict:
    return {'id': key, 'target': target, 'value': value}


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [row(' Root ', 'absent', -1), row(' Child ', 'ROOT', 8),
                row('leaf', 'child', 3), row('ROOT', ' root ', 0),
                row('safe', 'safe', 10**100)]
        expected = {'dirty': ['child', 'leaf', 'root'], 'clean': ['safe']}
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many([rows, []]), [expected, {'dirty': [], 'clean': []}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_final_target_and_lower_value(self) -> None:
        rows = [row('a', 'b', 9), row('b', 'a', 2), row('A', 'a', 1)]
        self.assertEqual(run(rows), {'dirty': [], 'clean': ['a', 'b']})
        rows.append(row('a', 'a', 0))
        self.assertEqual(run(rows), {'dirty': ['a', 'b'], 'clean': []})

    def test_validation_is_structural_and_fresh(self) -> None:
        rows = [row(' B ', ' Missing ', -2), row('b', 'b', 0)]
        expected = [row('b', 'missing', -2), row('b', 'b', 0)]
        canonical = validation.validate(rows)
        self.assertEqual(canonical, expected)
        self.assertEqual(list(canonical[0]), ['id', 'target', 'value'])
        canonical[0]['target'] = 'changed'
        self.assertEqual(rows[0]['target'], ' Missing ')
        self.assertEqual(validation.validate(rows), expected)

    def test_invalid_rows_and_precedence(self) -> None:
        class IntSubclass(int):
            pass

        invalid = [None, [], {}, row('', 'a', 1), row('a', ' \t', 1),
                   row(1, 'a', 1), row('a', None, 1), row('a', 'a', True),
                   row('a', 'a', IntSubclass(2)), row('a', 'a', 1.0),
                   dict(row('a', 'a', 1), extra=2)]
        for bad in invalid:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(bad=bad, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^cache-invalidation: invalid row$'):
                        api([row('a', 'missing', -1), row('a', 'a', 1), bad])
        for api in (run, render, engine.compute, validation.validate):
            for bad in (None, (), {}, 'rows'):
                with self.assertRaisesRegex(TypeError, '^cache-invalidation: rows must be a list$'):
                    api(bad)

    def test_normalization_and_subclasses(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        name = Text('  Straße / A  B Ω  ')
        canonical = 'strasse / a  b ω'
        rows = Rows([Row(row(name, name, 0))])
        expected = {'dirty': [canonical], 'clean': []}
        self.assertEqual(policy.normalize(name), canonical)
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(run_many(Rows([rows])), [expected])
        encoded = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), encoded)
        self.assertEqual(render_many([rows]), encoded)

    def test_domain_error_precedence(self) -> None:
        cases = [([row('a', 'absent', -1), row('b', 'c', 1), row('c', 'b', 1)],
                  'negative generation'),
                 ([row('a', 'absent', 1), row('b', 'c', 1), row('c', 'b', 1)],
                  'missing dependency'),
                 ([row('b', 'c', 1), row('c', 'b', 0)], 'cycle')]
        for rows, message in cases:
            before = copy.deepcopy(rows)
            for api in (run, render, engine.compute):
                with self.assertRaisesRegex(ValueError, '^cache-invalidation: ' + message + '$'):
                    api(rows)
            self.assertEqual(rows, before)

    def test_batches_atomic_and_sequential(self) -> None:
        batches = [[row('ok', 'ok', 1)], [row('bad', 'bad', -1)], [None]]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^cache-invalidation: negative generation$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
                self.assertIs(compute.call_args_list[0].args[0], batches[0])
                self.assertIs(compute.call_args_list[1].args[0], batches[1])
            self.assertEqual(batches, before)
            for bad in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^cache-invalidation: batches must be a list$'):
                    api(bad)

    def test_shared_engine_invocation_and_rendering(self) -> None:
        rows = [row('a', 'a', 1)]
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, rows], 2),
                                     (render_many, [rows, rows], 2)):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
        result = {'z': {'β': [2, 1], 'a': 0}, 'a': []}
        with patch.object(engine, 'compute', return_value=result):
            self.assertEqual(render(rows), '{"a":[],"z":{"a":0,"β":[2,1]}}\n')

    def test_empty_and_output_independence(self) -> None:
        self.assertEqual(run([]), {'dirty': [], 'clean': []})
        self.assertEqual(list(run([])), ['dirty', 'clean'])
        self.assertEqual(render([]), '{"clean":[],"dirty":[]}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')
        rows = [row('a', 'a', 0)]
        before = copy.deepcopy(rows)
        outputs = run_many([rows, rows])
        outputs[0]['dirty'].append('changed')
        outputs[0]['clean'].append('changed')
        self.assertEqual(outputs[1], {'dirty': ['a'], 'clean': []})
        self.assertEqual(run(rows), outputs[1])
        self.assertEqual(rows, before)

    def test_deep_dependency_chain(self) -> None:
        rows = [row(str(i), str(i + 1), 1) for i in range(2000)]
        rows.append(row('2000', '2000', 0))
        self.assertEqual(run(rows), {'dirty': sorted(str(i) for i in range(2001)), 'clean': []})


if __name__ == '__main__':
    unittest.main()
