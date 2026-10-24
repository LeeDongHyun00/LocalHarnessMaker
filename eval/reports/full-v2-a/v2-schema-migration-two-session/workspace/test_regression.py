import copy
import json
import unittest
from unittest.mock import patch

from project import render, render_many, run, run_many
from project import engine, policy, validation


class MigrationRegressionTests(unittest.TestCase):
    def test_domain_edge(self) -> None:
        rows = [
            {'id': ' NEXT_STEP ', 'target': ' ROOT ', 'value': 2},
            {'id': 'Root', 'target': 'root', 'value': 1},
            {'id': 'next-step', 'target': 'root', 'value': 2},
        ]
        self.assertEqual(run(rows), {'migrations': ['root', 'next-step']})
        with self.assertRaisesRegex(ValueError, '^schema-migration: version order$'):
            run([rows[1], dict(rows[0], value=1)])

    def test_normalization_and_validation_order(self) -> None:
        rows = [
            {'id': ' STRAẞE_A / B ', 'target': ' STRAẞE_A / B ', 'value': 3},
            {'id': 'strasse-a / b', 'target': 'strasse-a / b', 'value': 3},
        ]
        expected = {'migrations': ['strasse-a / b']}
        self.assertEqual(policy.normalize(' STRAẞE_A / B '), 'strasse-a / b')
        canonical = validation.validate(rows)
        self.assertEqual(len(canonical), 2)
        self.assertIsNot(canonical[0], canonical[1])
        self.assertIsNot(canonical[0], rows[0])
        self.assertEqual(engine.compute(rows), expected)
        self.assertEqual(run(rows), expected)
        self.assertEqual(render(rows), '{"migrations":["strasse-a / b"]}\n')

    def test_structural_errors_precede_selection_and_domain(self) -> None:
        prefixes = [
            [{'id': 'a', 'target': 'a', 'value': 1},
             {'id': 'a', 'target': 'a', 'value': 2}],
            [{'id': 'a', 'target': 'missing', 'value': 0}],
        ]
        for prefix in prefixes:
            for api in (validation.validate, engine.compute, run, render):
                with self.subTest(api=api.__name__, prefix=prefix):
                    with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                        api(prefix + [{'id': 'bad', 'target': 'bad', 'value': True}])

    def test_structure_and_subclasses(self) -> None:
        class Rows(list):
            pass

        class Row(dict):
            pass

        class Text(str):
            pass

        class Number(int):
            pass

        self.assertEqual(run(Rows([Row(id=Text(' A '), target=Text('A'), value=10**100)])),
                         {'migrations': ['a']})
        for api in (validation.validate, engine.compute, run, render):
            for rows in (None, (), {}, 'a'):
                with self.subTest(api=api.__name__, rows=rows):
                    with self.assertRaisesRegex(TypeError, '^schema-migration: rows must be a list$'):
                        api(rows)
            for row in (None, [], {}, {'id': 'a', 'target': 'a', 'value': 1, 'extra': 0},
                        {'id': ' ', 'target': 'a', 'value': 1},
                        {'id': 'a', 'target': '\t', 'value': 1},
                        {'id': 1, 'target': 'a', 'value': 1},
                        {'id': 'a', 'target': 1, 'value': 1},
                        {'id': 'a', 'target': 'a', 'value': Number(1)},
                        {'id': 'a', 'target': 'a', 'value': 1.0}):
                with self.subTest(api=api.__name__, row=row):
                    with self.assertRaisesRegex(ValueError, '^schema-migration: invalid row$'):
                        api([row])

    def test_error_precedence(self) -> None:
        cases = [
            ([{'id': 'a', 'target': 'a', 'value': 0},
              {'id': 'a', 'target': 'missing', 'value': 1}], 'duplicate id'),
            ([{'id': 'a', 'target': 'missing', 'value': 0}], 'invalid version'),
            ([{'id': 'a', 'target': 'b', 'value': 1},
              {'id': 'b', 'target': 'b', 'value': 2},
              {'id': 'c', 'target': 'missing', 'value': 3}], 'missing predecessor'),
            ([{'id': 'a', 'target': 'b', 'value': 1},
              {'id': 'b', 'target': 'b', 'value': 2}], 'version order'),
        ]
        for rows, error in cases:
            # Validation deliberately performs neither selection nor domain checks.
            self.assertEqual(len(validation.validate(rows)), len(rows))
            for api in (engine.compute, run, render):
                with self.subTest(api=api.__name__, error=error):
                    before = copy.deepcopy(rows)
                    with self.assertRaisesRegex(ValueError, '^schema-migration: ' + error + '$'):
                        api(rows)
                    self.assertEqual(rows, before)

    def test_order_empty_and_independence(self) -> None:
        rows = [{'id': 'z', 'target': 'z', 'value': 2},
                {'id': 'b', 'target': 'b', 'value': 1},
                {'id': 'a', 'target': 'a', 'value': 1}]
        before = copy.deepcopy(rows)
        first = run(rows)
        second = run(rows)
        self.assertEqual(first, {'migrations': ['a', 'b', 'z']})
        self.assertEqual(list(first), ['migrations'])
        first['migrations'].append('changed')
        self.assertEqual(second, {'migrations': ['a', 'b', 'z']})
        self.assertEqual(rows, before)
        self.assertEqual(run(rows), second)
        self.assertEqual(run([]), {'migrations': []})
        self.assertEqual(render([]), '{"migrations":[]}\n')

    def test_dynamic_compute_and_render_contract(self) -> None:
        rows = [{'id': 'é', 'target': 'é', 'value': 1}]
        original = engine.compute
        for api in (run, render):
            with patch.object(engine, 'compute', wraps=original) as observed:
                api(rows)
                observed.assert_called_once_with(rows)
        result = {'z': {'é': 1, 'a': 2}, 'a': [2, 1]}
        with patch.object(engine, 'compute', return_value=result) as observed:
            self.assertEqual(render(rows),
                             json.dumps(result, ensure_ascii=False, sort_keys=True,
                                        separators=(',', ':')) + '\n')
            observed.assert_called_once_with(rows)

    def test_batch_outer_inputs_and_empty(self) -> None:
        class Batches(list):
            pass

        for api, empty in ((run_many, []), (render_many, '')):
            for batches in ([], Batches()):
                with self.subTest(api=api.__name__, batches=batches):
                    with patch.object(engine, 'compute') as observed:
                        self.assertEqual(api(batches), empty)
                        observed.assert_not_called()
            for batches in (None, (), {}, '', iter([]), 1):
                with self.subTest(api=api.__name__, batches=batches):
                    with patch.object(engine, 'compute') as observed:
                        with self.assertRaisesRegex(TypeError, '^schema-migration: batches must be a list$'):
                            api(batches)
                        observed.assert_not_called()
            rows = [{'id': 'a', 'target': 'a', 'value': 1}]
            self.assertEqual(api(Batches([rows])), api([rows]))

    def test_batch_policies_and_encounter_order(self) -> None:
        batches = [
            [{'id': ' NEXT_STEP ', 'target': ' STRAẞE_A / B ', 'value': 3},
             {'id': 'STRAẞE_A / B', 'target': 'strasse_a / b', 'value': 2},
             {'id': 'next-step', 'target': 'strasse-a / b', 'value': 3},
             {'id': 'z', 'target': 'z', 'value': 2},
             {'id': 'a', 'target': 'a', 'value': 2}],
            [],
            [{'id': ' É ', 'target': 'é', 'value': 1}],
        ]
        before = copy.deepcopy(batches)
        self.assertEqual(run_many(batches), [
            {'migrations': ['a', 'strasse-a / b', 'z', 'next-step']},
            {'migrations': []}, {'migrations': ['é']}])
        self.assertEqual(render_many(batches),
                         '{"migrations":["a","strasse-a / b","z","next-step"]}\n'
                         '{"migrations":[]}\n{"migrations":["é"]}\n')
        self.assertEqual(batches, before)

    def test_batch_member_errors_and_precedence(self) -> None:
        cases = [
            ((), TypeError, 'rows must be a list'),
            ([{'id': 'a', 'target': 'a', 'value': 1},
              {'id': 'a', 'target': 'a', 'value': 2}, {}], ValueError, 'invalid row'),
            ([{'id': 'a', 'target': 'missing', 'value': 0},
              {'id': 'a', 'target': 'a', 'value': 1}], ValueError, 'duplicate id'),
            ([{'id': 'a', 'target': 'missing', 'value': 0}], ValueError, 'invalid version'),
            ([{'id': 'a', 'target': 'b', 'value': 1},
              {'id': 'b', 'target': 'b', 'value': 2},
              {'id': 'c', 'target': 'missing', 'value': 3}], ValueError, 'missing predecessor'),
            ([{'id': 'a', 'target': 'b', 'value': 1},
              {'id': 'b', 'target': 'b', 'value': 2}], ValueError, 'version order'),
        ]
        original = engine.compute
        for api in (run_many, render_many):
            for bad, error_type, message in cases:
                for position in (0, 1):
                    with self.subTest(api=api.__name__, message=message, position=position):
                        batches = [[]] * position + [bad, None]
                        before = copy.deepcopy(batches)
                        with patch.object(engine, 'compute', wraps=original) as observed:
                            with self.assertRaisesRegex(error_type, '^schema-migration: ' + message + '$'):
                                api(batches)
                            self.assertEqual(observed.call_count, position + 1)
                            for call, member in zip(observed.call_args_list, batches):
                                self.assertIs(call.args[0], member)
                        self.assertEqual(batches, before)

    def test_batch_dynamic_compute_once_per_member(self) -> None:
        batches = [[], [{'id': 'é', 'target': 'é', 'value': 1}], []]
        results = [{'z': {'é': 1, 'a': 2}, 'a': [2, 1]},
                   {'migrations': ['é']}, {'migrations': []}]
        for api in (run_many, render_many):
            with self.subTest(api=api.__name__):
                with patch.object(engine, 'compute', side_effect=results) as observed:
                    expected = results if api is run_many else ''.join(
                        json.dumps(result, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':')) + '\n' for result in results)
                    self.assertEqual(api(batches), expected)
                    self.assertEqual(observed.call_count, len(batches))
                    for call, member in zip(observed.call_args_list, batches):
                        self.assertIs(call.args[0], member)

    def test_batch_atomic_exception_propagation(self) -> None:
        for api in (run_many, render_many):
            batches = [[], [], []]
            failure = RuntimeError('compute failed')
            with patch.object(engine, 'compute', side_effect=[{'migrations': []}, failure]) as observed:
                with self.assertRaises(RuntimeError) as caught:
                    api(batches)
                self.assertIs(caught.exception, failure)
                self.assertEqual(observed.call_count, 2)
            self.assertEqual(batches, [[], [], []])

    def test_batch_results_are_independent(self) -> None:
        rows = [{'id': 'a', 'target': 'a', 'value': 1}]
        batches = [rows, rows, [], []]
        before = copy.deepcopy(batches)
        first = run_many(batches)
        second = run_many(batches)
        self.assertIsNot(first, second)
        for index, result in enumerate(first):
            self.assertIsNot(result, second[index])
            self.assertIsNot(result['migrations'], second[index]['migrations'])
            for other in first[index + 1:]:
                self.assertIsNot(result, other)
                self.assertIsNot(result['migrations'], other['migrations'])
        first[0]['migrations'].append('changed')
        first[2]['migrations'].append('changed')
        expected = [{'migrations': ['a']}, {'migrations': ['a']},
                    {'migrations': []}, {'migrations': []}]
        self.assertEqual(second, expected)
        self.assertEqual(run_many(batches), expected)
        self.assertEqual(first[1], expected[1])
        self.assertEqual(first[3], expected[3])
        self.assertEqual(batches, before)


if __name__ == '__main__':
    unittest.main()
