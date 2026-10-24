import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class RegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' Z ', 'target': ' Straße/A  B ', 'value': 7},
            {'id': 'z', 'target': 'STRASSE/a  b', 'value': 7},
            {'id': 'B', 'target': 'strasse/A  B', 'value': -7},
            {'id': 'A', 'target': 'strasse/a  b', 'value': -7},
            {'id': 'zero', 'target': '0', 'value': 0},
        ]
        expected = {'decisions': {
            '0': {'rule': 'zero', 'allow': False},
            'strasse/a  b': {'rule': 'a', 'allow': False},
        }}
        self.assertEqual(run(rows), expected)
        self.assertEqual(list(run(rows)['decisions']), ['0', 'strasse/a  b'])
        self.assertEqual(run_many([rows, []]), [expected, {'decisions': {}}])
        self.assertEqual(render_many([rows, []]), render(rows) + render([]))

    def test_normalization_and_validation(self) -> None:
        class Text(str):
            pass

        class Rows(list):
            pass

        class Row(dict):
            pass

        rows = Rows([Row(id=Text(' É/ Straße  X '), target=Text(' Ω/ B '), value=10**200)])
        canonical = validation.validate(rows)
        self.assertEqual(canonical, [{'id': 'é/ strasse  x', 'target': 'ω/ b', 'value': 10**200}])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(policy.normalize(Text(' É/ Straße  X ')), 'é/ strasse  x')
        self.assertEqual(run(rows), engine.compute(rows))
        duplicates = rows + rows
        self.assertEqual(len(validation.validate(duplicates)), 2)
        self.assertEqual(run(duplicates), run(rows))

    def test_invalid_rows_and_containers(self) -> None:
        class Integer(int):
            pass

        invalid = [None, [], {}, {'id': 'a', 'target': 'b', 'value': 1, 'extra': 0}]
        base = {'id': 'a', 'target': 'b', 'value': 1}
        for field, values in [('id', ['', ' \t', 1, None]),
                              ('target', ['', ' \n', False, []]),
                              ('value', [True, Integer(1), 1.0, '1', None])]:
            for value in values:
                invalid.append(dict(base, **{field: value}))
        for row in invalid:
            for api in (run, render, engine.compute, validation.validate):
                with self.subTest(row=row, api=api.__name__):
                    with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                        api([row])
        for value in (None, (), {}, 'rows', iter([])):
            for api in (run, render, engine.compute, validation.validate):
                with self.assertRaisesRegex(TypeError, '^access-policy: rows must be a list$'):
                    api(value)
        for api in (run_many, render_many):
            for value in (None, (), {}, 'batches'):
                with self.assertRaisesRegex(TypeError, '^access-policy: batches must be a list$'):
                    api(value)

    def test_structure_precedes_duplicates(self) -> None:
        rows = [{'id': ' A ', 'target': 'x', 'value': 1},
                {'id': 'a', 'target': 'y', 'value': 1}]
        self.assertEqual(len(validation.validate(rows)), 2)
        for api in (run, render, engine.compute):
            with self.assertRaisesRegex(ValueError, '^access-policy: duplicate id$'):
                api(rows)
            with self.assertRaisesRegex(ValueError, '^access-policy: invalid row$'):
                api(rows + [{'id': 'bad'}])

    def test_strength_and_id_ties(self) -> None:
        rows = [{'id': 'b', 'target': 'x', 'value': 10**200},
                {'id': 'a', 'target': 'x', 'value': 10**200},
                {'id': 'c', 'target': 'x', 'value': -9},
                {'id': 'd', 'target': 'y', 'value': -10**201},
                {'id': 'e', 'target': 'y', 'value': 10**200}]
        self.assertEqual(run(rows), {'decisions': {
            'x': {'rule': 'a', 'allow': True}, 'y': {'rule': 'd', 'allow': False}}})

    def test_render_exactly_matches_run(self) -> None:
        rows = [{'id': ' É ', 'target': ' Ω ', 'value': 1}]
        expected = json.dumps(run(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        self.assertEqual(render(rows), expected)
        self.assertEqual(render(rows), '{"decisions":{"ω":{"allow":true,"rule":"é"}}}\n')
        self.assertEqual(run([]), {'decisions': {}})
        self.assertEqual(render([]), '{"decisions":{}}\n')
        self.assertEqual(run_many([]), [])
        self.assertEqual(render_many([]), '')

    def test_independence_and_no_mutation(self) -> None:
        rows = [{'id': ' A ', 'target': ' X ', 'value': 1}]
        before = copy.deepcopy(rows)
        results = run_many([rows, rows])
        results[0]['decisions']['x']['rule'] = 'changed'
        self.assertEqual(results[1], run(rows))
        results[0]['decisions']['new'] = {}
        self.assertNotIn('new', run(rows)['decisions'])
        canonical = validation.validate(rows)
        canonical[0]['id'] = 'changed'
        self.assertEqual(rows, before)
        invalid = rows + [{'id': 'bad', 'target': {'nested': []}, 'value': 1}]
        snapshot = copy.deepcopy(invalid)
        for api in (run, render, validation.validate, engine.compute):
            with self.assertRaises(ValueError):
                api(invalid)
            self.assertEqual(invalid, snapshot)
        for api in (run_many, render_many):
            with self.assertRaises(ValueError):
                api([rows, invalid])
            self.assertEqual(invalid, snapshot)
            self.assertEqual(rows, before)

    def test_compute_resolved_at_call_time(self) -> None:
        rows = [{'id': 'a', 'target': 'x', 'value': 1}]
        original = engine.compute
        for api, argument, count in ((run, rows, 1), (render, rows, 1),
                                     (run_many, [rows, []], 2),
                                     (render_many, [rows, []], 2)):
            with patch.object(engine, 'compute', wraps=original) as compute:
                api(argument)
                self.assertEqual(compute.call_count, count)
                self.assertIs(compute.call_args_list[0].args[0], rows)

    def test_batches_stop_at_first_failure(self) -> None:
        first = [{'id': 'a', 'target': 'x', 'value': 1},
                 {'id': 'a', 'target': 'x', 'value': 2}]
        later = [{'invalid': []}]
        batches = [[], first, later]
        before = copy.deepcopy(batches)
        for api in (run_many, render_many):
            with patch.object(engine, 'compute', wraps=engine.compute) as compute:
                with self.assertRaisesRegex(ValueError, '^access-policy: duplicate id$'):
                    api(batches)
                self.assertEqual(compute.call_count, 2)
            self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
